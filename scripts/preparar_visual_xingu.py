"""Converte o snapshot validado em geometria SVG e dados offline para o Remotion."""
import argparse
import json
import math
from pathlib import Path

import geopandas as gpd

if __package__:
    from .coletar_xingu import atomic_json, sha256
else:
    from coletar_xingu import atomic_json, sha256

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'entregas/amazonia-xingu'


def project(lon, lat):
    radius = 6378137
    return radius * math.radians(lon), radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def svg_path(geometry, convert):
    polygons = list(geometry.geoms) if geometry.geom_type == 'MultiPolygon' else [geometry]
    rings = [ring for polygon in polygons for ring in [polygon.exterior, *polygon.interiors]]
    commands = []
    for ring in rings:
        points = [convert(x, y) for x, y in ring.coords]
        commands.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in points) + 'Z')
    return ''.join(commands)


def prepare(receipt_path, destination):
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    folder = Path(receipt['diretorio'])
    files = ['historico_video.json', 'xingu_pontos.json', 'comparativo.json',
             'municipios_amazonia.geojson', 'municipios_xingu.geojson']
    for name in files:
        if sha256(folder / name) != receipt['arquivos_sha256'][name]:
            raise ValueError(f'Produto alterado: {name}')
    mesh = gpd.read_file(folder / 'municipios_amazonia.geojson').to_crs(3857)
    minx, miny, maxx, maxy = mesh.total_bounds
    scale = 1000 / (maxx - minx)
    convert = lambda x, y: ((x - minx) * scale, (maxy - y) * scale)
    xingu = json.loads((folder / 'municipios_xingu.geojson').read_text(encoding='utf-8'))
    codes = {f['properties']['codigo_ibge'] for f in xingu['features']}
    municipalities = []
    for row in mesh.itertuples(index=False):
        anchor = row.geometry.representative_point()
        municipalities.append(dict(codigo_ibge=str(row.codigo_ibge), nome=row.nome,
                                   xingu=str(row.codigo_ibge) in codes,
                                   path=svg_path(row.geometry, convert), anchor=list(convert(anchor.x, anchor.y))))
    xbounds = mesh[mesh.codigo_ibge.isin(codes)].total_bounds
    xleft, xtop = convert(xbounds[0], xbounds[3])
    xright, xbottom = convert(xbounds[2], xbounds[1])
    history = json.loads((folder / 'historico_video.json').read_text(encoding='utf-8'))
    points = json.loads((folder / 'xingu_pontos.json').read_text(encoding='utf-8'))
    for day in points['dias']:
        day['pontos'] = [[*convert(*project(lon, lat)), code] for lon, lat, code in day['pontos']]
        counts = {code: 0 if day['focos'] is not None else None for code in sorted(codes)}
        for _, _, code in day['pontos']:
            counts[code] += 1
        if day['focos'] is not None and sum(counts.values()) != day['focos']:
            raise ValueError(f"Pontos/contagem divergentes: {day['dia_utc']}")
        day['municipios'] = counts
    config = json.loads((PROJECT / 'projeto.json').read_text(encoding='utf-8'))
    edition_path = PROJECT / 'edicao.json'
    edition = json.loads(edition_path.read_text(encoding='utf-8')) if edition_path.exists() else {}
    video = dict(config['video'], **edition)
    result = dict(snapshot_id=receipt['snapshot_id'], corte_exclusivo_utc=receipt['corte_exclusivo_utc'],
                  sensor=history['sensor'], fuso='UTC',
                  map_bounds=[0, 0, 1000, (maxy - miny) * scale],
                  xingu_bounds=[xleft, xtop, xright - xleft, xbottom - xtop],
                  municipios=municipalities, historico=history['mapas'],
                  escala=history['limites_superiores_escala_comum'], dias=points['dias'],
                  comparativos=json.loads((folder / 'comparativo.json').read_text(encoding='utf-8'))['periodos'],
                  video=video)
    atomic_json(destination, result)
    summary = dict(snapshot_id=receipt['snapshot_id'], municipios=len(municipalities), municipios_xingu=len(codes),
                   mapas=len(result['historico']), dias=len(result['dias']),
                   arquivo=str(destination.resolve()), sha256=sha256(destination),
                   edicao_sha256=sha256(edition_path) if edition_path.exists() else None)
    report_folder = 'visual-v2' if video.get('versao_edicao', 1) > 1 else 'visual'
    atomic_json(PROJECT / report_folder / 'dados.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recibo', type=Path, default=PROJECT / 'ingestao/ultima_ingestao.json')
    parser.add_argument('--saida', type=Path, default=ROOT / 'remotion/src/xingu-dados.json')
    args = parser.parse_args()
    print(json.dumps(prepare(args.recibo, args.saida), ensure_ascii=False, indent=2))
