"""Coleta auditável INPE para Amazônia Legal/Xingu, sem importar ou somar focos.

Arquiva versões por SHA-256, valida CSV/ZIP, revalida HTTP e relata cobertura de
arquivos. Cobertura de arquivos não certifica aquisição dos sensores ou espacialização.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import uuid
import zipfile

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/'
VALIDATOR_VERSION = 1
MAX_BYTES = 1_500_000_000
MAX_UNCOMPRESSED = 2_000_000_000
DAILY_PATTERN = re.compile(r'\bfocos_diario_br_\d{8}\.csv\b')


def sha256(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         suffix='.tmp', delete=False) as stream:
            staged = Path(stream.name)
            json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        staged.replace(path)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


def source_spec(name):
    annual = re.fullmatch(r'focos_br_ref_(\d{4})\.zip', name)
    monthly = re.fullmatch(r'focos_mensal_br_(\d{4})(\d{2})\.csv', name)
    daily = re.fullmatch(r'focos_diario_br_(\d{4})(\d{2})(\d{2})\.csv', name)
    if annual:
        year = int(annual[1])
        start, end = date(year, 1, 1), date(year + 1, 1, 1)
        kind, directory = 'anual_referencia', 'anual/Brasil_sat_ref/'
    elif monthly:
        year, month = map(int, monthly.groups())
        start = date(year, month, 1)
        end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        kind, directory = 'mensal', 'mensal/Brasil/'
    elif daily:
        start = date(*map(int, daily.groups()))
        end = start + timedelta(days=1)
        kind, directory = 'diario', 'diario/Brasil/'
    else:
        raise ValueError(f'Nome de fonte não permitido: {name}')
    return dict(arquivo=name, tipo=kind, url=BASE + directory + name,
                inicio_utc=start.isoformat(), fim_exclusivo_utc=end.isoformat())


@contextmanager
def csv_stream(path, spec):
    if spec['tipo'] != 'anual_referencia':
        with path.open('rb') as stream:
            yield stream
        return
    # Nunca extrair ZIPs: nomes internos não podem escrever no filesystem.
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if m.filename.lower().endswith('.csv')]
        if len(members) != 1 or members[0].file_size > MAX_UNCOMPRESSED:
            raise ValueError('ZIP deve conter um único CSV de tamanho permitido.')
        with archive.open(members[0]) as stream:
            yield stream


def inspect_source(path, spec, sensor):
    """Valida todas as linhas, em lotes, e registra observações sem inferir completude."""
    with csv_stream(path, spec) as stream:
        columns = list(pd.read_csv(stream, nrows=0).columns)
    aliases = {re.sub(r'[^a-z0-9]', '', str(c).lower()): c for c in columns}

    def pick(*names):
        return next((aliases[n] for n in names if n in aliases), None)

    dt_col = pick('datahoragmt', 'datahora', 'datahorautc', 'datapas', 'data')
    lat_col, lon_col = pick('lat', 'latitude'), pick('lon', 'longitude', 'long')
    sat_col = pick('satelite', 'satellite')
    if not all([dt_col, lat_col, lon_col]):
        raise ValueError('CSV sem colunas obrigatórias de data/latitude/longitude.')
    if not sat_col and spec['tipo'] != 'anual_referencia':
        raise ValueError('CSV operacional sem coluna de satélite.')
    selected = list(dict.fromkeys(c for c in [dt_col, lat_col, lon_col, sat_col] if c))
    rows, target_rows = 0, 0
    observed_days, target_days, sensors = Counter(), Counter(), Counter()
    minimum, maximum = None, None
    start = pd.Timestamp(spec['inicio_utc'], tz='UTC')
    end = pd.Timestamp(spec['fim_exclusivo_utc'], tz='UTC')
    with csv_stream(path, spec) as stream, pd.read_csv(
            stream, usecols=selected, chunksize=100_000, dtype=str) as chunks:
        for chunk in chunks:
            timestamps = pd.to_datetime(chunk[dt_col], format='mixed', utc=True, errors='coerce')
            lat = pd.to_numeric(chunk[lat_col], errors='coerce')
            lon = pd.to_numeric(chunk[lon_col], errors='coerce')
            if (timestamps.isna().any() or not lat.between(-90, 90).all()
                    or not lon.between(-180, 180).all()):
                raise ValueError('CSV com data ou coordenada inválida.')
            if not ((timestamps >= start) & (timestamps < end)).all():
                raise ValueError('Observação fora do período declarado no nome do arquivo.')
            rows += len(chunk)
            if len(chunk):
                low, high = timestamps.min(), timestamps.max()
                minimum = low if minimum is None else min(minimum, low)
                maximum = high if maximum is None else max(maximum, high)
            # Guardar apenas setembro/outubro; a validação de linhas cobre o arquivo inteiro.
            in_scope = timestamps.dt.month.isin([9, 10])
            labels = timestamps.dt.strftime('%Y-%m-%d')
            observed_days.update({k: int(v) for k, v in labels[in_scope].value_counts().items()})
            if sat_col:
                satellites = chunk[sat_col].fillna('').str.strip()
                if satellites.eq('').any():
                    raise ValueError('Satélite vazio em uma ou mais observações.')
                sensors.update({k: int(v) for k, v in satellites.value_counts().items()})
                target = satellites.eq(sensor)
                target_rows += int(target.sum())
                target_days.update({k: int(v) for k, v in labels[in_scope & target].value_counts().items()})
    if rows == 0 and spec['tipo'] != 'diario':
        raise ValueError('Arquivo anual/mensal vazio: revisar a fonte antes de aceitá-la.')
    return dict(versao_validador=VALIDATOR_VERSION, sensor_alvo=sensor, linhas=rows,
                linhas_sensor_alvo=target_rows if sat_col else None,
                sensor_evidencia='coluna_satelite' if sat_col else 'serie_referencia_sem_coluna_sensor',
                sensores=dict(sensors), observacao_min_utc=minimum.isoformat() if minimum is not None else None,
                observacao_max_utc=maximum.isoformat() if maximum is not None else None,
                registros_por_dia=dict(observed_days), sensor_alvo_por_dia=dict(target_days) if sat_col else None,
                contagens='linhas_brutas_nacionais_sem_deduplicacao_ou_recorte_municipal',
                cobertura_cientifica_validada=False)


def http_session():
    session = requests.Session()
    session.headers.update({'User-Agent': 'Pulso-Amazonia-Xingu/1', 'Accept-Encoding': 'identity'})
    session.mount('https://', HTTPAdapter(max_retries=Retry(
        total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=['GET'])))
    return session


class Collector:
    def __init__(self, output, raw, sensor, session=None, now=None):
        self.output, self.raw, self.sensor = Path(output), Path(raw), sensor
        self.now = now or datetime.now(timezone.utc)
        self.session = session if session is not None else http_session()
        self.output.mkdir(parents=True, exist_ok=True)
        self.index_path = self.output / 'catalogo.json'
        self.index = json.loads(self.index_path.read_text(encoding='utf-8')) if self.index_path.exists() else {}

    def blob_path(self, record):
        checksum = record['sha256']
        if not re.fullmatch(r'[a-f0-9]{64}', checksum):
            raise ValueError('Hash inválido no catálogo local.')
        source_spec(record['arquivo'])
        return self.output / 'objetos' / checksum / record['arquivo']

    def verified_cache(self, previous):
        path = self.blob_path(previous)
        if not path.is_file() or sha256(path) != previous['sha256']:
            raise ValueError('Cópia arquivada ausente ou corrompida; repetir download sem cache.')
        return path

    def collect_one(self, spec, local=False):
        previous = self.index.get(spec['arquivo'])
        if local:
            path = self.raw / spec['arquivo']
            if not path.is_file():
                if not previous:
                    raise FileNotFoundError(f"Fonte local ausente: {spec['arquivo']}")
                path = self.verified_cache(previous)
            return self._archive(path, spec, previous, online=False, headers={})
        headers = {}
        if previous:
            # Nunca usar 304 para aceitar um cache modificado ou inexistente.
            try:
                self.verified_cache(previous)
            except ValueError:
                pass  # Uma resposta 200 válida recuperará o conteúdo corrompido.
            else:
                if previous.get('etag'):
                    headers['If-None-Match'] = previous['etag']
                if previous.get('last_modified'):
                    headers['If-Modified-Since'] = previous['last_modified']
        staged = None
        try:
            with self.session.get(spec['url'], headers=headers, timeout=(15, 120),
                                  stream=True, allow_redirects=False) as response:
                if response.status_code == 304 and previous:
                    record = self._archive(self.verified_cache(previous), spec, previous,
                                           online=True, headers=response.headers, downloaded=False)
                    return record
                response.raise_for_status()
                if response.status_code != 200:
                    raise ValueError(f'HTTP inesperado: {response.status_code}')
                total = 0
                with tempfile.NamedTemporaryFile(dir=self.output, suffix='.tmp', delete=False) as stream:
                    staged = Path(stream.name)
                    for block in response.iter_content(chunk_size=1024 * 1024):
                        total += len(block)
                        if total > MAX_BYTES:
                            raise ValueError('Arquivo excede o limite de download.')
                        stream.write(block)
                length = response.headers.get('Content-Length')
                if length and not response.headers.get('Content-Encoding') and total != int(length):
                    raise ValueError('Download truncado: Content-Length não confere.')
                return self._archive(staged, spec, previous, online=True, headers=response.headers)
        finally:
            if staged is not None:
                staged.unlink(missing_ok=True)

    def _archive(self, path, spec, previous, online, headers, downloaded=True):
        checksum = sha256(path)
        reusable = (previous and previous['sha256'] == checksum
                    and previous['validacao'].get('versao_validador') == VALIDATOR_VERSION
                    and previous['validacao'].get('sensor_alvo') == self.sensor)
        validation = previous['validacao'] if reusable else inspect_source(path, spec, self.sensor)
        if validation['observacao_max_utc'] and datetime.fromisoformat(validation['observacao_max_utc']) > self.now:
            raise ValueError('Arquivo contém observações no futuro em relação à coleta UTC.')
        timestamp = self.now.isoformat()
        same = previous if reusable else {}
        record = dict(spec, sha256=checksum, bytes=path.stat().st_size,
                      origem='download_INPE' if online else 'arquivo_local',
                      obtido_utc=timestamp if online and downloaded else same.get('obtido_utc'),
                      verificado_utc=timestamp, consulta_online_ok=online,
                      etag=headers.get('ETag', same.get('etag')),
                      last_modified=headers.get('Last-Modified', same.get('last_modified')),
                      validacao=validation)
        destination = self.blob_path(record)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or sha256(destination) != checksum:
            # Cópia atômica; o original local nunca é movido nem alterado.
            staged = None
            try:
                with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.tmp', delete=False) as out:
                    staged = Path(out.name)
                    with path.open('rb') as original:
                        for block in iter(lambda: original.read(1024 * 1024), b''):
                            out.write(block)
                staged.replace(destination)
            finally:
                if staged is not None:
                    staged.unlink(missing_ok=True)
        record['blob'] = destination.relative_to(self.output).as_posix()
        self.index[spec['arquivo']] = record
        atomic_json(self.index_path, self.index)
        return record

    def daily_catalogue(self, year, months, cutoff):
        with self.session.get(BASE + 'diario/Brasil/', timeout=(15, 60), stream=True,
                              allow_redirects=False) as response:
            response.raise_for_status()
            if response.status_code != 200:
                raise ValueError(f'HTTP inesperado no catálogo: {response.status_code}')
            content = bytearray()
            for block in response.iter_content(chunk_size=64 * 1024):
                content.extend(block)
                if len(content) > 5_000_000:
                    raise ValueError('Catálogo excede o tamanho permitido.')
        names = set(DAILY_PATTERN.findall(content.decode('utf-8')))
        if not names:
            raise ValueError('Catálogo diário sem nomes reconhecidos.')
        sources = [source_spec(name) for name in sorted(names)]
        return [s for s in sources if (d := date.fromisoformat(s['inicio_utc'])).year == year
                and d.month in months and d <= cutoff]


def coverage_report(records, years, months, cutoff, now):
    """Não soma fontes sobrepostas e não transforma ausência no mensal em zero."""
    by_name = {r['arquivo']: r for r in records}
    result = []
    for year in years:
        for month in months:
            day = date(year, month, 1)
            while day.month == month:
                label = day.isoformat()
                names = [f'focos_diario_br_{day:%Y%m%d}.csv',
                         f'focos_mensal_br_{day:%Y%m}.csv', f'focos_br_ref_{year}.zip']
                available = [by_name[n] for n in names if n in by_name]
                chosen = available[0] if available else None
                state, count = 'ausente', None
                if day > now.date():
                    state = 'futuro'
                elif day > cutoff:
                    state = 'fora_do_corte'
                elif chosen:
                    state = {'diario': 'arquivo_diario_validado', 'mensal': 'somente_mensal',
                             'anual_referencia': 'arquivo_anual_validado'}[chosen['tipo']]
                    stats = chosen['validacao']
                    counts = stats['sensor_alvo_por_dia']
                    if counts is not None:
                        if chosen['tipo'] == 'diario' or label in stats['registros_por_dia']:
                            count = counts.get(label, 0)
                    if day == now.date():
                        state = 'dia_em_andamento'
                result.append(dict(dia_utc=label, estado=state, registros_sensor_alvo=count,
                                   fonte_preferida=chosen['arquivo'] if chosen else None,
                                   consulta_online_ok=chosen['consulta_online_ok'] if chosen else False,
                                   fontes_disponiveis=[dict(arquivo=r['arquivo'], sha256=r['sha256']) for r in available],
                                   cobertura_cientifica_validada=False))
                day += timedelta(days=1)
    return result


@contextmanager
def collection_lock(output):
    output.mkdir(parents=True, exist_ok=True)
    lock = output / 'coleta.lock'
    with lock.open('x', encoding='utf-8') as stream:
        stream.write(datetime.now(timezone.utc).isoformat())
    try:
        yield
    finally:
        lock.unlink()


def run(config_path, output, reports, raw, cutoff=None, local=False, progress=None, now=None):
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    now = now or datetime.now(timezone.utc)
    cutoff = cutoff or now.date()
    if cutoff > now.date():
        raise ValueError('--ate não pode estar no futuro UTC.')
    records, errors = [], []
    with collection_lock(output), http_session() as session:
        collector = Collector(output, raw, config['serie']['sensor'], session=session, now=now)
        specs = [source_spec(f'focos_br_ref_{y}.zip') for y in config['anos'] if y < config['ano_diario']]
        specs += [source_spec(f'focos_mensal_br_{config["ano_diario"]}{m:02d}.csv')
                  for m in config['meses'] if date(config['ano_diario'], m, 1) <= cutoff]
        try:
            if local:
                names = {p.name for p in raw.glob('focos_diario_br_*.csv')} | set(collector.index)
                dailies = [source_spec(n) for n in sorted(names) if DAILY_PATTERN.fullmatch(n)]
                dailies = [s for s in dailies if (d := date.fromisoformat(s['inicio_utc'])).year == config['ano_diario']
                           and d.month in config['meses'] and d <= cutoff]
            else:
                dailies = collector.daily_catalogue(config['ano_diario'], config['meses'], cutoff)
            specs += dailies
        except (requests.RequestException, ValueError, OSError) as exc:
            errors.append(dict(etapa='catalogo_diario', erro=str(exc)))
        for spec in specs:
            try:
                record = collector.collect_one(spec, local=local)
                records.append(record)
                if progress:
                    progress(f"OK {spec['arquivo']}: {record['validacao']['linhas']} linhas; {record['sha256'][:12]}")
            except (requests.RequestException, ValueError, OSError, zipfile.BadZipFile, EOFError, RuntimeError) as exc:
                errors.append(dict(arquivo=spec['arquivo'], erro=str(exc)))
                if not local:
                    try:
                        record = collector.collect_one(spec, local=True)
                        record = dict(record, consulta_online_ok=False, falha_online=str(exc))
                        records.append(record)
                    except (ValueError, OSError, zipfile.BadZipFile, EOFError, RuntimeError):
                        pass
                if progress:
                    progress(f"FALHA {spec['arquivo']}: {exc}")
        coverage = coverage_report(records, config['anos'], config['meses'], cutoff, now)
        report = dict(versao=1, iniciado_utc=now.isoformat(), terminado_utc=datetime.now(timezone.utc).isoformat(),
                      modo='local' if local else 'online', consulta_online_ok=not local and not errors,
                      estado='incompleta' if errors else ('coleta_local' if local else 'coleta_online_ok'),
                      config_sha256=hashlib.sha256(config_bytes).hexdigest(), ate_utc=cutoff.isoformat(),
                      arquivo_raiz=str(output.resolve()), sensor_alvo=config['serie']['sensor'],
                      cobertura_cientifica_validada=False, importacao_executada=False,
                      resumo=dict(fontes=len(records), falhas=len(errors), dias=len(coverage),
                                  estados_dias=dict(Counter(d['estado'] for d in coverage))),
                      fontes=records, erros=errors, cobertura_dias=coverage)
        identifier = now.strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8]
        atomic_json(reports / 'execucoes' / f'{identifier}.json', report)
        atomic_json(reports / 'ultima_tentativa.json', report)
        if not errors:
            atomic_json(reports / ('ultima_coleta_local.json' if local else 'ultima_coleta_ok.json'), report)
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'entregas/amazonia-xingu/projeto.json')
    parser.add_argument('--saida', type=Path, default=ROOT / 'dados-brutos/amazonia-xingu')
    parser.add_argument('--relatorios', type=Path, default=ROOT / 'entregas/amazonia-xingu/coleta')
    parser.add_argument('--raiz-fontes', type=Path, default=ROOT)
    parser.add_argument('--ate', type=date.fromisoformat, help='Último dia UTC desejado, YYYY-MM-DD.')
    parser.add_argument('--local', action='store_true', help='Arquivar fontes existentes sem consultar o INPE.')
    args = parser.parse_args()
    try:
        report = run(args.config, args.saida, args.relatorios, args.raiz_fontes, args.ate,
                     args.local, progress=lambda message: print(message, flush=True))
    except (ValueError, OSError) as exc:
        print(f'Não foi possível iniciar a coleta: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(dict(estado=report['estado'], **report['resumo']), ensure_ascii=False, indent=2))
    return 1 if report['erros'] else 0


if __name__ == '__main__':
    sys.exit(main())
