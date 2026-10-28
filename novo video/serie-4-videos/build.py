"""Build the four HyperFrames V2 projects, voice tracks, timed captions, maps, and ledgers."""
from pathlib import Path
import collections
import csv
import hashlib
import html
import json
import math
import random
import re
import shutil
import subprocess
import wave
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Polygon, Point

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DATA = json.loads((REPO / 'remotion/src/xingu-dados.json').read_text(encoding='utf-8'))
SCRIPT = json.loads((ROOT / 'script.json').read_text(encoding='utf-8'))
LEDGER = json.loads((ROOT / 'ledger.json').read_text(encoding='utf-8'))

FFMPEG_CMD = shutil.which('ffmpeg') or 'ffmpeg'
NAMES = {m['codigo_ibge']: m['nome'] for m in DATA['municipios']}
REGION = [m for m in DATA['municipios'] if m['xingu']]
ALTAMIRA_CODE = '1500602'
PEAKS = ['2026-09-13', '2026-09-21', '2026-09-26', '2026-10-09', '2026-10-12', '2026-10-25']

VISUAL_PATHS = {}
MUNI_BBOX = {}
for m in DATA['municipios']:
    rings = []
    all_pts = []
    for ring in re.findall(r'M([^M]+)', m['path']):
        coords = [tuple(map(float, p)) for p in re.findall(r'(-?[\d.]+),(-?[\d.]+)', ring)]
        if len(coords) < 3:
            continue
        all_pts.extend(coords)
        simple = list(LineString(coords).simplify(0.24).coords)
        if len(simple) < 3:
            simple = coords
        rings.append('M' + 'L'.join(f'{a:.2f},{b:.2f}' for a, b in simple) + 'Z')
    VISUAL_PATHS[m['codigo_ibge']] = ''.join(rings)
    if all_pts:
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        MUNI_BBOX[m['codigo_ibge']] = (min(xs), min(ys), max(xs), max(ys), sum(xs) / len(xs), sum(ys) / len(ys))


def esc(s):
    return html.escape(str(s), quote=True)


def number(n):
    return f'{n:,}'.replace(',', '.')


def blur_words(text, cls=''):
    words = str(text).split(' ')
    spans = ' '.join(f'<span class="bw">{esc(w)}</span>' for w in words if w)
    return f'<span class="bw-wrap {cls}">{spans}</span>'


def command(args):
    subprocess.run([str(x) for x in args], check=True, capture_output=True)


def validate_data():
    snapshot = REPO / 'entregas/amazonia-xingu/snapshots' / DATA['snapshot_id']
    totals = collections.Counter()
    altamira_0910 = 0
    with (snapshot / 'xingu_diario.csv').open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['estado'] == 'validado':
                totals[row['data_utc']] += int(row['focos'])
                if row['data_utc'] == '2026-10-09' and row['codigo_ibge'] == ALTAMIRA_CODE:
                    altamira_0910 = int(row['focos'])
    assert sum(totals.values()) == 3688, f'Expected 3688, got {sum(totals.values())}'
    assert altamira_0910 == 104, f'Expected 104 for Altamira on 09/10, got {altamira_0910}'
    for month in ['2026-09', '2026-10']:
        top = sorted((d for d in totals if d.startswith(month)), key=lambda d: (-totals[d], d))[:3]
        assert set(top) == {d for d in PEAKS if d.startswith(month)}
    for d in DATA['dias']:
        if d['estado'] == 'validado':
            assert d['focos'] == totals[d['dia_utc']] == len(d['pontos'])
    assert DATA['comparativos'][-1]['atual'] == 3688
    assert DATA['comparativos'][-1]['anterior'] == 1113
    print('Data: daily counts (3.688 vs 1.113), top 6 days (1.305) and Altamira 09/10 (104) reconciled.', flush=True)


def ensure_aviso_image():
    target = ROOT.parent / 'aviso_queimadas_gov.png'
    W, H = 680, 1446
    img = Image.new('RGB', (W, H), '#181c1e')
    draw = ImageDraw.Draw(img)
    f_bold_lg = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 28)
    f_bold = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 24)
    f_reg = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 23)
    f_sm = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 19)

    # Top status & GovBR header
    draw.rectangle([0, 0, W, 148], fill='#232525')
    draw.text((36, 18), '09:41', fill='#d8e0dc', font=f_sm)
    draw.ellipse([36, 56, 108, 128], fill='#1351b4')
    draw.text((50, 76), 'gov', fill='#ffffff', font=f_bold)
    draw.text((126, 58), 'Gov.br • Avisos Oficiais', fill='#f5f1e8', font=f_bold)
    draw.text((126, 94), 'Canal verificado • Defesa Civil e Saúde', fill='#9bb6aa', font=f_sm)

    # Date pill: 11/10/2026
    draw.rounded_rectangle([190, 168, 490, 212], radius=18, fill='#263538', outline='#4c686b', width=1)
    draw.text((228, 177), '11 de outubro de 2026', fill='#f5f1e8', font=f_sm)

    # Greeting card (recipient name anonymized)
    draw.rounded_rectangle([32, 234, 648, 340], radius=20, fill='#232b2d', outline='#365157', width=1)
    draw.rounded_rectangle([54, 254, 340, 286], radius=6, fill='#323d40')
    draw.text((54, 294), 'Aviso preventivo para a sua localidade cadastrada.', fill='#c0d0c8', font=f_sm)

    # Block 1: Fire alert (highlighted in V1 c1)
    draw.rounded_rectangle([32, 364, 648, 568], radius=22, fill='#26383c', outline='#ffc277', width=3)
    draw.text((58, 386), 'ALERTA DE INCÊNDIOS — 11/10/2026', fill='#ffc277', font=f_sm)
    draw.text((58, 424), 'Sua região está sob alerta', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 462), 'de incêndios.', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 512), 'Condições de estiagem elevam o risco de fogo.', fill='#c0d0c8', font=f_reg)

    # Block 2: Smoke & respiratory health (highlighted in V1 c2)
    draw.rounded_rectangle([32, 594, 648, 868], radius=22, fill='#233337', outline='#4c686b', width=2)
    draw.text((58, 618), 'ATENÇÃO À FUMAÇA E À SAÚDE', fill='#abd5bd', font=f_sm)
    draw.text((58, 656), 'A fumaça pode causar', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 694), 'problemas respiratórios.', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 748), 'Redobre o cuidado com crianças, idosos e', fill='#d8e2dc', font=f_reg)
    draw.text((58, 780), 'pessoas com doenças respiratórias.', fill='#d8e2dc', font=f_reg)
    draw.text((58, 816), 'Hidrate-se e evite exposição à fumaça.', fill='#c0d0c8', font=f_sm)

    # Block 3: Official prevention guidance (highlighted in V4 c6)
    draw.rounded_rectangle([32, 894, 648, 1188], radius=22, fill='#233337', outline='#4c686b', width=2)
    draw.text((58, 918), 'ORIENTAÇÕES OFICIAIS DE PREVENÇÃO', fill='#ffc277', font=f_sm)
    draw.text((58, 956), 'Acompanhe os alertas.', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 994), 'Evite provocar incêndios.', fill='#f5f1e8', font=f_bold_lg)
    draw.text((58, 1048), 'Não utilize fogo para limpeza de áreas ou', fill='#d8e2dc', font=f_reg)
    draw.text((58, 1080), 'queima de lixo. Em emergência, acione 193', fill='#d8e2dc', font=f_reg)
    draw.text((58, 1112), 'ou a Defesa Civil do seu município.', fill='#d8e2dc', font=f_reg)

    # Footer bar
    draw.rounded_rectangle([32, 1220, 648, 1380], radius=18, fill='#1d2628', outline='#365157', width=1)
    draw.text((58, 1246), 'Mensagem automática • Governo Federal / Gov.br', fill='#9bb6aa', font=f_sm)
    draw.text((58, 1280), 'Enviada em 11/10/2026 • Nome da destinatária oculto', fill='#9bb6aa', font=f_sm)
    draw.text((58, 1314), 'Defesa Civil • Ministério da Saúde • IBAMA', fill='#abd5bd', font=f_sm)

    img.save(target, format='PNG', optimize=True)
    return target


def svg_overview(mode='empty'):
    """Generate Amazonia Legal SVG map for V1 and V2.
    mode:
      - 'empty': clean outline of Amazonia Legal
      - 'xingu': Amazonia Legal dimmed (25%), Xingu highlighted (100% + amber stroke)
      - 'sep2026': Sept 2026 fire detection points across Amazonia Legal
      - 'oct2026': Oct 1-26 2026 fire detection points across Amazonia Legal
    """
    x, y, w, h = DATA['map_bounds']
    pad = 0.035 * max(w, h)
    view = f'{x - pad:.2f} {y - pad:.2f} {w + 2 * pad:.2f} {h + 2 * pad:.2f}'
    paths = []
    for m in DATA['municipios']:
        vpath = VISUAL_PATHS[m['codigo_ibge']]
        if mode == 'xingu':
            if m['xingu']:
                paths.append(f'<path d="{vpath}" fill="#2b5a4e" stroke="#ffc277" stroke-width="0.65"/>')
            else:
                paths.append(f'<path d="{vpath}" fill="#1b353b" stroke="#537072" stroke-width="0.16" opacity="0.25"/>')
        else:
            fill = '#1d3940' if mode == 'empty' else '#193238'
            stroke = '#6a8785' if mode == 'empty' else '#4b6768'
            paths.append(f'<path d="{vpath}" fill="{fill}" stroke="{stroke}" stroke-width="0.18"/>')

    if mode in ('sep2026', 'oct2026'):
        target_month = 9 if mode == 'sep2026' else 10
        state = next(s for s in DATA['historico'] if s['ano'] == 2026 and s['mes'] == target_month)
        rng = random.Random(202600 + target_month)
        circles = []
        for code, count in sorted(state['municipios'].items()):
            if count <= 0 or code not in MUNI_BBOX:
                continue
            minx, miny, maxx, maxy, cx, cy = MUNI_BBOX[code]
            # Deterministic visual points proportional to municipal detections (capped for crisp SVG rendering)
            n_dots = min(18, max(1, int(round(math.sqrt(count) * 0.85))))
            for k in range(n_dots):
                if k == 0:
                    px, py = cx, cy
                else:
                    px = cx + rng.uniform(-0.28, 0.28) * (maxx - minx)
                    py = cy + rng.uniform(-0.28, 0.28) * (maxy - miny)
                circles.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="2.1" fill="#ffc277" fill-opacity="0.88"/>')
        paths.extend(circles)

    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="1000" height="800">' + ''.join(paths) + '</svg>'


