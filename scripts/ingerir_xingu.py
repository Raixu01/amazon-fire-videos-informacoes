"""Importa um manifesto INPE imutável e prepara dados auditáveis para o vídeo."""
import argparse
import calendar
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

import geopandas as gpd
import pandas as pd

if __package__:
    from .coletar_xingu import atomic_json, csv_stream, sha256, source_spec
    from .util import find_col
else:
    from coletar_xingu import atomic_json, csv_stream, sha256, source_spec
    from util import find_col

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'entregas/amazonia-xingu'
UTC = timezone.utc
VERSION = 1


def normalize_chunk(raw, filename, sensor, cutoff, evidence=None, months=(9, 10)):
    spec = source_spec(filename)
    dt = find_col(raw.columns, 'data_hora_gmt', 'datahora', 'datahorautc', 'data_pas', 'data')
    lat, lon = find_col(raw.columns, 'lat', 'latitude'), find_col(raw.columns, 'lon', 'longitude', 'long')
    sat = find_col(raw.columns, 'satelite', 'satellite')
    ident = find_col(raw.columns, 'foco_id', 'id', 'id_bdq')
    if not all([dt, lat, lon]):
        raise ValueError(f'Colunas obrigatórias ausentes: {filename}')
    documental = sat is None
    if documental and not (spec['tipo'] == 'anual_referencia' and evidence
                           and evidence['sensor'] == sensor
                           and int(spec['inicio_utc'][:4]) in evidence['anos_permitidos']):
        raise ValueError(f'Sensor ausente e sem evidência documental: {filename}')
    timestamps = pd.to_datetime(raw[dt], format='mixed', utc=True, errors='coerce')
    latitude, longitude = pd.to_numeric(raw[lat], errors='coerce'), pd.to_numeric(raw[lon], errors='coerce')
    if timestamps.isna().any() or not latitude.between(-90, 90).all() or not longitude.between(-180, 180).all():
        raise ValueError(f'Data/coordenada inválida: {filename}')
    if not ((timestamps >= pd.Timestamp(spec['inicio_utc'], tz='UTC'))
            & (timestamps < pd.Timestamp(spec['fim_exclusivo_utc'], tz='UTC'))).all():
        raise ValueError(f'Data fora do período nominal: {filename}')
    satellites = raw[sat].fillna('').str.strip() if sat else pd.Series(sensor, index=raw.index)
    if satellites.eq('').any():
        raise ValueError(f'Satélite vazio: {filename}')
    result = pd.DataFrame(dict(id_original=raw[ident].fillna('') if ident else '',
                               data_hora_utc=timestamps, latitude=latitude, longitude=longitude,
                               satelite=satellites, sensor_documental=documental))
    result = result[(satellites == sensor) & timestamps.dt.month.isin(months) & (timestamps < cutoff)].copy()
    result['data_utc'] = result.data_hora_utc.dt.strftime('%Y-%m-%d')
    # float.hex preserva exatamente o valor lido, sem arredondar coordenadas.
    def key(row):
        y, x = float(row.latitude), float(row.longitude)
        y, x = 0.0 if y == 0 else y, 0.0 if x == 0 else x
        text = '|'.join([row.data_hora_utc.isoformat(), y.hex(), x.hex(), row.satelite])
        return hashlib.sha256(text.encode()).hexdigest()
    result['chave_deduplicacao'] = [key(r) for r in result.itertuples(index=False)]
    return result.reset_index(drop=True)


