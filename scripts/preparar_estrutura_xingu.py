"""Inicializa a estrutura proposta e o plano de cenas, sem importar focos ou renderizar.

Usa apenas a biblioteca padrão. Execute da raiz: python scripts/preparar_estrutura_xingu.py
"""
import argparse
import calendar
import csv
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'entregas/amazonia-xingu'
INPE = 'https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/'


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def validate_config(config):
    video = config['video']
    if config['anos'] != list(range(2018, 2027)) or config['meses'] != [9, 10]:
        raise ValueError('A estrutura requer os nove anos e setembro/outubro.')
    codes = [m['codigo_ibge'] for m in config['territorio']['municipios_xingu']]
    if len(codes) != 10 or len(set(codes)) != 10:
        raise ValueError('O Xingu deve conter dez códigos municipais distintos.')
    position = 0
    for scene in video['cenas']:
        if scene['inicio'] != position or scene['duracao'] <= 0:
            raise ValueError(f"Lacuna ou sobreposição na cena {scene['id']}")
        if scene['id'] == 'historico_duplo':
            expected = len(config['anos']) * scene['segundos_por_ano']
        elif scene['id'].startswith('diario_'):
            month = 9 if scene['id'] == 'diario_setembro' else 10
            expected = calendar.monthrange(config['ano_diario'], month)[1] * scene['segundos_por_dia']
        else:
            expected = scene['duracao']
        if scene['duracao'] != expected:
            raise ValueError(f"Duração incompatível na cena {scene['id']}")
        position += scene['duracao']
    if position != video['duracao_segundos']:
        raise ValueError('Duração total incompatível.')


def expand_timeline(config):
    validate_config(config)
    fps = config['video']['fps']
    rows = []
    for scene in config['video']['cenas']:
        if scene['id'] == 'historico_duplo':
            periods = [(str(y), scene['segundos_por_ano']) for y in config['anos']]
            limits = 'todos_amazonia_legal'
        elif scene['id'].startswith('diario_'):
            month = 9 if scene['id'] == 'diario_setembro' else 10
            year = config['ano_diario']
            periods = [(date(year, month, day).isoformat(), scene['segundos_por_dia'])
                       for day in range(1, calendar.monthrange(year, month)[1] + 1)]
            limits = 'somente_xingu'
        else:
            periods = [('', scene['duracao'])]
            limits = 'transicao_para_xingu' if scene['id'] == 'zoom_xingu' else 'conforme_roteiro'
        start = scene['inicio'] * fps
        for period, seconds in periods:
            end = start + seconds * fps
            rows.append(dict(cena=scene['id'], periodo=period, inicio_frame=start,
                             fim_frame_exclusivo=end, limites=limits))
            start = end
    return rows


def inventory(raw, config):
    expected = [(f'focos_br_ref_{y}.zip', 'anual_referencia', 'anual/Brasil_sat_ref/')
                for y in config['anos'] if y < config['ano_diario']]
    expected += [(f'focos_mensal_br_{config["ano_diario"]}{m:02d}.csv', 'mensal', 'mensal/Brasil/')
                 for m in config['meses']]
    for year in [config['ano_diario']]:
        for month in config['meses']:
            expected += [(p.name, 'diario', 'diario/Brasil/')
                         for p in sorted(raw.glob(f'focos_diario_br_{year}{month:02d}*.csv'))]
    result = []
    for filename, kind, remote in expected:
        path = raw / filename
        exists = path.is_file()
        result.append(dict(arquivo=filename, caminho=str(path.resolve()), tipo=kind,
                           url=INPE + remote + filename, disponivel=exists,
                           bytes=path.stat().st_size if exists else None,
                           sha256=digest(path) if exists else None,
                           estado='inventariado' if exists else 'ausente',
                           obrigatorio=kind != 'diario'))
    return result