def svg_region(day=None, highlight_altamira=False):
    """Generate Xingu 10-municipalities SVG map for V3."""
    x, y, w, h = DATA['xingu_bounds']
    pad = 0.04 * max(w, h)
    view = f'{x - pad:.2f} {y - pad:.2f} {w + 2 * pad:.2f} {h + 2 * pad:.2f}'
    paths = []
    for m in REGION:
        code = m['codigo_ibge']
        is_atm = (code == ALTAMIRA_CODE)
        if highlight_altamira:
            if is_atm:
                paths.append(f'<path d="{m["path"]}" fill="#2d594e" stroke="#ffc277" stroke-width="0.85"/>')
            else:
                paths.append(f'<path d="{m["path"]}" fill="#1b353b" stroke="#6a8785" stroke-width="0.28" opacity="0.25"/>')
        else:
            paths.append(f'<path d="{m["path"]}" fill="#234942" stroke="#9bb6aa" stroke-width="0.38"/>')

    if day:
        for px, py, muni_code in day['pontos']:
            if highlight_altamira and str(muni_code) != ALTAMIRA_CODE:
                paths.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="1.15" fill="#ffc277" fill-opacity="0.22"/>')
            else:
                paths.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="1.25" fill="#ffc277" fill-opacity="0.92"/>')

    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="1000" height="800">' + ''.join(paths) + '</svg>'


def daily_bars_svg(mode='build', highlight_date=None):
    """Generate the 56-day bar chart (01/09 to 26/10/2026) with zero baseline for V3."""
    valid_days = [d for d in DATA['dias'] if d['estado'] == 'validado']
    assert len(valid_days) == 56
    W, H = 980, 520
    base_y = 430
    max_h = 310
    max_val = 336
    bar_w = 11.5
    step = 16.2
    start_x = 42

    items = []
    # Reference line (max 336 and 150 guide)
    y_336 = base_y - max_h
    y_149 = base_y - (149 / max_val) * max_h
    items.append(f'<line class="chart-ref" x1="{start_x - 8}" y1="{y_336:.1f}" x2="{W - 20}" y2="{y_336:.1f}" stroke="#365157" stroke-dasharray="4 4" stroke-width="1.5"/>')
    items.append(f'<line class="chart-ref" x1="{start_x - 8}" y1="{y_149:.1f}" x2="{W - 20}" y2="{y_149:.1f}" stroke="#2b454b" stroke-dasharray="4 4" stroke-width="1"/>')

    # Month divider between Sept (index 29) and Oct (index 30)
    div_x = start_x + 30 * step - 3.5
    items.append(f'<line class="chart-ref" x1="{div_x:.1f}" y1="{y_336 - 16:.1f}" x2="{div_x:.1f}" y2="{base_y + 38:.1f}" stroke="#4c686b" stroke-width="1.5"/>')

    peak_annotations = {
        '2026-09-13': ('13/09 · 101', -18),
        '2026-09-21': ('21/09 · 149', -18),
        '2026-09-26': ('26/09 · 108', -18),
        '2026-10-09': ('09/10 · 336', -18),
        '2026-10-12': ('12/10 · 314', -18),
        '2026-10-25': ('25/10 · 297', -18),
    }

    for idx, d in enumerate(valid_days):
        dt = d['dia_utc']
        focos = d['focos']
        bh = max(2.0, (focos / max_val) * max_h)
        bx = start_x + idx * step
        by = base_y - bh
        is_oct = dt.startswith('2026-10')

        fill = '#abd5bd' if not is_oct else '#7eb5a0'
        opacity = '1'
        extra_cls = 'day-bar'

        if mode == 'peak' and highlight_date:
            if dt == highlight_date:
                fill = '#ffc277'
                opacity = '1'
                extra_cls = 'day-bar peak-target'
            else:
                fill = '#5f7d79'
                opacity = '0.25'
        elif mode == 'oct-window':
            if is_oct:
                fill = '#ffc277'
                opacity = '0.88'
            else:
                fill = '#5f7d79'
                opacity = '0.25'
        elif mode == 'top6':
            if dt in ('2026-09-21', '2026-10-09'):
                fill = '#ffc277'
                opacity = '1'
            elif dt in peak_annotations:
                fill = '#ffd89e'
                opacity = '0.95'
                extra_cls = 'day-bar peak-other'
            else:
                fill = '#5f7d79'
                opacity = '0.25'

        items.append(
            f'<rect class="{extra_cls}" data-idx="{idx}" data-date="{dt}" '
            f'x="{bx:.2f}" y="{by:.2f}" width="{bar_w}" height="{bh:.2f}" rx="2" '
            f'fill="{fill}" opacity="{opacity}" style="transform-box:fill-box;transform-origin:center bottom"/>'
        )

        if mode == 'top6' and dt in ('2026-09-13', '2026-09-26', '2026-10-12', '2026-10-25'):
            order_map = {'2026-09-13': 0, '2026-09-26': 1, '2026-10-12': 2, '2026-10-25': 3}
            k_ord = order_map[dt]
            cx = bx + bar_w / 2
            # Staggered vertical leader height so adjacent labels never collide
            stem_top = by - (34 if k_ord % 2 == 0 else 68)
            items.append(
                f'<g class="peak-mark" data-mark-order="{k_ord}">'
                f'<line x1="{cx:.1f}" y1="{by - 3:.1f}" x2="{cx:.1f}" y2="{stem_top:.1f}" stroke="#ffc277" stroke-width="2"/>'
                f'<circle cx="{cx:.1f}" cy="{stem_top:.1f}" r="3.5" fill="#ffc277"/>'
                f'</g>'
            )

    # Zero axis
    items.append(f'<line class="chart-axis" x1="{start_x - 10}" y1="{base_y}" x2="{W - 16}" y2="{base_y}" stroke="#f5f1e8" stroke-width="2.5"/>')
    items.append(f'<text x="{start_x}" y="{base_y + 34}" fill="#c0d0c8" font-size="22" font-family="Pulso, sans-serif" font-weight="700">Setembro (1–30)</text>')
    items.append(f'<text x="{div_x + 14:.1f}" y="{base_y + 34}" fill="#ffc277" font-size="22" font-family="Pulso, sans-serif" font-weight="700">Outubro (1–26 • parcial)</text>')
    items.append(f'<text x="6" y="{base_y + 6}" fill="#c0d0c8" font-size="20" font-family="Pulso, sans-serif">0</text>')
    items.append(f'<text x="0" y="{y_336 + 7:.1f}" fill="#c0d0c8" font-size="19" font-family="Pulso, sans-serif">336</text>')

    return f'<svg class="daily-svg" viewBox="0 0 {W} {H}" width="100%" height="100%">' + ''.join(items) + '</svg>'