def spatialize(rows, mesh):
    if mesh.crs is None or not mesh.geometry.is_valid.all() or mesh.codigo_ibge.duplicated().any():
        raise ValueError('Malha sem CRS, com geometrias inválidas ou códigos repetidos.')
    points = gpd.GeoDataFrame(rows.copy().reset_index(drop=True),
                              geometry=gpd.points_from_xy(rows.longitude, rows.latitude), crs=4326)
    joined = gpd.sjoin(points, mesh[['codigo_ibge', 'geometry']].to_crs(4326), how='left', predicate='intersects')
    matched = joined[joined.codigo_ibge.notna()].copy()
    repeated = matched.index[matched.index.duplicated(keep=False)].unique()
    candidates = matched.loc[repeated].groupby(level=0).codigo_ibge.agg(lambda values: sorted(set(values)))
    ambiguous = candidates[candidates.map(len) > 1]
    audit = dict(pontos_entrada=len(rows), fora_territorio=int(joined[joined.codigo_ibge.isna()].index.nunique()),
                 pontos_ambiguos=len(ambiguous), criterio_fronteira='menor_codigo_ibge_sem_buffer',
                 amostra_ambiguidades=[dict(chave_deduplicacao=rows.iloc[int(i)].chave_deduplicacao,
                                            candidatos=codes, escolhido=codes[0]) for i, codes in ambiguous.head(100).items()])
    matched = matched.sort_values('codigo_ibge')
    matched = matched[~matched.index.duplicated(keep='first')].sort_index()
    accepted = pd.DataFrame(matched.drop(columns=['geometry', 'index_right'])).reset_index(drop=True)
    audit['aceitos'] = len(accepted)
    if audit['aceitos'] + audit['fora_territorio'] != len(rows):
        raise ValueError('Falha de reconciliação da espacialização.')
    return accepted, audit


def reconcile_sources(rows, overlap_days=None):
    issues = []
    operational = rows[rows.tipo_fonte.isin(['mensal', 'diario'])]
    groups_by_day = dict(tuple(operational.groupby('data_utc')))
    for day in sorted(set(groups_by_day) | set(overlap_days or [])):
        part = groups_by_day.get(day, operational.iloc[:0])
        groups = {kind: set(group.chave_deduplicacao) for kind, group in part.groupby('tipo_fonte')}
        if (overlap_days is not None and day in overlap_days) or ('mensal' in groups and 'diario' in groups):
            monthly, daily = groups.get('mensal', set()), groups.get('diario', set())
            if monthly != daily:
                issues.append(dict(dia_utc=day, somente_mensal=len(monthly - daily),
                                   somente_diario=len(daily - monthly)))
    return issues


def compare_window(facts, coverage, start, end, previous_year, codes):
    result = dict(inicio_atual_utc=start.isoformat(), fim_atual_exclusivo_utc=end.isoformat(),
                  estado='indisponivel', atual=None, anterior=None, diferenca=None,
                  variacao_pct=None, municipios=[])
    if end <= start:
        return dict(result, motivo='Janela atual ainda não observada.')
    old_start, old_end = start.replace(year=previous_year), end.replace(year=previous_year)
    result.update(inicio_anterior_utc=old_start.isoformat(), fim_anterior_exclusivo_utc=old_end.isoformat())
    days = [d.strftime('%Y-%m-%d') for lo, hi in [(start, end), (old_start, old_end)]
            for d in pd.date_range(lo, hi, inclusive='left', freq='D')]
    invalid = [d for d in days if coverage.get(d) != 'validado']
    if invalid:
        return dict(result, motivo='Janela com cobertura de ingestão não validada.', dias_nao_validados=invalid)

    def counts(lo, hi):
        selected = facts[(facts.data_hora_utc >= lo) & (facts.data_hora_utc < hi)
                         & facts.codigo_ibge.isin(codes)]
        return selected.groupby('codigo_ibge').size().reindex(codes, fill_value=0)

    current, previous = counts(start, end), counts(old_start, old_end)
    def numbers(a, b):
        return dict(atual=int(a), anterior=int(b), diferenca=int(a - b),
                    variacao_pct=round(100 * (int(a) - int(b)) / int(b), 2) if b else None,
                    base_zero=bool(b == 0))
    result.update(numbers(current.sum(), previous.sum()), estado='validado',
                  municipios=[dict(codigo_ibge=code, **numbers(current[code], previous[code])) for code in codes])
    return result


def source_paths(report, root):
    paths = []
    for record in report['fontes']:
        spec = source_spec(record['arquivo'])
        if record['url'] != spec['url'] or not record.get('consulta_online_ok'):
            raise ValueError(f"Fonte sem procedência online confirmada: {record['arquivo']}")
        checksum = record['sha256']
        if len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum):
            raise ValueError('Hash inválido no manifesto de coleta.')
        path = root / 'objetos' / checksum / record['arquivo']
        if not path.is_file() or sha256(path) != checksum:
            raise ValueError(f"Arquivo ausente ou hash divergente: {record['arquivo']}")
        paths.append((record, path))
    if len({r['arquivo'] for r, _ in paths}) != len(paths):
        raise ValueError('Manifesto contém versões concorrentes para um mesmo nome.')
    return paths