def prepare(output, raw):
    config = json.loads((PROJECT / 'projeto.json').read_text(encoding='utf-8'))
    timeline = expand_timeline(config)
    mesh = ROOT / config['territorio']['visualizacao']
    features = json.loads(mesh.read_text(encoding='utf-8'))['features']
    codes = {str(f['properties']['codigo_ibge']) for f in features}
    wanted = {m['codigo_ibge'] for m in config['territorio']['municipios_xingu']}
    if not wanted.issubset(codes):
        raise ValueError(f'Municípios ausentes na malha: {sorted(wanted - codes)}')
    sources = inventory(raw, config)
    output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    db_path = output / 'base_planejada.sqlite'
    with sqlite3.connect(db_path) as db:
        db.executescript((PROJECT / 'base.sql').read_text(encoding='utf-8'))
        serialized = json.dumps(config, ensure_ascii=False, sort_keys=True)
        existing = db.execute('SELECT configuracao_json FROM projeto WHERE id = ?', (config['id'],)).fetchone()
        if existing and existing[0] != serialized:
            raise ValueError('Configuração mudou. Use --saida com outro diretório para preservar a base anterior.')
        db.execute('INSERT OR IGNORE INTO projeto VALUES (?, ?, ?)', (config['id'], config['versao'], serialized))
        for feature in features:
            props = feature['properties']
            code = str(props['codigo_ibge'])
            db.execute('INSERT OR IGNORE INTO municipio VALUES (?, ?, ?, ?, ?, ?)',
                       (code, props['nome'], props['uf'], config['territorio']['malha'],
                        config['territorio']['analise'] + '#' + code,
                        config['territorio']['visualizacao'] + '#' + code))
        region_source = 'https://www.gov.br/mdr/pt-br/assuntos/desenvolvimento-regional/pdrsx/pdrsx'
        for region, name in [('amazonia_legal', 'Amazônia Legal'), ('xingu', config['territorio']['regiao'])]:
            db.execute('INSERT OR IGNORE INTO regiao VALUES (?, ?, ?)',
                       (region, name, region_source if region == 'xingu' else config['territorio']['malha']))
        db.executemany('INSERT OR IGNORE INTO regiao_municipio VALUES (?, ?)',
                       [('amazonia_legal', code) for code in sorted(codes)] + [('xingu', code) for code in sorted(wanted)])
        for source in sources:
            if source['disponivel']:
                db.execute('''INSERT OR IGNORE INTO fonte
                    (caminho, url, sha256, bytes, inventariado_utc, tipo, estado)
                    VALUES (?, ?, ?, ?, ?, ?, 'inventariado')''',
                           (source['caminho'], source['url'], source['sha256'], source['bytes'], timestamp, source['tipo']))
        violations = db.execute('PRAGMA foreign_key_check').fetchall()
        if violations:
            raise ValueError(f'Integridade referencial: {violations}')
    save_json(output / 'inventario.json', dict(gerado_utc=timestamp, importacao_executada=False, fontes=sources))
    save_json(output / 'timeline.json', dict(fps=config['video']['fps'], total_frames=timeline[-1]['fim_frame_exclusivo'], cenas=timeline))
    with (output / 'calendario_esperado.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['data_utc', 'historico_amazonia', 'diario_xingu', 'comparacao_xingu', 'estado_planejado'])
        for year in config['anos']:
            for month in config['meses']:
                for day in range(1, calendar.monthrange(year, month)[1] + 1):
                    d = date(year, month, day)
                    status = 'futuro' if d > date.fromisoformat(config['data_planejamento']) else 'nao_validado'
                    writer.writerow([d.isoformat(), 1, int(year == config['ano_diario']),
                                     int(year in [config['ano_diario'], config['ano_comparacao']]), status])
    report = dict(estado='estrutura_preparada_sem_ingestao_ou_render', municipios=len(codes),
                  municipios_xingu=len(wanted), dias_planejados=549, segmentos_video=len(timeline),
                  frames=timeline[-1]['fim_frame_exclusivo'], fontes_locais=sum(s['disponivel'] for s in sources),
                  faltantes_obrigatorias=[s['arquivo'] for s in sources if s['obrigatorio'] and not s['disponivel']],
                  bloqueios_execucao=['Ingerir e validar fontes e cobertura diária.',
                                     'Fixar corte UTC e gerar snapshot auditado.',
                                     'Implementar exportação dos agregados e assets.',
                                     'Implementar composição Remotion conforme projeto.json e validar quadros.',
                                     'Renderizar e conferir MP4.'])
    save_json(output / 'preflight.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, default=PROJECT / 'preparado')
    parser.add_argument('--raiz-fontes', type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(prepare(args.saida, args.raiz_fontes), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