CSS = '''
@font-face{font-family:Pulso;src:url('assets/segoeui.ttf')}
@font-face{font-family:Pulso;src:url('assets/segoeuib.ttf');font-weight:700}
*{box-sizing:border-box}
html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#10282d;color:#f5f1e8;font-family:Pulso,system-ui,sans-serif;font-variant-numeric:tabular-nums}
#root{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden}
h1,h2,h3,p{margin:0}
h1{font-size:88px;font-weight:700;line-height:1.06;letter-spacing:-2.5px;color:#f5f1e8}
h2{font-size:74px;font-weight:700;line-height:1.1;letter-spacing:-2px;color:#f5f1e8}
p{font-size:44px;line-height:1.32;color:#f5f1e8}
.muted{color:#c0d0c8}
.accent{color:#ffc277}
.green{color:#abd5bd}
.bluegrey{color:#64828a}
.dim-25{opacity:0.25}
.bw{display:inline-block;will-change:filter,opacity}
.eyebrow{font-size:28px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:#abd5bd;margin-bottom:16px}
.brand{position:absolute;left:96px;top:36px;font-size:42px;font-weight:700;letter-spacing:-1.5px;z-index:30}
.series{position:absolute;left:246px;top:50px;font-size:24px;color:#c0d0c8;letter-spacing:2px;font-weight:700;z-index:30}
.episode-pill{position:absolute;right:96px;top:40px;padding:8px 20px;border:1.5px solid #ffc277;border-radius:8px;font-size:26px;font-weight:700;color:#ffc277;background:#153339;z-index:30}
.rule{position:absolute;left:96px;right:96px;top:112px;height:1px;background:#2f4c52;z-index:30}
.foot{position:absolute;left:96px;right:96px;bottom:22px;display:flex;justify-content:space-between;font-size:23px;color:#c0d0c8;z-index:30}
.progress{position:absolute;bottom:0;left:0;width:1920px;height:5px;background:#ffc277;transform-origin:left center;z-index:35}
.stage{position:absolute;left:96px;right:96px;top:160px;height:690px;overflow:hidden}
.inside{position:relative;width:100%;height:100%}
.two{display:grid;grid-template-columns:1.05fr 0.95fr;gap:64px;align-items:center;height:100%}
.two.map-left{grid-template-columns:0.76fr 1.24fr;gap:48px}
.stack{display:flex;flex-direction:column;justify-content:center;gap:26px;height:100%}
.center-stage{display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:28px;height:100%;max-width:1520px}
.chip{display:inline-flex;align-items:center;gap:12px;align-self:flex-start;padding:10px 22px;border:1.5px solid #7b9991;border-radius:8px;font-size:30px;font-weight:700;color:#f5f1e8;background:#17363d}
.chip.amber{border-color:#ffc277;color:#ffc277;background:#1d3530}
.halo-box{border:2.5px solid #ffc277;border-radius:16px;padding:28px 34px;background:#163339;box-shadow:0 0 0 4px rgba(255,194,119,0.16)}
.hero-num{font-size:164px;font-weight:700;line-height:0.96;letter-spacing:-5px;color:#ffc277;font-variant-numeric:tabular-nums}
.hero-unit{font-size:44px;font-weight:700;color:#f5f1e8}
.support-line{font-size:44px;line-height:1.3;color:#c0d0c8;max-width:860px}
.closing-banner{margin-top:12px;padding:18px 28px;border-left:6px solid #ffc277;background:#16343a;font-size:46px;font-weight:700;color:#f5f1e8}
.carrier-dot{position:absolute;width:28px;height:28px;border-radius:50%;background:#ffc277;box-shadow:0 0 0 8px rgba(255,194,119,0.28);transform:translate(-50%,-50%);pointer-events:none;z-index:25}
/* Phone capture */
.phone-frame{position:relative;width:420px;height:660px;margin:auto;border-radius:26px;border:2px solid #5a7a7c;background:#181c1e;overflow:hidden}
.phone-inner{position:relative;width:420px;height:893px;transform-origin:center 280px}
.phone-inner img{width:420px;height:893px;display:block}
.phone-dim-top,.phone-dim-mid,.phone-dim-bot{position:absolute;left:0;right:0;background:#10282d;opacity:0.75;pointer-events:none}
.phone-highlight{position:absolute;left:16px;right:16px;border:3px solid #ffc277;border-radius:16px;box-shadow:0 0 0 5px rgba(255,194,119,0.22);pointer-events:none}
/* Map container */
.map-card{position:relative;width:100%;height:630px;display:flex;align-items:center;justify-content:center}
.map-card img,.map-card svg{width:100%;height:100%;object-fit:contain}
/* Step illustration stage (V1 c4) */
.illus-stage{position:relative;width:560px;height:520px;margin:auto;border-radius:20px;border:1.5px solid #365157;background:#153137;display:flex;align-items:center;justify-content:center}
.illus-badge{position:absolute;left:24px;top:20px;font-size:24px;font-weight:700;color:#abd5bd;letter-spacing:2px;text-transform:uppercase;padding:6px 14px;border:1px solid #4c686b;border-radius:6px}
.illus-step{position:absolute;inset:70px 40px 40px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px}
/* V4 comparison bars */
.comp-stage{display:grid;grid-template-columns:1.1fr 0.9fr;gap:56px;align-items:center;height:100%}
.bars-box{position:relative;height:540px;display:flex;flex-direction:column;justify-content:center;gap:36px}
.bar-row{display:grid;grid-template-columns:130px 1fr 210px;gap:24px;align-items:center}
.bar-year{font-size:46px;font-weight:700}
.bar-track{height:88px;background:#18373d;border-radius:10px;overflow:hidden;position:relative;border:1px solid #2f4c52}
.bar-fill-2025{height:100%;width:30.18%;background:#64828a;transform-origin:left center;border-radius:8px}
.bar-fill-2026{height:100%;width:100%;background:#ffc277;transform-origin:left center;border-radius:8px}
.bar-val{font-size:56px;font-weight:700;font-variant-numeric:tabular-nums}
/* Captions track */
.caption-host{position:absolute;left:160px;right:160px;top:900px;height:108px;display:flex;justify-content:center;align-items:center;pointer-events:none}
.caption-box{background:#091b20;border:1px solid #2f4c52;padding:12px 28px;border-radius:10px;max-width:1540px;text-align:center}
.caption-box p{font-size:40px;line-height:1.24;color:#f5f1e8;font-weight:700}
'''


def build_v1_scenes():
    scenes = []
    # Scene 1 (0-6s): Frame 0 capture real 11/10/2026, push 100->118% on fire alert block, rest at 25%
    s0_html = f'''
    <div class="two">
      <div class="stack">
        <div class="chip amber">Mensagem Gov.br • 11/10/2026</div>
        <h1>{blur_words("Você também recebeu?")}</h1>
        <p class="support-line">“Sua região está sob alerta de incêndios.”</p>
      </div>
      <div class="phone-frame" id="e1-s0-phone" data-layout-allow-overflow>
        <div class="phone-inner" id="e1-s0-inner">
          <img src="assets/aviso.png" alt="Captura de alerta GovBR de 11/10/2026">
          <div class="phone-dim-top" style="top:0;height:218px"></div>
          <div class="phone-highlight" style="top:222px;height:132px"></div>
          <div class="phone-dim-bot" style="top:358px;bottom:0"></div>
        </div>
      </div>
    </div>'''
    s0_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.08);
    tl.fromTo('#e1-s0-inner', {scale:1, y:0}, {scale:1.18, y:-18, duration:2.4, ease:'power2.inOut'}, 0.25);
    '''
    scenes.append((s0_html, s0_js))

    # Scene 2 (6-16s): Pan vertical curto para a frase sobre fumaça; destaque âmbar estático; T1 exit via ponto âmbar
    s1_html = f'''
    <div class="two" id="e1-s1-wrap">
      <div class="stack">
        <div class="eyebrow">O QUE O AVISO DESTACA</div>
        <h1>{blur_words("A fumaça pode causar problemas respiratórios")}</h1>
        <p class="support-line">O risco pode chegar até a nossa casa.</p>
      </div>
      <div class="phone-frame" style="position:relative" data-layout-allow-overflow>
        <div class="phone-inner" id="e1-s1-inner">
          <img src="assets/aviso.png" alt="Trecho sobre fumaça e problemas respiratórios">
          <div class="phone-dim-top" style="top:0;height:362px"></div>
          <div class="phone-highlight" style="top:364px;height:174px"></div>
          <div class="phone-dim-bot" style="top:542px;bottom:0"></div>
        </div>
        <div class="carrier-dot" id="e1-s1-dot" style="left:50%;top:50%;opacity:0"></div>
      </div>
    </div>'''
    s1_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    tl.fromTo('#e1-s1-inner', {scale:1.18, y:-18}, {scale:1.18, y:-142, duration:0.75, ease:'power2.inOut'}, 0.05);
    tl.fromTo('#e1-s1-dot', {opacity:0, scale:0.4}, {opacity:1, scale:1, duration:0.25, ease:'power2.out'}, 9.15);
    tl.fromTo('#e1-s1-dot', {scale:1}, {scale:24, duration:0.58, ease:'power3.in', immediateRender:false}, 9.4);
    tl.fromTo('#e1-s1-wrap', {scale:1, opacity:1}, {scale:1.45, opacity:0, duration:0.58, ease:'power3.in', immediateRender:false}, 9.4);
    '''
    scenes.append((s1_html, s1_js))

    # Scene 3 (16-28s): T1 revela Amazônia Legal e marca o Xingu; contorno desenha em 0.8s
    s2_html = f'''
    <div class="two" id="e1-s2-wrap">
      <div class="stack">
        <div class="chip">Recorte territorial</div>
        <h1>{blur_words("Amazônia Legal")}</h1>
        <div class="halo-box" id="e1-s2-xingu-tag">
          <div class="eyebrow accent" style="margin-bottom:6px">DETALHE REGIONAL</div>
          <h2 class="accent" style="font-size:64px">Xingu</h2>
          <p class="muted" style="font-size:34px">10 municípios do Pará • Na estiagem, o fogo se espalha mais fácil</p>
        </div>
      </div>
      <div class="map-card" id="e1-s2-map">
        <img id="e1-s2-base" src="assets/overview-empty.svg" alt="Amazônia Legal" style="position:absolute;inset:0">
        <img id="e1-s2-xingu" src="assets/overview-xingu.svg" alt="Região de Integração Xingu" style="position:absolute;inset:0;opacity:0">
        <svg viewBox="0 0 1000 800" style="position:absolute;inset:0;width:100%;height:100%">
          <rect id="e1-s2-frame" x="605" y="218" width="210" height="290" rx="14" fill="none" stroke="#ffc277" stroke-width="5" pathLength="100" stroke-dasharray="100 120" stroke-dashoffset="110"/>
        </svg>
        <div class="carrier-dot" id="e1-s2-dot" style="left:69%;top:46%"></div>
      </div>
    </div>'''
    s2_js = '''
    tl.fromTo('#e1-s2-wrap', {scale:0.65, opacity:0}, {scale:1, opacity:1, duration:0.6, ease:'power3.out'}, 0);
    tl.fromTo('#e1-s2-dot', {scale:14, opacity:1}, {scale:1, opacity:1, duration:0.6, ease:'power3.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.25);
    tl.fromTo('#e1-s2-xingu', {opacity:0}, {opacity:1, duration:0.6, ease:'power2.inOut'}, 2.2);
    tl.fromTo('#e1-s2-base', {opacity:1}, {opacity:0.25, duration:0.6, ease:'power2.inOut'}, 2.2);
    tl.fromTo('#e1-s2-frame', {strokeDashoffset:110}, {strokeDashoffset:0, duration:0.8, ease:'power2.out'}, 2.3);
    tl.fromTo('#e1-s2-xingu-tag', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 2.5);
    '''
    scenes.append((s2_html, s2_js))

    # Scene 4 (28-42s): Três passos, um por vez, mesma posição: folha seca -> fogo -> fumaça sobre casa. Rótulo "Ilustração"
    s3_html = f'''
    <div class="two">
      <div class="stack">
        <div class="chip">Ilustração explicativa</div>
        <h1>{blur_words("Seca · fogo · fumaça")}</h1>
        <p class="support-line" id="e1-s3-sub">Afeta principalmente a respiração de <span class="accent" style="font-weight:700">crianças e idosos</span>.</p>
      </div>
      <div class="illus-stage">
        <div class="illus-badge">Ilustração</div>
        <!-- Passo 1: Folha seca -->
        <div class="illus-step" id="e1-s3-step1">
          <svg width="220" height="220" viewBox="0 0 200 200">
            <path d="M40,160 C40,70 110,30 165,35 C160,95 130,155 40,160 Z" fill="#ffc277" stroke="#f5f1e8" stroke-width="4"/>
            <path d="M40,160 Q100,105 160,38" fill="none" stroke="#10282d" stroke-width="5"/>
          </svg>
          <h2 class="accent" style="font-size:52px">1. Vegetação seca</h2>
        </div>
        <!-- Passo 2: Fogo (mesma posição central) -->
        <div class="illus-step" id="e1-s3-step2" style="opacity:0">
          <svg width="220" height="220" viewBox="0 0 200 200">
            <path d="M100,25 C135,70 160,105 145,148 C135,172 115,182 100,182 C85,182 65,172 55,148 C40,105 65,70 100,25 Z" fill="#ffc277" stroke="#f5f1e8" stroke-width="4"/>
            <path d="M100,82 C118,108 125,130 115,155 C108,168 92,168 85,155 C75,130 82,108 100,82 Z" fill="#10282d"/>
          </svg>
          <h2 class="accent" style="font-size:52px">2. Fogo</h2>
        </div>
        <!-- Passo 3: Fumaça sobre casa (mesma posição central) -->
        <div class="illus-step" id="e1-s3-step3" style="opacity:0">
          <svg width="240" height="220" viewBox="0 0 240 200">
            <path d="M55,62 C75,42 108,42 125,58 C145,42 178,46 190,66 C175,84 142,84 122,72 C98,84 68,80 55,62 Z" fill="#c0d0c8" stroke="#ffc277" stroke-width="3"/>
            <polygon points="120,88 65,130 175,130" fill="#abd5bd" stroke="#f5f1e8" stroke-width="3"/>
            <rect x="80" y="130" width="80" height="52" fill="#234942" stroke="#f5f1e8" stroke-width="3"/>
          </svg>
          <h2 class="accent" style="font-size:52px">3. Fumaça sobre a casa</h2>
        </div>
      </div>
    </div>'''
    s3_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    tl.fromTo('#e1-s3-step1', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 0.2);
    // Quando a voz diz "fogo" (~1.6s), passo 1 recua a 25% num canto e passo 2 assume o centro
    tl.to('#e1-s3-step1', {opacity:0.25, scale:0.38, x:-175, y:-145, duration:0.3, ease:'power2.inOut'}, 1.55);
    tl.fromTo('#e1-s3-step2', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 1.65);
    // Quando a voz diz "fumaça" (~2.5s), passo 2 recua a 25% e passo 3 assume o centro
    tl.to('#e1-s3-step2', {opacity:0.25, scale:0.38, x:175, y:-145, duration:0.3, ease:'power2.inOut'}, 2.5);
    tl.fromTo('#e1-s3-step3', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 2.6);
    tl.fromTo('#e1-s3-sub', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.25, ease:'power2.out'}, 4.2);
    '''
    scenes.append((s3_html, s3_js))

    # Scene 5 (42-52s): Fundo limpo, uma linha: "Acompanhe os avisos oficiais", pausa 0.5s, blur por palavra, parado + T1 exit
    s4_html = f'''
    <div class="center-stage" id="e1-s4-wrap">
      <div class="eyebrow">CUIDADO E PREVENÇÃO</div>
      <h1 style="font-size:98px">{blur_words("Acompanhe os avisos oficiais")}</h1>
      <div class="closing-banner" id="e1-s4-close">O aviso é sobre a fumaça.</div>
      <div class="carrier-dot" id="e1-s4-dot" style="left:69%;top:48%;opacity:0"></div>
    </div>'''
    s4_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.5);
    tl.fromTo('#e1-s4-close', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 1.8);
    tl.fromTo('#e1-s4-dot', {opacity:0, scale:0.5}, {opacity:1, scale:1, duration:0.25, ease:'power2.out'}, 9.15);
    tl.fromTo('#e1-s4-dot', {scale:1}, {scale:24, duration:0.58, ease:'power3.in', immediateRender:false}, 9.4);
    tl.fromTo('#e1-s4-wrap', {scale:1, opacity:1}, {scale:1.4, opacity:0, duration:0.58, ease:'power3.in', immediateRender:false}, 9.4);
    '''
    scenes.append((s4_html, s4_js))

    # Scene 6 (52-60s): Ponto âmbar cresce sobre o mapa; selo "Parte 2"; "E os satélites, o que mostram?" + frase final
    s5_html = f'''
    <div class="two" id="e1-s5-wrap">
      <div class="stack">
        <div class="chip amber">Parte 2 • A época</div>
        <h1>{blur_words("E os satélites, o que mostram?")}</h1>
        <div class="closing-banner">O aviso é sobre a fumaça.</div>
      </div>
      <div class="map-card">
        <img src="assets/overview-xingu.svg" alt="Mapa da Amazônia Legal e Xingu">
        <div class="carrier-dot" id="e1-s5-dot" style="left:69%;top:46%"></div>
      </div>
    </div>'''
    s5_js = '''
    tl.fromTo('#e1-s5-wrap', {scale:0.65, opacity:0}, {scale:1, opacity:1, duration:0.6, ease:'power3.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.25);
    tl.fromTo('#e1-s5-dot', {scale:1}, {scale:18, duration:0.6, ease:'power3.in'}, 7.35);
    '''
    scenes.append((s5_html, s5_js))
    return scenes