def read_sources(paths, sensor, cutoff, evidence, config, progress=None):
    parts, audits = [], []
    for source_id, (record, path) in enumerate(paths, start=1):
        spec = source_spec(record['arquivo'])
        frames, read = [], 0
        with csv_stream(path, spec) as stream, pd.read_csv(stream, dtype=str, chunksize=100_000) as chunks:
            for chunk in chunks:
                read += len(chunk)
                frames.append(normalize_chunk(chunk, record['arquivo'], sensor, cutoff, evidence, config['meses']))
        if read != record['validacao']['linhas']:
            raise ValueError(f"Contagem de linhas difere da coleta: {record['arquivo']}")
        if not frames:
            raise ValueError(f"CSV sem cabeçalho legível: {record['arquivo']}")
        frame = pd.concat(frames, ignore_index=True)
        before = len(frame)
        frame = frame.drop_duplicates('chave_deduplicacao').copy()
        frame['fonte_id'], frame['tipo_fonte'] = source_id, record['tipo']
        parts.append(frame)
        audits.append(dict(arquivo=record['arquivo'], fonte_id=source_id, linhas_lidas=read,
                           linhas_sensor_periodo=before, duplicatas_internas=before - len(frame),
                           linhas_unicas_sensor_periodo=len(frame),
                           sensor_documental=bool(frame.sensor_documental.any())))
        if progress:
            progress(f"LIDO {record['arquivo']}: {len(frame)} focos do sensor/período, antes do recorte espacial")
    rows = pd.concat(parts, ignore_index=True)
    if rows.empty:
        raise ValueError('Nenhuma observação do sensor/período nos arquivos selecionados.')
    return rows, audits


def calendar_coverage(config, report, paths, cutoff, conflicts):
    sources = {r['arquivo']: (i, r) for i, (r, _) in enumerate(paths, start=1)}
    collection_day = datetime.fromisoformat(report['iniciado_utc']).date()
    conflicts = {r['dia_utc'] for r in conflicts}
    result = []
    for year in config['anos']:
        for month in config['meses']:
            current = date(year, month, 1)
            while current.month == month:
                start = datetime.combine(current, datetime.min.time(), tzinfo=UTC)
                end = start + timedelta(days=1)
                names = [f'focos_diario_br_{current:%Y%m%d}.csv', f'focos_mensal_br_{current:%Y%m}.csv',
                         f'focos_br_ref_{year}.zip']
                available = [sources[n] for n in names if n in sources]
                valid = []
                for source_id, record in available:
                    spec = source_spec(record['arquivo'])
                    modified = parsedate_to_datetime(record['last_modified']) if record.get('last_modified') else None
                    product_end = datetime.fromisoformat(spec['fim_exclusivo_utc']).replace(tzinfo=UTC)
                    # Mensal em andamento não certifica dias já decorridos por si só.
                    if modified and modified >= product_end and product_end <= cutoff:
                        valid.append(source_id)
                state, reason, covered = 'nao_validado', 'Sem produto fechado e validado para o dia.', None
                if current > collection_day:
                    state, reason = 'futuro', 'Dia posterior à data da coleta.'
                elif end > cutoff:
                    reason = 'Dia fora do corte de dias fechados deste snapshot.'
                elif current.isoformat() in conflicts:
                    reason = 'Divergência entre as assinaturas AQUA do mensal e do diário; comparação bloqueada.'
                elif valid:
                    state, reason, covered = 'validado', 'Ingestão de produto fechado validada; não certifica aquisição sob nuvens ou todas as passagens.', end.isoformat()
                elif not available:
                    state, reason = 'ausente', 'Nenhum produto disponível para o dia.'
                result.append(dict(data_utc=current.isoformat(), estado=state, fim_coberto_utc=covered,
                                   justificativa=reason, fontes=[i for i, _ in available]))
                current += timedelta(days=1)
    return result


