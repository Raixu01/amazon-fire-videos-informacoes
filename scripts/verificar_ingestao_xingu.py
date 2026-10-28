"""Confere independentemente a base SQLite e os produtos exportados do Xingu."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

import pandas as pd

if __package__:
    from .coletar_xingu import atomic_json, sha256
else:
    from coletar_xingu import atomic_json, sha256

PROJECT = Path(__file__).resolve().parents[1] / 'entregas/amazonia-xingu'


def verify(receipt_path):
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    folder = Path(receipt['diretorio'])
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    for name, checksum in receipt['arquivos_sha256'].items():
        require(Path(name).name == name, 'Caminho inesperado no recibo.')
        require(sha256(folder / name) == checksum, f'Hash divergente: {name}')
    historical = pd.read_parquet(folder / 'historico_municipal.parquet')
    daily = pd.read_parquet(folder / 'xingu_diario.parquet')
    points = json.loads((folder / 'xingu_pontos.json').read_text(encoding='utf-8'))
    history_json = json.loads((folder / 'historico_video.json').read_text(encoding='utf-8'))
    comparisons = json.loads((folder / 'comparativo.json').read_text(encoding='utf-8'))
    with closing(sqlite3.connect((folder / 'base.sqlite').resolve().as_uri() + '?mode=ro', uri=True)) as db:
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'Integridade SQLite falhou.')
        require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'Integridade referencial falhou.')
        total, unique = db.execute('SELECT COUNT(*),COUNT(DISTINCT chave_deduplicacao) FROM foco').fetchone()
        require(total == unique == receipt['focos_amazonia_legal'], 'Duplicatas ou contagem total divergente.')
        validated_total = db.execute("""SELECT COUNT(*) FROM foco f JOIN cobertura_dia c
            ON c.snapshot_id=f.snapshot_id AND c.data_utc=f.data_utc
            WHERE c.regiao_id='amazonia_legal' AND c.estado IN ('validado','parcial')""").fetchone()[0]
        require(int(historical.focos_observados.sum()) == validated_total, 'Histórico não reconcilia com a base.')
        for state in history_json['mapas']:
            period = f"{state['ano']}-{state['mes']:02d}"
            actual = historical[historical.mes_utc == period].set_index('codigo_ibge').focos_observados
            for code, value in state['municipios'].items():
                require((pd.isna(actual[code]) and value is None) or (not pd.isna(actual[code]) and int(actual[code]) == value),
                        f'Valor municipal divergente: {period}/{code}')
        for day in points['dias']:
            rows = daily[daily.data_utc == day['dia_utc']]
            if day['focos'] is None:
                require(rows.focos.isna().all() and not day['pontos'], f'Dia desconhecido com observações publicadas: {day["dia_utc"]}')
            else:
                require(int(rows.focos.sum()) == day['focos'] == len(day['pontos']), f'Pontos/diário divergentes: {day["dia_utc"]}')
        for comparison in comparisons['periodos']:
            if comparison['estado'] != 'validado':
                continue
            for name, suffix in [('atual', 'atual'), ('anterior', 'anterior')]:
                lo, hi = comparison[f'inicio_{suffix}_utc'][:10], comparison[f'fim_{suffix}_exclusivo_utc'][:10]
                count = db.execute("""SELECT COUNT(*) FROM foco f JOIN regiao_municipio r ON r.codigo_ibge=f.codigo_ibge
                    WHERE r.regiao_id='xingu' AND f.data_utc>=? AND f.data_utc<?""", (lo, hi)).fetchone()[0]
                require(count == comparison[name] == sum(m[name] for m in comparison['municipios']),
                        f'Comparativo divergente: {comparison["periodo"]}/{name}')
        codes = {r[0] for r in db.execute("SELECT codigo_ibge FROM regiao_municipio WHERE regiao_id='xingu'")}
        geometries = json.loads((folder / 'municipios_xingu.geojson').read_text(encoding='utf-8'))
        require({f['properties']['codigo_ibge'] for f in geometries['features']} == codes,
                'Camada visual do Xingu contém municípios incorretos.')
    return dict(snapshot_id=receipt['snapshot_id'], verificado_utc=datetime.now(timezone.utc).isoformat(),
                estado='aprovado_integridade_e_reconciliacao', focos_amazonia_legal=total,
                linhas_historico=len(historical), linhas_diario_xingu=len(daily),
                focos_xingu_2026=int(daily.focos.sum()), corte_exclusivo_utc=receipt['corte_exclusivo_utc'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recibo', type=Path, default=PROJECT / 'ingestao/ultima_ingestao.json')
    args = parser.parse_args()
    try:
        report = verify(args.recibo)
        atomic_json(args.recibo.parent / 'ultima_verificacao.json', report)
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f'Verificação falhou: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