def build_v2_scenes():
    scenes = []
    # Scene 1 (0-7s): Mapa da Amazônia Legal vazio; "Por que agora?"
    s0_html = f'''
    <div class="two">
      <div class="stack">
        <div class="eyebrow">ÉPOCA DE MENOS CHUVA</div>
        <h1 style="font-size:100px">{blur_words("Por que agora?")}</h1>
        <p class="support-line">Estamos no período de estiagem na Amazônia Legal.</p>
      </div>
      <div class="map-card">
        <img src="assets/overview-empty.svg" alt="Mapa da Amazônia Legal vazio">
      </div>
    </div>'''
    s0_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    '''
    scenes.append((s0_html, s0_js))

    # Scene 2 (7-18s): Folha verde que seca (1.2s power2.inOut); gota de chuva diminui; seta entra depois
    s1_html = f'''
    <div class="center-stage">
      <div class="eyebrow">CONDIÇÕES PARA O FOGO</div>
      <h1 style="font-size:84px">
        {blur_words("Menos chuva")}
        <span id="e2-s1-arrow" class="accent" style="display:inline-block;margin:0 18px;opacity:0">→</span>
        <span id="e2-s1-part2" style="display:inline-block;opacity:0">vegetação mais seca</span>
      </h1>
      <div style="display:flex;align-items:center;gap:80px;margin-top:24px;padding:36px 56px;border:1.5px solid #365157;border-radius:20px;background:#153137">
        <div style="display:flex;flex-direction:column;align-items:center;gap:14px">
          <svg width="160" height="170" viewBox="0 0 160 170">
            <g id="e2-s1-drop" style="transform-origin:80px 90px">
              <path d="M80,20 C80,20 132,82 132,116 C132,145 108,162 80,162 C52,162 28,145 28,116 C28,82 80,20 80,20 Z" fill="#abd5bd" stroke="#f5f1e8" stroke-width="3"/>
            </g>
          </svg>
          <span class="muted" style="font-size:32px;font-weight:700">Menos chuva</span>
        </div>
        <div id="e2-s1-arrow2" class="accent" style="font-size:88px;font-weight:700;opacity:0">→</div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:14px">
          <svg width="180" height="170" viewBox="0 0 180 170">
            <path id="e2-s1-leaf" d="M35,145 C35,60 100,22 155,28 C148,88 120,140 35,145 Z" fill="#abd5bd" stroke="#f5f1e8" stroke-width="3.5"/>
            <path d="M35,145 Q92,90 150,30" fill="none" stroke="#10282d" stroke-width="4"/>
          </svg>
          <span id="e2-s1-leaf-lbl" class="accent" style="font-size:32px;font-weight:700">Vegetação mais seca</span>
        </div>
      </div>
    </div>'''
    s1_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    tl.fromTo('#e2-s1-drop', {scale:1, opacity:1}, {scale:0.52, opacity:0.25, duration:1.2, ease:'power2.inOut'}, 0.6);
    tl.fromTo('#e2-s1-leaf', {fill:'#abd5bd'}, {fill:'#ffc277', duration:1.2, ease:'power2.inOut'}, 0.6);
    tl.fromTo(['#e2-s1-arrow', '#e2-s1-arrow2'], {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 1.9);
    tl.fromTo('#e2-s1-part2', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 2.15);
    '''
    scenes.append((s1_html, s1_js))

    # Scene 3 (18-32s): Aula do mapa: ponto ampliado com legenda; depois pontos de setembro e outubro (até 26/10) de 2026 via T2
    s2_html = f'''
    <div class="two">
      <div class="stack">
        <div class="chip amber">Setembro e outubro 2026 • UTC</div>
        <h1>{blur_words("1 ponto = 1 foco de calor detectado")}</h1>
        <p class="support-line">Não é um incêndio contado um a um, nem área queimada.</p>
        <div class="halo-box" id="e2-s2-batch-label" style="opacity:0">
          <div class="eyebrow accent" style="margin-bottom:6px" id="e2-s2-month-kicker">LOTES MENSAIS (AQUA_M-T)</div>
          <p style="font-size:36px;font-weight:700">Setembro completo + 1 a 26 de outubro de 2026</p>
        </div>
      </div>
      <div class="map-card">
        <!-- Estado 1: Ponto ampliado didático -->
        <div id="e2-s2-lesson" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;background:#153137;border:2px solid #ffc277;border-radius:20px">
          <div style="width:92px;height:92px;border-radius:50%;background:#ffc277;box-shadow:0 0 0 22px rgba(255,194,119,0.22)"></div>
          <h2 class="accent" style="font-size:52px">1 foco detectado pelo satélite</h2>
          <p class="muted" style="font-size:32px">Passagem do sensor AQUA_M-T</p>
        </div>
        <!-- Estado 2: Lote Setembro 2026 -->
        <div id="e2-s2-sep" style="position:absolute;inset:0;opacity:0">
          <img src="assets/overview-sep2026.svg" alt="Focos em setembro de 2026 na Amazônia Legal">
          <div class="chip amber" style="position:absolute;left:24px;top:20px">Setembro 2026 • Lote mensal</div>
        </div>
        <!-- Estado 3: Lote Outubro 1-26 2026 -->
        <div id="e2-s2-oct" style="position:absolute;inset:0;opacity:0">
          <img src="assets/overview-oct2026.svg" alt="Focos em 1 a 26 de outubro de 2026 na Amazônia Legal">
          <div class="chip amber" style="position:absolute;left:24px;top:20px">Outubro 2026 (1–26/10 • UTC)</div>
        </div>
      </div>
    </div>'''
    s2_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    // T2 swap 1: Legenda do ponto -> Lote de Setembro 2026 (t=4.4s)
    tl.to('#e2-s2-lesson', {opacity:0, filter:'blur(8px)', duration:0.2, ease:'power2.in'}, 4.4);
    tl.fromTo('#e2-s2-sep', {opacity:0, filter:'blur(8px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, ease:'power2.out'}, 4.6);
    tl.fromTo('#e2-s2-batch-label', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 4.6);
    // T2 swap 2: Lote de Setembro -> Lote de Outubro 1-26 2026 (t=8.8s)
    tl.to('#e2-s2-sep', {opacity:0, filter:'blur(8px)', duration:0.2, ease:'power2.in'}, 8.8);
    tl.fromTo('#e2-s2-oct', {opacity:0, filter:'blur(8px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, ease:'power2.out'}, 9.0);
    '''
    scenes.append((s2_html, s2_js))

    # Scene 4 (32-44s): Pacífico mais quente com seta curta para a Amazônia; selo NOAA 08/10/2026
    s3_html = f'''
    <div class="two">
      <div class="stack">
        <div class="chip amber">NOAA, 08/10/2026</div>
        <h1>{blur_words("El Niño em curso")}</h1>
        <p class="support-line">O aquecimento do Pacífico pode reduzir as chuvas e favorecer o fogo na Amazônia.</p>
      </div>
      <div class="map-card" style="background:#153137;border:1.5px solid #365157;border-radius:20px;padding:28px">
        <svg viewBox="0 0 820 540" width="100%" height="100%">
          <!-- Oceano Pacífico à esquerda e norte da América do Sul à direita -->
          <rect x="20" y="40" width="780" height="460" rx="16" fill="#11262b"/>
          <text x="55" y="105" fill="#c0d0c8" font-size="28" font-weight="700" font-family="Pulso, sans-serif">OCEANO PACÍFICO EQUATORIAL</text>
          <!-- Faixa aquecida do Pacífico (colore em 0.8s) -->
          <rect id="e2-s3-band" x="50" y="210" width="320" height="110" rx="55" fill="#2b4c52" stroke="#ffc277" stroke-width="3"/>
          <text x="88" y="275" fill="#10282d" font-size="30" font-weight="700" font-family="Pulso, sans-serif">Mais quente</text>
          <!-- Seta curta para a Amazônia (entra depois) -->
          <g id="e2-s3-arrow" style="opacity:0">
            <line x1="390" y1="265" x2="485" y2="265" stroke="#ffc277" stroke-width="8" stroke-linecap="round"/>
            <polygon points="505,265 475,245 475,285" fill="#ffc277"/>
          </g>
          <!-- Região Amazônica -->
          <g transform="translate(520, 145)">
            <rect x="0" y="0" width="245" height="240" rx="22" fill="#1e423b" stroke="#abd5bd" stroke-width="3"/>
            <text x="34" y="105" fill="#f5f1e8" font-size="32" font-weight="700" font-family="Pulso, sans-serif">Amazônia</text>
            <text x="34" y="150" fill="#ffc277" font-size="27" font-weight="700" font-family="Pulso, sans-serif">Menos chuva</text>
          </g>
        </svg>
      </div>
    </div>'''
    s3_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    tl.fromTo('#e2-s3-band', {fill:'#2b4c52'}, {fill:'#ffc277', duration:0.8, ease:'power2.inOut'}, 0.4);
    tl.fromTo('#e2-s3-arrow', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.22, ease:'power2.out'}, 1.5);
    '''
    scenes.append((s3_html, s3_js))

    # Scene 5 (44-53s): Fundo limpo, duas linhas: "O clima aumenta o risco." / "Não explica tudo."
    s4_html = f'''
    <div class="center-stage" id="e2-s4-wrap">
      <div class="eyebrow">CLIMA E CAUSA</div>
      <h1 id="e2-s4-l1" style="font-size:96px">{blur_words("O clima aumenta o risco.")}</h1>
      <h1 id="e2-s4-l2" class="accent" style="font-size:96px;opacity:0">Não explica tudo.</h1>
      <p class="support-line" id="e2-s4-sub" style="opacity:0">A origem do fogo também importa.</p>
      <div class="carrier-dot" id="e2-s4-dot" style="left:69%;top:46%;opacity:0"></div>
    </div>'''
    s4_js = '''
    tl.fromTo(el.querySelectorAll('#e2-s4-l1 .bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.5);
    tl.fromTo('#e2-s4-l2', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 2.4);
    tl.fromTo('#e2-s4-sub', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 3.4);
    tl.fromTo('#e2-s4-dot', {opacity:0, scale:0.5}, {opacity:1, scale:1, duration:0.25, ease:'power2.out'}, 8.15);
    tl.fromTo('#e2-s4-dot', {scale:1}, {scale:24, duration:0.58, ease:'power3.in', immediateRender:false}, 8.4);
    tl.fromTo('#e2-s4-wrap', {scale:1, opacity:1}, {scale:1.4, opacity:0, duration:0.58, ease:'power3.in', immediateRender:false}, 8.4);
    '''
    scenes.append((s4_html, s4_js))

    # Scene 6 (53-60s): T1 do mapa ao recorte do Xingu; selo "Parte 3"; "E no Xingu?"
    s5_html = f'''
    <div class="two" id="e2-s5-wrap">
      <div class="stack">
        <div class="chip amber">Parte 3 • Os picos</div>
        <h1 style="font-size:98px">{blur_words("E no Xingu?")}</h1>
        <div class="closing-banner">O clima aumenta o risco. Não explica tudo.</div>
      </div>
      <div class="map-card" id="e2-s5-map">
        <img src="assets/overview-xingu.svg" alt="Recorte do Xingu na Amazônia Legal">
        <div class="carrier-dot" id="e2-s5-dot" style="left:69%;top:46%"></div>
      </div>
    </div>'''
    s5_js = '''
    tl.fromTo('#e2-s5-wrap', {scale:0.65, opacity:0}, {scale:1, opacity:1, duration:0.6, ease:'power3.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.2);
    tl.fromTo('#e2-s5-map', {scale:1, x:0, y:0}, {scale:2.4, x:-240, y:40, duration:0.65, ease:'power3.in'}, 6.3);
    tl.fromTo('#e2-s5-dot', {scale:1}, {scale:16, duration:0.65, ease:'power3.in'}, 6.3);
    '''
    scenes.append((s5_html, s5_js))
    return scenes


def build_v3_scenes():
    scenes = []
    # Scene 1 (0-7s): Dez municípios do Xingu, tamanhos relativos preservados; continua T1 do V2
    s0_html = f'''
    <div class="two" id="e3-s0-wrap">
      <div class="stack">
        <div class="chip amber">Detalhe regional • Pará</div>
        <h1>{blur_words("Região de Integração Xingu — 10 municípios")}</h1>
        <p class="support-line">O fogo não aparece igual todos os dias.</p>
      </div>
      <div class="map-card">
        <img src="assets/region.svg" alt="Dez municípios da Região de Integração Xingu">
      </div>
    </div>'''
    s0_js = '''
    tl.fromTo('#e3-s0-wrap', {scale:0.62, opacity:0}, {scale:1, opacity:1, duration:0.6, ease:'power3.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.2);
    '''
    scenes.append((s0_html, s0_js))

    # Scene 2 (7-15s): Mapa recua à esquerda (40%); gráfico diário (1/9-26/10) desenha à direita, base zero
    s1_html = f'''
    <div class="two map-left">
      <div class="stack" style="gap:18px">
        <div class="map-card" style="height:430px">
          <img src="assets/region.svg" alt="Mapa do Xingu">
        </div>
        <h2>{blur_words("Cada barra = 1 dia")}</h2>
        <p class="muted" style="font-size:32px">56 dias validados (1/9 a 26/10/2026 • UTC)</p>
      </div>
      <div style="height:560px;display:flex;flex-direction:column;justify-content:center">
        {daily_bars_svg(mode='build')}
      </div>
    </div>'''
    s1_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    tl.fromTo(el.querySelectorAll('.chart-axis'), {scaleX:0, opacity:0}, {scaleX:1, opacity:1, duration:0.35, ease:'power2.out'}, 0.2);
    tl.fromTo(el.querySelectorAll('.chart-ref'), {opacity:0}, {opacity:1, duration:0.3, ease:'power2.out'}, 0.55);
    tl.fromTo(el.querySelectorAll('.day-bar'), {scaleY:0}, {scaleY:1, duration:0.7, stagger:0.018, ease:'expo.out'}, 0.85);
    '''
    scenes.append((s1_html, s1_js))

    # Scene 3 (15-26s): Barra de 21/09 sobe em âmbar; resto a 25%; mapa mostra só os pontos desse dia; 149 · "21 de setembro"
    s2_html = f'''
    <div class="two map-left" id="e3-s2-stage">
      <div class="stack" style="gap:16px">
        <div class="map-card" style="height:430px" id="e3-s2-map">
          <img src="assets/d-2026-09-21.svg" alt="149 focos no Xingu em 21 de setembro de 2026">
        </div>
        <div class="chip amber">Maior pico de setembro</div>
      </div>
      <div style="height:580px;display:flex;flex-direction:column;justify-content:space-between">
        <div class="halo-box" id="e3-s2-hero" style="display:flex;align-items:baseline;justify-content:space-between">
          <div>
            <div class="eyebrow accent" style="margin-bottom:4px">21 DE SETEMBRO DE 2026</div>
            <div style="font-size:44px;font-weight:700">21 de setembro</div>
          </div>
          <div style="text-align:right">
            <span class="hero-num" id="e3-s2-num">149</span>
            <span class="hero-unit"> focos</span>
          </div>
        </div>
        <div style="height:360px">
          {daily_bars_svg(mode='peak', highlight_date='2026-09-21')}
        </div>
      </div>
    </div>'''
    s2_js = '''
    tl.fromTo('#e3-s2-map', {opacity:0, filter:'blur(8px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 0.1);
    tl.fromTo(el.querySelectorAll('.peak-target'), {scaleY:0}, {scaleY:1, duration:0.7, ease:'expo.out'}, 0.3);
    // Pausa de 0.5s antes do número-clímax 149 pousar fixo
    tl.fromTo('#e3-s2-num', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 1.35);
    tl.to('#e3-s2-stage', {opacity:0, filter:'blur(8px)', duration:0.2, ease:'power2.in'}, 10.78);
    '''
    scenes.append((s2_html, s2_js))

    # Scene 4 (26-31s): Mapa limpa; gráfico segura; "Outubro: 1–26" (T2 entre datas; sem fala - respiro)
    s3_html = f'''
    <div class="two map-left" id="e3-s3-stage">
      <div class="stack" style="gap:18px">
        <div class="map-card" style="height:430px">
          <img src="assets/region.svg" alt="Mapa do Xingu limpo entre datas">
        </div>
        <div class="chip amber">Corte parcial • UTC</div>
      </div>
      <div style="height:580px;display:flex;flex-direction:column;justify-content:space-between">
        <div class="halo-box">
          <div class="eyebrow accent" style="margin-bottom:6px">MUDANÇA DE MÊS</div>
          <h1 style="font-size:84px">{blur_words("Outubro: 1–26")}</h1>
        </div>
        <div style="height:360px">
          {daily_bars_svg(mode='oct-window')}
        </div>
      </div>
    </div>'''
    s3_js = '''
    tl.fromTo('#e3-s3-stage', {opacity:0, filter:'blur(8px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, ease:'power2.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.15);
    tl.to('#e3-s3-stage', {opacity:0, filter:'blur(8px)', duration:0.2, ease:'power2.in'}, 4.78);
    '''
    scenes.append((s3_html, s3_js))

    # Scene 5 (31-42s): Barra de 09/10 em âmbar; número maior que o anterior: 336 · "9 de outubro"
    s4_html = f'''
    <div class="two map-left" id="e3-s4-stage">
      <div class="stack" style="gap:16px">
        <div class="map-card" style="height:430px" id="e3-s4-map">
          <img src="assets/d-2026-10-09.svg" alt="336 focos no Xingu em 9 de outubro de 2026">
        </div>
        <div class="chip amber">Maior pico da série (Outubro: 1–26)</div>
      </div>
      <div style="height:580px;display:flex;flex-direction:column;justify-content:space-between">
        <div class="halo-box" style="display:flex;align-items:baseline;justify-content:space-between">
          <div>
            <div class="eyebrow accent" style="margin-bottom:4px">9 DE OUTUBRO DE 2026</div>
            <div style="font-size:44px;font-weight:700">9 de outubro</div>
          </div>
          <div style="text-align:right">
            <span class="hero-num" id="e3-s4-num" style="font-size:178px">336</span>
            <span class="hero-unit"> focos</span>
          </div>
        </div>
        <div style="height:360px">
          {daily_bars_svg(mode='peak', highlight_date='2026-10-09')}
        </div>
      </div>
    </div>'''
    s4_js = '''
    tl.fromTo('#e3-s4-stage', {opacity:0, filter:'blur(8px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, ease:'power2.out'}, 0);
    tl.fromTo(el.querySelectorAll('.peak-target'), {scaleY:0}, {scaleY:1, duration:0.75, ease:'expo.out'}, 0.25);
    // Pausa de 0.5s antes do número-clímax 336 pousar fixo
    tl.fromTo('#e3-s4-num', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 1.45);
    '''
    scenes.append((s4_html, s4_js))

    # Scene 6 (42-50s): Zoom em Altamira no mapa de 09/10; fração discreta "104 dos 336" · "Foco ≠ área queimada"
    s5_html = f'''
    <div class="two">
      <div class="map-card" style="overflow:hidden" data-layout-allow-overflow>
        <img id="e3-s5-map" src="assets/d-2026-10-09-altamira.svg" alt="Altamira destacada em 9 de outubro com 104 focos">
      </div>
      <div class="stack">
        <div class="eyebrow accent">ALTAMIRA EM 9 DE OUTUBRO</div>
        <h1 style="font-size:112px">{blur_words("104 dos 336")}</h1>
        <p class="support-line">Registros concentrados no maior município da região naquele dia.</p>
        <div class="halo-box" id="e3-s5-note">
          <h2 class="accent" style="font-size:54px">Foco ≠ área queimada</h2>
          <p class="muted" style="font-size:32px;margin-top:8px">Cada ponto indica uma detecção de calor do satélite.</p>
        </div>
      </div>
    </div>'''
    s5_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.15);
    tl.fromTo('#e3-s5-map', {scale:1}, {scale:1.14, duration:0.8, ease:'power2.out'}, 0.1);
    tl.fromTo('#e3-s5-note', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 2.8);
    '''
    scenes.append((s5_html, s5_js))

    # Scene 7 (50-60s): Gráfico completo; quatro outras barras ganham marca fina em ordem cronológica (0.4s cada)
    s6_html = f'''
    <div style="display:flex;flex-direction:column;justify-content:space-between;height:100%">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px">
        <div>
          <div class="chip amber" style="margin-bottom:12px">3 maiores dias de cada mês</div>
          <h2 style="font-size:64px">{blur_words("Poucos dias concentraram muitos focos.")}</h2>
        </div>
        <div class="halo-box" id="e3-s6-next" style="padding:18px 28px;text-align:right">
          <div class="eyebrow accent" style="margin-bottom:4px">PARTE 4</div>
          <div style="font-size:44px;font-weight:700">E em 2025?</div>
        </div>
      </div>
      <div style="display:flex;gap:18px;flex-wrap:wrap">
        <div class="chip peak-pill" data-pill="0">13/09 · <span class="accent">101</span></div>
        <div class="chip amber">21/09 · 149</div>
        <div class="chip peak-pill" data-pill="1">26/09 · <span class="accent">108</span></div>
        <div class="chip amber">09/10 · 336</div>
        <div class="chip peak-pill" data-pill="2">12/10 · <span class="accent">314</span></div>
        <div class="chip peak-pill" data-pill="3">25/10 · <span class="accent">297</span></div>
      </div>
      <div style="height:360px">
        {daily_bars_svg(mode='top6')}
      </div>
    </div>'''
    s6_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    el.querySelectorAll('.peak-mark').forEach((m) => {
      const ord = Number(m.dataset.markOrder || 0);
      tl.fromTo(m, {opacity:0}, {opacity:1, duration:0.25, ease:'power2.out'}, 0.5 + ord * 0.4);
    });
    el.querySelectorAll('.peak-pill').forEach((p) => {
      const ord = Number(p.dataset.pill || 0);
      tl.fromTo(p, {opacity:0.2, filter:'blur(4px)'}, {opacity:1, filter:'blur(0px)', duration:0.25, ease:'power2.out'}, 0.5 + ord * 0.4);
    });
    tl.fromTo('#e3-s6-next', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.25, ease:'power2.out'}, 2.8);
    '''
    scenes.append((s6_html, s6_js))
    return scenes


def build_v4_scenes():
    scenes = []
    # Scene 1 (0-7s): Título "Xingu: 2025 × 2026" · chip "Setembro + 1–26/10 • UTC"
    s0_html = f'''
    <div class="center-stage">
      <div class="chip amber">Setembro + 1–26/10 • UTC</div>
      <h1 style="font-size:102px">{blur_words("Xingu: 2025 × 2026")}</h1>
      <p class="support-line">Mesmo período, mesmo sensor (AQUA_M-T) e mesmos 10 municípios.</p>
    </div>'''
    s0_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.1);
    '''
    scenes.append((s0_html, s0_js))

    # Scene 2 (7-19s): Eixo de base zero; barra de 2025 (cinza-azulado, 1.113) cresce e fica; pausa 0.5s; barra de 2026 (âmbar, 3.688)
    s1_html = f'''
    <div class="center-stage" style="width:100%;max-width:100%">
      <div class="eyebrow">FOCOS DE CALOR DETECTADOS NO XINGU</div>
      <div class="bars-box" style="width:100%">
        <div class="bar-row">
          <div class="bar-year muted">2025</div>
          <div class="bar-track"><div class="bar-fill-2025" id="e4-s1-b25"></div></div>
          <div class="bar-val muted" id="e4-s1-v25">1.113</div>
        </div>
        <div class="bar-row">
          <div class="bar-year accent">2026</div>
          <div class="bar-track"><div class="bar-fill-2026" id="e4-s1-b26"></div></div>
          <div class="bar-val accent" id="e4-s1-v26">3.688</div>
        </div>
        <div class="muted" style="font-size:30px">Base zero • Setembro completo + 1 a 26 de outubro (UTC)</div>
      </div>
    </div>'''
    s1_js = '''
    tl.fromTo('#e4-s1-b25', {scaleX:0}, {scaleX:1, duration:0.7, ease:'expo.out'}, 0.35);
    tl.fromTo('#e4-s1-v25', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 0.85);
    // Frase de 2026 inicia em t=6.0s locais (13.0s absolutos), após pausa de 0.5s
    tl.fromTo('#e4-s1-b26', {scaleX:0}, {scaleX:1, duration:0.75, ease:'expo.out'}, 6.0);
    tl.fromTo('#e4-s1-v26', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 6.6);
    '''
    scenes.append((s1_html, s1_js))

    # Scene 3 (19-26s): Foco entre as barras: +231% pousa fixo, sem contagem; pausa de 0.5s antes
    s2_html = f'''
    <div class="comp-stage">
      <div class="bars-box">
        <div class="bar-row">
          <div class="bar-year muted">2025</div>
          <div class="bar-track"><div class="bar-fill-2025"></div></div>
          <div class="bar-val muted">1.113</div>
        </div>
        <div class="bar-row">
          <div class="bar-year accent">2026</div>
          <div class="bar-track"><div class="bar-fill-2026"></div></div>
          <div class="bar-val accent">3.688</div>
        </div>
      </div>
      <div class="halo-box" id="e4-s2-card" style="text-align:center;padding:44px 36px">
        <div class="eyebrow accent">VARIAÇÃO NO PERÍODO</div>
        <div class="hero-num" id="e4-s2-pct" style="font-size:172px">+231%</div>
        <p class="muted" style="font-size:34px;margin-top:14px">De 1.113 para 3.688 focos detectados</p>
      </div>
    </div>'''
    s2_js = '''
    // Pausa de 0.5s antes de +231% pousar fixo
    tl.fromTo('#e4-s2-card', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.18, ease:'power2.out'}, 0.5);
    tl.fromTo('#e4-s2-pct', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.15, ease:'power2.out'}, 0.55);
    '''
    scenes.append((s2_html, s2_js))

    # Scene 4 (26-37s): Barras a 25%; dois selos, um por vez: "2025: sem El Niño" · "2026: com El Niño" · "Isso não prova a causa."
    s3_html = f'''
    <div class="comp-stage">
      <div class="bars-box dim-25">
        <div class="bar-row">
          <div class="bar-year muted">2025</div>
          <div class="bar-track"><div class="bar-fill-2025"></div></div>
          <div class="bar-val muted">1.113</div>
        </div>
        <div class="bar-row">
          <div class="bar-year accent">2026</div>
          <div class="bar-track"><div class="bar-fill-2026"></div></div>
          <div class="bar-val accent">3.688</div>
        </div>
      </div>
      <div class="stack" style="gap:24px">
        <div class="chip" id="e4-s3-tag1" style="font-size:40px;padding:18px 28px">2025: sem El Niño</div>
        <div class="chip amber" id="e4-s3-tag2" style="font-size:40px;padding:18px 28px;opacity:0">2026: com El Niño</div>
        <div class="halo-box" id="e4-s3-cause" style="opacity:0">
          <h2 style="font-size:56px">Isso não prova a causa.</h2>
          <p class="muted" style="font-size:32px;margin-top:8px">O clima aumenta o risco, mas não explica sozinho.</p>
        </div>
      </div>
    </div>'''
    s3_js = '''
    tl.fromTo('#e4-s3-tag1', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 0.3);
    tl.fromTo('#e4-s3-tag2', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 3.1);
    tl.fromTo('#e4-s3-cause', {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.2, ease:'power2.out'}, 5.2);
    '''
    scenes.append((s3_html, s3_js))

    # Scene 5 (37-47s): Fundo limpo; "Lei 9.605/1998 — art. 41" · "Provocar incêndio em floresta ou em demais formas de vegetação"
    s4_html = f'''
    <div class="center-stage">
      <div class="chip amber">Lei 9.605/1998 — art. 41</div>
      <div class="halo-box" style="padding:42px 48px;max-width:1560px">
        <h1 style="font-size:76px;line-height:1.15">{blur_words("“Provocar incêndio em floresta ou em demais formas de vegetação”")}</h1>
      </div>
      <p class="muted" style="font-size:32px">Lei de Crimes Ambientais (redação da Lei nº 14.944/2024)</p>
    </div>'''
    s4_js = '''
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.2);
    '''
    scenes.append((s4_html, s4_js))

    # Scene 6 (47-60s): T3: câmera recua do número e pousa na captura do aviso (nome oculto), destacando prevenção; frase final parada >= 2s
    s5_html = f'''
    <div class="two" id="e4-s5-stage">
      <div class="stack">
        <div id="e4-s5-recede" class="chip" style="font-size:28px">2025: 1.113 → 2026: 3.688 (+231%)</div>
        <h1 style="font-size:84px">{blur_words("Acompanhe os alertas. Evite provocar incêndios.")}</h1>
        <p class="support-line">Prevenir é proteger a floresta, a saúde e quem vive aqui.</p>
        <div class="chip amber">pulso. • INPE / AQUA_M-T • IBGE • NOAA</div>
      </div>
      <div class="phone-frame" id="e4-s5-phone" data-layout-allow-overflow>
        <div class="phone-inner" style="transform:scale(1.06) translateY(-195px)">
          <img src="assets/aviso.png" alt="Captura do alerta GovBR destacando orientações de prevenção">
          <div class="phone-dim-top" style="top:0;height:546px"></div>
          <div class="phone-highlight" style="top:548px;height:184px"></div>
          <div class="phone-dim-bot" style="top:736px;bottom:0"></div>
        </div>
      </div>
    </div>'''
    s5_js = '''
    // T3: Recuo de chegada (scale 1 -> 0.6 no elemento de partida / câmera recuando de 1.38 -> 1.0 com blur máx 6px)
    tl.fromTo('#e4-s5-stage', {scale:1.38, filter:'blur(6px)'}, {scale:1, filter:'blur(0px)', duration:0.75, ease:'power3.out'}, 0);
    tl.fromTo('#e4-s5-recede', {scale:1.25}, {scale:1, duration:0.75, ease:'power3.out'}, 0);
    tl.fromTo(el.querySelectorAll('.bw'), {opacity:0, filter:'blur(6px)'}, {opacity:1, filter:'blur(0px)', duration:0.13, stagger:0.07, ease:'power2.out'}, 0.35);
    '''
    scenes.append((s5_html, s5_js))
    return scenes


def speech(ep, directory):
    """Fit each recorded line into its slot; pad final audio to exact 60.000s (2,880,000 samples @ 48kHz)."""
    tracks = []
    captions = []
    report = []
    units = []
    for scene_index, scene in enumerate(ep['scenes']):
        if scene.get('phrases'):
            for j, phrase in enumerate(scene['phrases']):
                units.append((f'e{ep["episode"]}-{scene_index:02}-p{j}', phrase))
        elif scene.get('text', '').strip():
            units.append((f'e{ep["episode"]}-{scene_index:02}', scene))

    for i, (stem_name, scene) in enumerate(units):
        stem = ROOT / 'speech' / stem_name
        with wave.open(str(stem.with_suffix('.wav'))) as f:
            duration = f.getnframes() / f.getframerate()
        window = scene['end'] - scene['start']
        available = window - 0.45
        tempo = max(1.0, duration / available)
        assert tempo < 1.55, f'Speech too fast: ep={ep["episode"]} unit={stem_name} tempo={tempo:.2f}'
        output = directory / 'assets' / f'voice-{i}.wav'
        command([FFMPEG_CMD, '-y', '-i', stem.with_suffix('.wav'), '-af', f'atempo={tempo:.8f},aresample=48000', '-ac', '1', output])
        start = scene['start'] + 0.16
        tracks.append((output, start))
        words = json.loads(stem.with_suffix('.json').read_text(encoding='utf-8-sig'))
        if isinstance(words, dict):
            words = [words]
        groups = []
        group = []
        for word in words:
            group.append(word)
            pos = word['char_start'] + word['char_count']
            suffix = scene['text'][pos:pos + 1]
            if len(group) >= 7 or suffix in ['.', '?', ':', '!']:
                groups.append(group)
                group = []
        if group:
            groups.append(group)
        for j, group in enumerate(groups):
            a = group[0]['char_start']
            b = (groups[j + 1][0]['char_start'] if j + 1 < len(groups) else len(scene['text']))
            caption = scene['text'][a:b].strip()
            begin = start + group[0]['start'] / tempo
            end = (start + groups[j + 1][0]['start'] / tempo if j + 1 < len(groups) else start + duration / tempo + 0.12)
            end = min(end, scene['end'] - 0.12)
            if end > begin and caption:
                captions.append(dict(start=round(begin, 4), end=round(end, 4), text=caption))
        report.append(dict(unit=stem_name, start=start, raw_duration=round(duration, 3), tempo=round(tempo, 4), end=round(start + duration / tempo, 3)))

    raw_mix = directory / 'assets/narracao-raw.wav'
    final_wav = directory / 'assets/narracao.wav'
    args = [FFMPEG_CMD, '-y']
    for path, _ in tracks:
        args += ['-i', path]
    filters = []
    for i, (_, start) in enumerate(tracks):
        filters.append(f'[{i}:a]adelay={round(start * 1000)}:all=1[a{i}]')
    filters.append(
        ''.join(f'[a{i}]' for i in range(len(tracks)))
        + f'amix=inputs={len(tracks)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000,apad=whole_dur=60.5,atrim=0:60[out]'
    )
    command(args + ['-filter_complex', ';'.join(filters), '-map', '[out]', '-ar', '48000', '-ac', '2', raw_mix])

    # Guarantee exact 60.000000s (2,880,000 stereo frames at 48kHz) so HyperFrames clip_media_fit never triggers
    target_frames = 60 * 48000
    with wave.open(str(raw_mix), 'rb') as rf:
        params = rf.getparams()
        frames = rf.readframes(target_frames)
        actual_frames = len(frames) // (params.nchannels * params.sampwidth)
        if actual_frames < target_frames:
            frames += b'\x00' * ((target_frames - actual_frames) * params.nchannels * params.sampwidth)
        elif actual_frames > target_frames:
            frames = frames[:target_frames * params.nchannels * params.sampwidth]
    with wave.open(str(final_wav), 'wb') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(frames)
    raw_mix.unlink(missing_ok=True)

    (directory / 'captions.json').write_text(json.dumps(captions, ensure_ascii=False, indent=2), encoding='utf-8')
    (directory / 'audio-report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

    def tc(t):
        ms = round(t * 1000)
        return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'

    (directory / 'legendas.srt').write_text(
        '\n\n'.join(f'{i + 1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i, c in enumerate(captions)),
        encoding='utf-8',
    )
    return captions


def write_captions_subcomp(ep_num, captions, scenes_dir):
    """Write a dedicated captions sub-composition driven by GSAP timeline per references/captions.md."""
    comp_id = f'e{ep_num}-captions'
    items = []
    tweens = []
    for i, c in enumerate(captions):
        cid = f'e{ep_num}-cap-{i}'
        st = c['start']
        en = c['end']
        items.append(
            f'<div id="{cid}" class="caption-host" style="opacity:0;visibility:hidden">'
            f'<div class="caption-box"><p>{esc(c["text"])}</p></div></div>'
        )
        tweens.append(
            f'tl.set("#{cid}", {{visibility:"visible", opacity:0}}, {st:.4f});'
            f'tl.fromTo("#{cid}", {{opacity:0}}, {{opacity:1, duration:0.08, ease:"power2.out", immediateRender:false}}, {st:.4f});'
            f'tl.to("#{cid}", {{opacity:0, duration:0.08, ease:"power2.in"}}, {max(st + 0.09, en - 0.08):.4f});'
            f'tl.set("#{cid}", {{opacity:0, visibility:"hidden"}}, {en:.4f});'
        )
    html_doc = f'''<!doctype html><html lang="pt-BR"><body><template>
<style>#root {{ position: absolute; inset: 0; pointer-events: none; }}</style>
<div id="root" data-composition-id="{comp_id}" data-width="1920" data-height="1080">
{''.join(items)}
</div>
<script>
(()=>{{
  const tl = gsap.timeline({{paused:true}});
  {''.join(tweens)}
  window.__timelines = window.__timelines || {{}};
  window.__timelines['{comp_id}'] = tl;
}})();
</script>
</template></body></html>'''
    (scenes_dir / f'{comp_id}.html').write_text(html_doc, encoding='utf-8')
    return (
        f'<div id="{comp_id}" class="clip" data-composition-id="{comp_id}" '
        f'data-composition-src="compositions/{comp_id}.html" data-start="0" data-duration="60" '
        f'data-track-index="1" data-track-kind="captions" data-width="1920" data-height="1080" '
        f'style="position:absolute;inset:0;pointer-events:none;z-index:20"></div>'
    )


def build():
    validate_data()
    aviso_path = ensure_aviso_image()
    gsap_bytes = (ROOT / 'episodio-1/assets/gsap.min.js').read_bytes()
    (ROOT / 'renders').mkdir(exist_ok=True)

    builders = {
        1: build_v1_scenes,
        2: build_v2_scenes,
        3: build_v3_scenes,
        4: build_v4_scenes,
    }

    for ep in SCRIPT:
        n = ep['episode']
        folder = ROOT / f'episodio-{n}'
        assets = folder / 'assets'
        scenes_dir = folder / 'compositions'
        assets.mkdir(parents=True, exist_ok=True)
        scenes_dir.mkdir(parents=True, exist_ok=True)
        for old_file in scenes_dir.glob('*.html'):
            old_file.unlink()

        (assets / 'gsap.min.js').write_bytes(gsap_bytes)
        for font in ['segoeui.ttf', 'segoeuib.ttf']:
            shutil.copyfile(Path('C:/Windows/Fonts') / font, assets / font)
        shutil.copyfile(aviso_path, assets / 'aviso.png')

        # Generate required SVG maps
        (assets / 'overview-empty.svg').write_text(svg_overview('empty'), encoding='utf-8')
        (assets / 'overview-xingu.svg').write_text(svg_overview('xingu'), encoding='utf-8')
        if n == 2:
            (assets / 'overview-sep2026.svg').write_text(svg_overview('sep2026'), encoding='utf-8')
            (assets / 'overview-oct2026.svg').write_text(svg_overview('oct2026'), encoding='utf-8')
        (assets / 'region.svg').write_text(svg_region(), encoding='utf-8')
        if n == 3:
            for date in PEAKS:
                day = next(d for d in DATA['dias'] if d['dia_utc'] == date)
                (assets / f'd-{date}.svg').write_text(svg_region(day=day), encoding='utf-8')
            day_0910 = next(d for d in DATA['dias'] if d['dia_utc'] == '2026-10-09')
            (assets / 'd-2026-10-09-altamira.svg').write_text(svg_region(day=day_0910, highlight_altamira=True), encoding='utf-8')

        captions = speech(ep, folder)
        built_scenes = builders[n]()
        assert len(built_scenes) == len(ep['scenes']), f'Scene count mismatch in ep {n}'

        hosts = []
        board = []
        for i, (scene_meta, (inner_html, scene_js)) in enumerate(zip(ep['scenes'], built_scenes)):
            comp_id = f'e{n}-s{i}'
            dur = scene_meta['end'] - scene_meta['start']
            scene_html = f'''<!doctype html><html lang="pt-BR"><body><template>
<style>#root {{ position: absolute; inset: 0; }}</style>
<div id="root" data-composition-id="{comp_id}" data-width="1920" data-height="1080">
  <div class="stage"><div class="inside">{inner_html}</div></div>
</div>
<script>
(()=>{{
  const el = document.querySelector('[data-composition-id="{comp_id}"]');
  const tl = gsap.timeline({{paused:true}});
  {scene_js}
  window.__timelines = window.__timelines || {{}};
  window.__timelines['{comp_id}'] = tl;
}})();
</script>
</template></body></html>'''
            (scenes_dir / f'{comp_id}.html').write_text(scene_html, encoding='utf-8')
            hosts.append(
                f'<div id="{comp_id}" class="clip" data-composition-id="{comp_id}" '
                f'data-composition-src="compositions/{comp_id}.html" data-start="{scene_meta["start"]}" '
                f'data-duration="{dur}" data-track-index="0" data-track-kind="graphics" '
                f'data-width="1920" data-height="1080" style="position:absolute;inset:0;z-index:10"></div>'
            )
            spoken = scene_meta['text'] if scene_meta['text'] else '(Respiro visual — sem locução)'
            board.append(
                f'## Frame {i + 1} — Cena {i + 1} ({scene_meta["start"]}–{scene_meta["end"]}s)\n\n'
                f'- status: built\n- src: compositions/{comp_id}.html\n- duration: {dur}s\n\n{spoken}\n'
            )

        captions_host = write_captions_subcomp(n, captions, scenes_dir)
        footer_text = 'Focos de calor detectados — INPE / AQUA_M-T • Setembro e 1–26/10/2026 • UTC'

        page = f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>Fogo no Xingu — Parte {n} de 4</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="60" data-fps="30">
  <div class="brand">pulso<span class="accent">.</span></div>
  <div class="series">FOGO NO XINGU • {esc(ep["title"].upper())}</div>
  <div class="episode-pill">Parte {n} de 4</div>
  <div class="rule"></div>
  {''.join(hosts)}
  {captions_host}
  <div class="foot"><span>{footer_text}</span><span>Limites IBGE 2024 • NOAA 08/10/2026</span></div>
  <div class="progress"></div>
  <audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="60" data-track-index="2" data-volume="1"></audio>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo('.progress', {{scaleX:0}}, {{scaleX:1, duration:60, ease:'none'}}, 0);
window.__timelines = window.__timelines || {{}};
window.__timelines['main'] = tl;
</script></body></html>'''
        (folder / 'index.html').write_text(page, encoding='utf-8')
        (folder / 'STORYBOARD.md').write_text(
            f'---\nformat: 1920x1080\nduration: 60s\nmessage: {ep["closing_line"]}\n---\n\n' + '\n'.join(board),
            encoding='utf-8',
        )
        spoken_scenes = [p for s in ep['scenes'] for p in s.get('phrases', [s]) if p.get('text')]
        (folder / 'SCRIPT.md').write_text(
            '\n\n'.join(f'[{s["start"]}–{s["end"]}s] {s["text"]}' for s in spoken_scenes),
            encoding='utf-8',
        )
        ep_ledger = {
            'episode': n,
            'title': ep['title'],
            'question': ep['question'],
            'closing_line': ep['closing_line'],
            'seams': [s for s in LEDGER['seams'] if s['episode'] == n],
            'scenes': [
                {'id': f'e{n}-s{i}', 'start': s['start'], 'end': s['end'], 'word_count': len(s['text'].split()) if s['text'] else 0}
                for i, s in enumerate(ep['scenes'])
            ],
        }
        (folder / 'ledger.json').write_text(json.dumps(ep_ledger, ensure_ascii=False, indent=2), encoding='utf-8')
        config = dict(
            paths=dict(blocks='compositions', components='compositions/components', assets='assets'),
            authoringSkill='hyperframes',
            media=dict(autoProxy=False),
        )
        (folder / 'hyperframes.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
        (folder / 'package.json').write_text(
            json.dumps(
                dict(
                    name=f'pulso-xingu-v2-episodio-{n}',
                    private=True,
                    scripts=dict(
                        check='hyperframes check',
                        render=f'hyperframes render --fps 30 --quality delivery --output ../renders/0{n}.mp4',
                    ),
                ),
                indent=2,
            ),
            encoding='utf-8',
        )
        print(f'Built V2 episode {n} ({ep["title"]}): {len(ep["scenes"])} scenes, {len(captions)} captions.', flush=True)


if __name__ == '__main__':
    build()