def write_database(path, config, mesh, paths, facts, links, coverage, snapshot_id, cutoff):
    db = sqlite3.connect(path)
    db.executescript((PROJECT / 'base.sql').read_text(encoding='utf-8'))
    with db:
        db.execute('INSERT INTO projeto VALUES (?, ?, ?)', (config['id'], config['versao'], json.dumps(config, ensure_ascii=False)))
        for row in mesh.itertuples(index=False):
            code = str(row.codigo_ibge)
            db.execute('INSERT INTO municipio VALUES (?, ?, ?, ?, ?, ?)',
                       (code, row.nome, row.uf, config['territorio']['malha'],
                        config['territorio']['analise'] + '#' + code, config['territorio']['visualizacao'] + '#' + code))
        for region, name, source in [('amazonia_legal', 'Amazônia Legal', config['territorio']['malha']),
                                      ('xingu', config['territorio']['regiao'], 'projeto.json; recorte confirmado')]:
            db.execute('INSERT INTO regiao VALUES (?, ?, ?)', (region, name, source))
        codes = [str(c) for c in mesh.codigo_ibge]
        xingu = [m['codigo_ibge'] for m in config['territorio']['municipios_xingu']]
        db.executemany('INSERT INTO regiao_municipio VALUES (?, ?)',
                       [('amazonia_legal', c) for c in codes] + [('xingu', c) for c in xingu])
        now = datetime.now(UTC).isoformat()
        db.execute('''INSERT INTO snapshot (id, projeto_id, criado_utc, corte_utc, sensor, fuso, versao_malha, estado)
                      VALUES (?, ?, ?, ?, ?, 'UTC', ?, 'preparando')''',
                   (snapshot_id, config['id'], now, cutoff.isoformat(), config['serie']['sensor'], config['territorio']['malha']))
        for i, (record, blob) in enumerate(paths, start=1):
            db.execute('''INSERT INTO fonte (id,caminho,url,sha256,bytes,inventariado_utc,obtido_utc,
                          last_modified,tipo,sensor_declarado,estado) VALUES (?,?,?,?,?,?,?,?,?,?,'validado')''',
                       (i, str(blob), record['url'], record['sha256'], blob.stat().st_size, now,
                        record.get('obtido_utc'), record.get('last_modified'), record['tipo'], config['serie']['sensor']))
            db.execute('INSERT INTO snapshot_fonte VALUES (?, ?)', (snapshot_id, i))
        db.executemany('INSERT INTO foco VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       ((snapshot_id, r.chave_deduplicacao, r.id_original or None, r.data_hora_utc.isoformat(),
                         r.data_utc, float(r.latitude), float(r.longitude), r.satelite, r.codigo_ibge)
                        for r in facts.itertuples(index=False)))
        db.executemany('INSERT INTO foco_fonte VALUES (?, ?, ?)',
                       ((snapshot_id, r.chave_deduplicacao, int(r.fonte_id)) for r in links.itertuples(index=False)))
        for day in coverage:
            for region in ['amazonia_legal', 'xingu']:
                db.execute('INSERT INTO cobertura_dia VALUES (?, ?, ?, ?, ?, ?)',
                           (snapshot_id, day['data_utc'], region, day['estado'], day['fim_coberto_utc'], day['justificativa']))
                db.executemany('INSERT INTO cobertura_fonte VALUES (?, ?, ?, ?)',
                               [(snapshot_id, day['data_utc'], region, f) for f in day['fontes']])
    if db.execute('PRAGMA foreign_key_check').fetchall():
        db.close()
        raise ValueError('Violação de integridade referencial.')
    return db


def json_records(frame):
    return frame.astype(object).where(frame.notna(), None).to_dict('records')


def export_data(folder, db, config, facts, coverage, cutoff, visual):
    monthly = pd.read_sql_query("SELECT * FROM mensal_municipal WHERE regiao_id='amazonia_legal' ORDER BY mes_utc,codigo_ibge", db)
    daily = pd.read_sql_query("SELECT * FROM diario_municipal WHERE regiao_id='xingu' AND substr(data_utc,1,4)=? ORDER BY data_utc,codigo_ibge",
                              db, params=[str(config['ano_diario'])])
    for frame, column in [(monthly, 'focos_observados'), (daily, 'focos')]:
        frame[column] = frame[column].astype('Int64')
    expected_months = len(visual['features']) * len(config['anos']) * len(config['meses'])
    expected_days = len(config['territorio']['municipios_xingu']) * sum(
        calendar.monthrange(config['ano_diario'], m)[1] for m in config['meses'])
    if len(monthly) != expected_months or len(daily) != expected_days:
        raise ValueError('Granularidade municipal incompleta nos agregados.')
    monthly.to_parquet(folder / 'historico_municipal.parquet', index=False)
    monthly.to_csv(folder / 'historico_municipal.csv', index=False)
    daily.to_parquet(folder / 'xingu_diario.parquet', index=False)
    daily.to_csv(folder / 'xingu_diario.csv', index=False)
    history = []
    for period, group in monthly.groupby('mes_utc', sort=True):
        values = {r['codigo_ibge']: r['focos_observados'] for r in json_records(group)}
        valid_values = [v for v in values.values() if v is not None]
        state = 'validado' if group.estado.eq('validado').all() else ('parcial' if valid_values else 'sem_dados')
        history.append(dict(ano=int(period[:4]), mes=int(period[5:]), estado=state,
                            focos_observados=sum(valid_values) if valid_values else None, municipios=values))
    numbers = monthly.focos_observados.dropna().astype(float)
    thresholds = sorted({0, *(int(v) for v in numbers.quantile([.25, .5, .75, .9, 1]).tolist())}) if len(numbers) else [0]
    atomic_json(folder / 'historico_video.json', dict(sensor=config['serie']['sensor'], fuso='UTC',
                corte_exclusivo_utc=cutoff.isoformat(), limites_superiores_escala_comum=thresholds, mapas=history))
    xingu_codes = [m['codigo_ibge'] for m in config['territorio']['municipios_xingu']]
    xingu = facts[(facts.codigo_ibge.isin(xingu_codes)) & (facts.data_hora_utc.dt.year == config['ano_diario'])]
    by_day = {k: g for k, g in xingu.groupby('data_utc')}
    states = {r['data_utc']: r['estado'] for r in coverage}
    points = []
    for day, group in daily.groupby('data_utc', sort=True):
        part = by_day.get(day, xingu.iloc[:0])
        valid = states[day] == 'validado'
        count = int(group.focos.sum()) if valid else None
        if valid and count != len(part):
            raise ValueError(f'Pontos e agregado diário não reconciliam: {day}')
        points.append(dict(dia_utc=day, estado=states[day], focos=count,
                           pontos=[[float(r.longitude), float(r.latitude), r.codigo_ibge]
                                   for r in part.itertuples(index=False)] if valid else []))
    atomic_json(folder / 'xingu_pontos.json', dict(sensor=config['serie']['sensor'], dias=points))
    comparisons = []
    year = config['ano_diario']
    for label, start, end in [('setembro', datetime(year, 9, 1, tzinfo=UTC), datetime(year, 10, 1, tzinfo=UTC)),
                               ('outubro', datetime(year, 10, 1, tzinfo=UTC), datetime(year, 11, 1, tzinfo=UTC)),
                               ('conjunto', datetime(year, 9, 1, tzinfo=UTC), datetime(year, 11, 1, tzinfo=UTC))]:
        actual_end = min(end, cutoff)
        comparison = compare_window(facts, states, start, actual_end, config['ano_comparacao'], xingu_codes)
        comparisons.append(dict(periodo=label, parcial=actual_end < end, **comparison))
    atomic_json(folder / 'comparativo.json', dict(sensor=config['serie']['sensor'], fuso='UTC',
                                                 unidade='focos de calor detectados', periodos=comparisons))
    atomic_json(folder / 'municipios_amazonia.geojson', visual)
    atomic_json(folder / 'municipios_xingu.geojson', dict(type='FeatureCollection', features=[
        f for f in visual['features'] if str(f['properties']['codigo_ibge']) in xingu_codes]))
    return dict(linhas_historico=len(monthly), linhas_diario_xingu=len(daily),
                focos_xingu_2026=int(len(xingu)), comparativos=comparisons)


def ingest(config_path=PROJECT / 'projeto.json', report_path=PROJECT / 'coleta/ultima_coleta_ok.json',
           output=PROJECT / 'snapshots', receipts=PROJECT / 'ingestao', cutoff=None, archive=None,
           evidence_path=PROJECT / 'referencia_sensor.json', progress=None):
    config_bytes, report_bytes = config_path.read_bytes(), report_path.read_bytes()
    config, report = json.loads(config_bytes), json.loads(report_bytes)
    if not report.get('consulta_online_ok') or report.get('erros'):
        raise ValueError('A ingestão exige manifesto de coleta online concluída sem erros.')
    if report.get('config_sha256') and report['config_sha256'] != hashlib.sha256(config_bytes).hexdigest():
        raise ValueError('A configuração difere da usada na coleta; criar manifesto consistente antes de importar.')
    collected = datetime.fromisoformat(report['iniciado_utc'])
    cutoff = cutoff or collected.replace(hour=0, minute=0, second=0, microsecond=0)
    if cutoff.tzinfo is None or cutoff.utcoffset() != timedelta(0) or cutoff.time() != datetime.min.time():
        raise ValueError('O corte deve ser meia-noite UTC, fim exclusivo dos dias fechados.')
    if cutoff > collected.replace(hour=0, minute=0, second=0, microsecond=0):
        raise ValueError('O corte excede o último dia fechado da coleta.')
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    product = source_spec('focos_br_ref_2018.zip')['url'].rsplit('/', 1)[0] + '/'
    if evidence.get('produto_url') != product or evidence.get('sensor') != config['serie']['sensor']:
        raise ValueError('Evidência documental não corresponde ao produto/sensor configurado.')
    mesh_path = ROOT / config['territorio']['analise']
    visual_path = ROOT / config['territorio']['visualizacao']
    inputs = dict(versao=VERSION, config_sha256=hashlib.sha256(config_bytes).hexdigest(),
                  coleta_sha256=hashlib.sha256(report_bytes).hexdigest(), malha_sha256=sha256(mesh_path),
                  visual_sha256=sha256(visual_path), evidencia_sha256=sha256(evidence_path),
                  codigo_sha256=sha256(Path(__file__)), schema_sha256=sha256(PROJECT / 'base.sql'),
                  corte_exclusivo_utc=cutoff.isoformat())
    snapshot_id = 'xingu-' + hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[:20]
    output, receipts = Path(output), Path(receipts)
    target = output / snapshot_id
    paths = source_paths(report, archive or Path(report['arquivo_raiz']))
    for record, _ in paths:
        source = source_spec(record['arquivo'])
        nominal = date.fromisoformat(source['inicio_utc'])
        if nominal.year not in config['anos'] or (source['tipo'] != 'anual_referencia'
                and (nominal.year != config['ano_diario'] or nominal.month not in config['meses'])):
            raise ValueError(f"Fonte fora do escopo configurado: {source['arquivo']}")
    if target.exists():
        receipt = json.loads((target / 'recibo.json').read_text(encoding='utf-8'))
        for name, checksum in receipt['arquivos_sha256'].items():
            if sha256(target / name) != checksum:
                raise ValueError(f'Snapshot existente alterado: {name}')
        atomic_json(receipts / 'ultima_ingestao.json', receipt)
        return receipt
    mesh = gpd.read_file(mesh_path).to_crs(4326)
    mesh['codigo_ibge'] = mesh.codigo_ibge.astype(str)
    visual = json.loads(visual_path.read_text(encoding='utf-8'))
    mesh_codes = set(mesh.codigo_ibge)
    xingu_codes = {m['codigo_ibge'] for m in config['territorio']['municipios_xingu']}
    if mesh_codes != {str(f['properties']['codigo_ibge']) for f in visual['features']} or not xingu_codes.issubset(mesh_codes):
        raise ValueError('Malhas analítica/visual ou recorte do Xingu não reconciliam.')
    rows, source_audits = read_sources(paths, config['serie']['sensor'], cutoff, evidence, config, progress)
    names = {r['arquivo'] for r, _ in paths}
    overlap = {source_spec(n)['inicio_utc'] for n in names if n.startswith('focos_diario_')
               and f"focos_mensal_br_{date.fromisoformat(source_spec(n)['inicio_utc']):%Y%m}.csv" in names
               and datetime.fromisoformat(source_spec(n)['fim_exclusivo_utc']).replace(tzinfo=UTC) <= cutoff}
    conflicts = reconcile_sources(rows, overlap)
    unique = rows.drop_duplicates('chave_deduplicacao').reset_index(drop=True)
    facts, spatial_audit = spatialize(unique, mesh)
    accepted_keys = set(facts.chave_deduplicacao)
    links = rows.loc[rows.chave_deduplicacao.isin(accepted_keys), ['chave_deduplicacao', 'fonte_id']].drop_duplicates()
    coverage = calendar_coverage(config, report, paths, cutoff, conflicts)
    output.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{snapshot_id}-', suffix='.tmp', dir=output))
    db = write_database(stage / 'base.sqlite', config, mesh, paths, facts, links, coverage, snapshot_id, cutoff)
    try:
        exported = export_data(stage, db, config, facts, coverage, cutoff, visual)
        unlinked = db.execute('''SELECT COUNT(*) FROM foco f WHERE NOT EXISTS
            (SELECT 1 FROM foco_fonte p WHERE p.snapshot_id=f.snapshot_id AND p.chave_deduplicacao=f.chave_deduplicacao)''').fetchone()[0]
        if unlinked or db.execute('SELECT COUNT(*) FROM foco').fetchone()[0] != len(facts):
            raise ValueError('Contagem de focos/linhagem não reconciliou.')
        audit = dict(snapshot_id=snapshot_id, fontes=source_audits, espacial=spatial_audit,
                     linhas_sensor_periodo=sum(r['linhas_sensor_periodo'] for r in source_audits),
                     duplicatas_entre_fontes=len(rows) - len(unique),
                     focos_unicos_nacionais_periodo=len(unique), focos_amazonia_legal=len(facts),
                     vinculos_linhagem=len(links), focos_sem_linhagem=unlinked,
                     divergencias_mensal_diario=conflicts, cobertura_dias=coverage,
                     sensor_evidencia=evidence,
                     validacao='integridade, ingestao dos produtos e consistencia espacial/temporal; nao valida deteccao sob nuvens',
                     **exported)
        atomic_json(stage / 'auditoria.json', audit)
        files = {p.name: sha256(p) for p in sorted(stage.iterdir()) if p.name != 'base.sqlite'}
        manifest = dict(snapshot_id=snapshot_id, entradas=inputs, sensor=config['serie']['sensor'],
                        fuso='UTC', corte_exclusivo_utc=cutoff.isoformat(), arquivos_sha256=files,
                        estado='validado_ingestao', edicao_mensal_completa=all(
                            d['estado'] == 'validado' for d in coverage if d['data_utc'].startswith(str(config['ano_diario']))),
                        comparativos_disponiveis=all(c['estado'] == 'validado' for c in exported['comparativos']))
        atomic_json(stage / 'manifesto.json', manifest)
        with db:
            db.execute("UPDATE snapshot SET estado='validado', manifesto_sha256=? WHERE id=?", (sha256(stage / 'manifesto.json'), snapshot_id))
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('SQLite integrity_check falhou.')
    finally:
        db.close()
    receipt = dict(snapshot_id=snapshot_id, diretorio=str(target.resolve()), base=str((target / 'base.sqlite').resolve()),
                   corte_exclusivo_utc=cutoff.isoformat(), estado='validado_ingestao',
                   focos_amazonia_legal=len(facts), duplicatas_entre_fontes=len(rows) - len(unique),
                   divergencias_mensal_diario=len(conflicts), **exported,
                   arquivos_sha256={p.name: sha256(p) for p in sorted(stage.iterdir())})
    atomic_json(stage / 'recibo.json', receipt)
    stage.rename(target)
    atomic_json(receipts / 'ultima_ingestao.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=PROJECT / 'projeto.json')
    parser.add_argument('--coleta', type=Path, default=PROJECT / 'coleta/ultima_coleta_ok.json')
    parser.add_argument('--saida', type=Path, default=PROJECT / 'snapshots')
    parser.add_argument('--relatorios', type=Path, default=PROJECT / 'ingestao')
    parser.add_argument('--fontes', type=Path, help='Localização alternativa do arquivo de fontes coletadas.')
    parser.add_argument('--corte-utc', type=lambda s: datetime.fromisoformat(s.replace('Z', '+00:00')),
                        help='Fim exclusivo à meia-noite UTC; padrão: início do dia da coleta.')
    args = parser.parse_args()
    try:
        receipt = ingest(args.config, args.coleta, args.saida, args.relatorios, args.corte_utc, args.fontes,
                         progress=lambda s: print(s, flush=True))
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f'Ingestão interrompida; versão publicada preservada: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({k: v for k, v in receipt.items() if k != 'arquivos_sha256'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
