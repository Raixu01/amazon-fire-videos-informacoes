"""Build the four local HyperFrames projects, voice tracks and timed captions."""
from pathlib import Path
import collections
import csv
import html
import json
import math
import re
import shutil
import subprocess
import wave
import imageio_ffmpeg
from shapely.geometry import LineString

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
DATA = json.loads((REPO / 'remotion/src/xingu-dados.json').read_text(encoding='utf-8'))
SCRIPT = json.loads((ROOT / 'script.json').read_text(encoding='utf-8'))
FF = imageio_ffmpeg.get_ffmpeg_exe()
COLORS = ['#18383d', '#34584c', '#73784b', '#bc8a49', '#e7aa5b', '#ffd293']
NAMES = {m['codigo_ibge']: m['nome'] for m in DATA['municipios']}
REGION = [m for m in DATA['municipios'] if m['xingu']]
VISUAL_PATHS = {}
for m in DATA['municipios']:
    rings=[]
    for ring in re.findall(r'M([^M]+)', m['path']):
        coords=[tuple(map(float, p)) for p in re.findall(r'(-?[\d.]+),(-?[\d.]+)',ring)]
        if len(coords)<3:continue
        simple=list(LineString(coords).simplify(.24).coords)
        if len(simple)<3:simple=coords
        rings.append('M'+'L'.join(f'{a:.2f},{b:.2f}' for a,b in simple)+'Z')
    VISUAL_PATHS[m['codigo_ibge']]=''.join(rings)
PEAKS = ['2026-09-13','2026-09-21','2026-09-26','2026-10-09','2026-10-12','2026-10-25']


def esc(s):
    return html.escape(str(s), quote=True)


def number(n):
    return f'{n:,}'.replace(',', '.')


def command(args):
    subprocess.run([str(x) for x in args], check=True, capture_output=True)


def validate_data():
    snapshot = REPO / 'entregas/amazonia-xingu/snapshots' / DATA['snapshot_id']
    totals = collections.Counter()
    with (snapshot / 'xingu_diario.csv').open(encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row['estado'] == 'validado':
                totals[row['data_utc']] += int(row['focos'])
    assert sum(totals.values()) == 3688
    for month in ['2026-09','2026-10']:
        top = sorted((d for d in totals if d.startswith(month)), key=lambda d: (-totals[d],d))[:3]
        assert set(top) == {d for d in PEAKS if d.startswith(month)}
    for d in DATA['dias']:
        if d['estado'] == 'validado':
            assert d['focos'] == totals[d['dia_utc']] == len(d['pontos'])
    assert DATA['comparativos'][-1]['atual'] == 3688
    assert DATA['comparativos'][-1]['anterior'] == 1113
    print('Data: daily counts, top days and comparison reconciled.', flush=True)


def svg_map(region=False, state=None, day=None, highlight=False):
    bounds = DATA['xingu_bounds'] if region else DATA['map_bounds']
    x,y,w,h = bounds
    pad = .035 * max(w,h)
    view = f'{x-pad} {y-pad} {w+2*pad} {h+2*pad}'
    paths = []
    for m in (REGION if region else DATA['municipios']):
        fill = '#254c43' if region else '#244047'
        stroke = '#9bb6aa' if region else '#6a8785'
        if highlight and m['xingu']:
            fill,stroke = '#abd5bd','#f5f1e8'
        if state:
            n = state['municipios'].get(m['codigo_ibge'],0)
            i = next((i for i,v in enumerate(DATA['escala']) if n <= v),5)
            fill = COLORS[i]
        visual_path = m['path'] if region else VISUAL_PATHS[m['codigo_ibge']]
        paths.append(f'<path d="{visual_path}" fill="{fill}" stroke="{stroke}" stroke-width="{.35 if region else .16}"/>')
    if day:
        for px,py,municipality in day['pontos']:
            paths.append(f'<circle cx="{px}" cy="{py}" r="1.05" fill="#ffc277" fill-opacity=".88"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" width="1000" height="800">'+''.join(paths)+'</svg>'


CSS = '''
@font-face{font-family:Pulso;src:url('assets/segoeui.ttf')}@font-face{font-family:Pulso;src:url('assets/segoeuib.ttf');font-weight:700}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden;background:#10282d;color:#f5f1e8;font-family:Pulso,system-ui,sans-serif}
#root{position:relative;width:100%;height:100%;overflow:hidden}h1,h2,p{margin:0}h1{font-size:94px;font-weight:700;line-height:1.07;letter-spacing:-3px}h2{font-size:68px;line-height:1.13;letter-spacing:-1.5px}p{font-size:42px;line-height:1.35}.muted{color:#c0d0c8}.accent{color:#ffc277}.green{color:#abd5bd}.eyebrow{font-size:25px;font-weight:700;letter-spacing:3px;text-transform:uppercase;margin-bottom:24px}
.brand{position:absolute;left:76px;top:32px;font-size:40px;font-weight:700;letter-spacing:-2px}.episode{position:absolute;right:76px;top:48px;font-size:24px;letter-spacing:2px;color:#c0d0c8}.series{position:absolute;left:242px;top:49px;font-size:23px;color:#c0d0c8;letter-spacing:2px}.rule{position:absolute;left:76px;right:76px;top:108px;height:1px;background:#365157}
.stage{position:absolute;inset:150px 76px 218px;overflow:hidden}.inside{position:relative;width:100%;height:100%}.two{display:grid;grid-template-columns:1.02fr 1fr;gap:70px;align-items:center;height:100%}.two.wide{grid-template-columns:1.2fr .8fr}.stack{display:flex;flex-direction:column;justify-content:center;gap:30px;height:100%}.lead{max-width:820px;font-size:46px;line-height:1.3}.tag{display:inline-block;align-self:flex-start;padding:10px 18px;border:1px solid #7b9991;border-radius:5px;font-size:24px;color:#c0d0c8}.label{font-size:30px;color:#c0d0c8}.big{font-size:170px;line-height:1;font-weight:700;letter-spacing:-6px}.large{font-size:116px;line-height:1.05;font-weight:700;letter-spacing:-3px}.medium{font-size:64px;line-height:1.15;font-weight:700}.small{font-size:28px;line-height:1.35}.foot{position:absolute;left:76px;bottom:20px;font-size:21px;color:#c0d0c8}.cut{position:absolute;right:76px;bottom:20px;font-size:21px;color:#c0d0c8}.progress{position:absolute;bottom:0;left:0;width:1920px;height:5px;background:#ffc277;transform-origin:left center}
.caption{position:absolute;left:180px;right:180px;bottom:75px;display:flex;justify-content:center;align-items:center;min-height:103px;pointer-events:none}.caption p{font-size:40px;line-height:1.25;text-align:center;background:#091b20;padding:13px 25px;border-radius:9px;max-width:1500px;color:#f5f1e8}
.map{width:100%;height:100%;object-fit:contain}.mapbox{height:570px;position:relative}.screenshot{position:relative;width:340px;height:723px;margin:auto;overflow:hidden;border-radius:22px;border:2px solid #4c686b}.screenshot img{width:340px;height:auto;display:block}.name-mask{position:absolute;left:38px;top:89px;width:205px;height:24px;background:#232525}.quote{font-size:57px;line-height:1.22;font-weight:700}.quote-line{margin-top:28px;font-size:32px;color:#c0d0c8}.note{font-size:29px;line-height:1.35;color:#c0d0c8;max-width:780px}.chain{display:flex;gap:25px;align-items:center;margin-top:65px}.chain-step{width:500px;border:1px solid #4c686b;border-radius:16px;padding:45px 30px;min-height:200px;display:flex;align-items:center;font-size:49px;font-weight:700}.arrow{font-size:60px;color:#ffc277}.numbered{display:flex;gap:25px;align-items:center;border-bottom:1px solid #365157;padding:25px 0}.numbered b{font-size:46px;color:#ffc277;min-width:50px}.numbered span{font-size:41px}
.history-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.year{font-size:85px;font-weight:700;letter-spacing:-3px}.history-pair{display:grid;grid-template-columns:1fr 1fr;gap:55px;height:535px}.hist-panel{position:relative}.hist-label{display:flex;justify-content:space-between;font-size:35px;font-weight:700}.hist-panel img{width:100%;height:405px;object-fit:contain}.hist-total{font-size:40px;font-weight:700;color:#ffc277}.legend{display:flex;align-items:center;gap:18px;font-size:24px;justify-content:center;margin-top:12px}.legend span{display:flex;align-items:center;gap:8px}.legend i{display:block;width:28px;height:16px}.yearline{position:absolute;bottom:0;left:0;right:0;display:flex;justify-content:space-between;gap:12px;color:#91aaa2;font-size:29px}.yearline b{color:#ffc277}.peak-layout{display:grid;grid-template-columns:930px 1fr;gap:60px;height:100%}.peak-map{position:relative;height:600px}.peak-info{display:flex;flex-direction:column;justify-content:center;gap:18px}.ranks{margin-top:15px;display:flex;flex-direction:column;gap:12px}.rank{display:flex;justify-content:space-between;font-size:31px;border-bottom:1px solid #365157;padding-bottom:10px}.daily-context{position:absolute;left:10px;bottom:4px;width:880px;height:90px}.date-list{display:flex;gap:24px;margin-top:42px}.date-item{padding:22px 30px;border:1px solid #4c686b;border-radius:12px;font-size:32px}.date-item b{display:block;font-size:50px;color:#ffc277}.barrow{display:grid;grid-template-columns:150px 1fr 180px;gap:28px;align-items:center;margin-top:38px;font-size:48px}.bartrack{height:76px;width:100%;background:#233e43;border-radius:6px;overflow:hidden}.barfill{height:100%;background:#ffc277;width:100%;transform-origin:left center}.barfill.old{background:#abd5bd}.barlabel{font-weight:700}.law{font-size:68px;line-height:1.2;font-weight:700;max-width:1400px}.lawbox{border-top:2px solid #ffc277;padding-top:45px;margin-top:30px}.callout{font-size:33px;line-height:1.35;border:1px solid #4c686b;border-radius:12px;padding:24px 30px}.climate{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin-top:48px}.climate-box{padding:35px;border:1px solid #4c686b;border-radius:15px}.climate-box strong{display:block;font-size:68px;color:#ffc277}.climate-box span{font-size:39px}.subtle-map{position:absolute;right:-30px;top:0;width:850px;height:700px;opacity:.24}.overview-label{position:absolute;left:430px;top:118px;font-size:30px;color:#abd5bd;font-weight:700}
 .history-state{opacity:0}.year{font-size:72px;line-height:1}.history-pair{height:500px}.hist-panel img{height:440px}
'''


def screenshot():
    return '<div class="screenshot"><img src="assets/aviso.png" alt="Alerta de incêndios recebido em 11 de outubro de 2026"><div class="name-mask"></div></div>'


def title(kicker, title, body='', extra=''):
    return f'<div class="stack"><div class="eyebrow accent">{kicker}</div><h1>{title}</h1>{f"<p class=lead>{body}</p>" if body else ""}{extra}</div>'


def historical(year):
    pair = [s for s in DATA['historico'] if s['ano']==year]
    panels = []
    for state in pair:
        month = 'Setembro' if state['mes']==9 else 'Outubro'
        partial = year==2026 and state['mes']==10
        label = '1–26/10 · parcial' if partial else month
        panels.append(f'<div class="hist-panel"><div class="hist-label"><span>{label}</span><span class="hist-total">{number(state["focos_observados"])} focos</span></div><img src="assets/h-{year}-{state["mes"]}.svg" alt="Mapa municipal de {month} de {year}"></div>')
    legend = ''.join(f'<span><i style="background:{c}"></i>{v}</span>' for c,v in zip(COLORS,['0','1–2','3–7','8–26','27–77','78+']))
    years=''.join(f'<{"b" if y==year else "span"}>{y}</{"b" if y==year else "span"}>' for y in range(2020,2027))
    return f'<div class="history-head"><div><div class="eyebrow" style="margin:0">AMAZÔNIA LEGAL</div><div class="small muted">Focos por município · mesma escala</div></div><div class="year">{year}</div></div><div class="history-pair">'+''.join(panels)+f'</div><div class="legend">{legend}</div><div class="yearline">{years}</div>'


def context_chart(day):
    month = day[5:7]
    values=[d for d in DATA['dias'] if d['dia_utc'][5:7]==month and d['estado']=='validado']
    bars=[]
    for i,d in enumerate(values):
        height=d['focos']/336*66
        fill='#ffc277' if d['dia_utc']==day else '#658c7b'
        bars.append(f'<rect x="{i*27+6}" y="{68-height}" width="18" height="{height}" fill="{fill}"/>')
    return '<svg class="daily-context" viewBox="0 0 880 90"><text x="6" y="87" fill="#c0d0c8" font-size="15">Outros dias do mês · escala fixa de 0 a 336 focos</text>'+''.join(bars)+'</svg>'


def peak(day):
    d=next(d for d in DATA['dias'] if d['dia_utc']==day)
    ranks=sorted(d['municipios'].items(),key=lambda x:-x[1])[:3]
    date=day[8:10]+'/'+day[5:7]+'/2026'
    ranks_html=''.join(f'<div class="rank"><span>{esc(NAMES[k])}</span><strong>{n}</strong></div>' for k,n in ranks)
    return f'<div class="peak-layout"><div class="peak-map"><img class="map" src="assets/d-{day}.svg" alt="Focos detectados no Xingu em {date}">{context_chart(day)}</div><div class="peak-info"><div class="eyebrow accent">XINGU · TOTAL DO DIA</div><div class="medium">{date}</div><div><span class="big accent">{d["focos"]}</span><span class="label"> focos</span></div><div class="ranks">{ranks_html}</div><div class="small muted">Um ponto indica uma detecção, não a área queimada.</div></div></div>'


def scene_content(ep, i):
    if ep==1:
        if i==0:return '<div class="two wide">'+title('UM AVISO PERTO DE VOCÊ','Você também recebeu?', 'Sua região está sob alerta de incêndios.', '<div class="tag">Mensagem de 11/10/2026</div>')+screenshot()+'</div>'
        if i==1:return '<div class="two wide">'+title('O QUE O AVISO DIZ','O risco também está na fumaça.','Ela pode chegar até a nossa casa.')+'<div class="stack"><div class="quote accent">“A fumaça pode causar problemas respiratórios.”</div><div class="quote-line">Trecho da mensagem recebida</div><div class="callout">O aviso traz cuidados para reduzir a exposição.</div></div></div>'
        if i==2:return '<div class="stack"><div class="eyebrow accent">ÉPOCA DE ESTIAGEM</div><h1>O fogo encontra condições para se espalhar.</h1><div class="chain"><div class="chain-step">Menos chuva</div><div class="arrow">→</div><div class="chain-step">Vegetação mais seca</div><div class="arrow">→</div><div class="chain-step accent">Maior risco</div></div></div>'
        if i==3:return '<div class="two">'+title('FUMAÇA E SAÚDE','Quem precisa de mais atenção?', 'Acompanhe as orientações oficiais.')+'<div class="stack"><div class="numbered"><b>01</b><span>Crianças</span></div><div class="numbered"><b>02</b><span>Idosos</span></div><div class="numbered"><b>03</b><span>Pessoas com doenças respiratórias</span></div></div></div>'
        return '<div class="two">'+title('NO PRÓXIMO VÍDEO','O que os satélites mostram?', 'Vamos começar pelo mapa.', '<div class="tag">Parte 2 · O contexto amazônico</div>')+'<div class="mapbox"><img class="map" src="assets/overview.svg" alt="Localização do Xingu na Amazônia Legal"><span class="overview-label">Xingu</span></div></div>'
    if ep==2:
        if i==0:return '<div class="two">'+title('ENTENDA O CONTEXTO','Por que falar de fogo agora?', 'A estiagem deixa a vegetação mais vulnerável.')+'<div class="mapbox"><img class="map" src="assets/overview.svg" alt="Amazônia Legal com o Xingu destacado"></div></div>'
        if i==1:
            return ''.join(f'<div class="history-state" data-at="{k*22/7}" data-until="{(k+1)*22/7}" style="position:absolute;inset:0">{historical(y)}</div>' for k,y in enumerate(range(2020,2027)))
        if i==2:return '<div class="two">'+title('CLIMA E RISCO','El Niño pode favorecer a seca.', 'Menos chuva pode facilitar a propagação do fogo.')+'<div class="stack"><div class="eyebrow green">OUTUBRO DE 2026</div><div class="large accent">El Niño em curso</div><div class="note">Condição confirmada pela NOAA em 08/10/2026.</div><div class="tag">2023–2024: episódio anterior</div></div></div>'
        if i==3:return title('A DISTINÇÃO IMPORTA','O clima aumenta o risco.', 'A origem do fogo e as condições locais também precisam ser consideradas.', '<div class="callout">El Niño não explica sozinho o número de focos.</div>')
        return '<div class="two">'+title('APROXIMANDO O MAPA','E aqui no Xingu?', 'Dez municípios do Pará, em detalhe.', '<div class="tag">Parte 3 · Os dias de maior pico</div>')+'<div class="mapbox"><img class="map regional-zoom" src="assets/region.svg" alt="Região de Integração Xingu"></div></div>'
    if ep==3:
        if i==0:return '<div class="two">'+title('REGIÃO DE INTEGRAÇÃO XINGU','Alguns dias concentram mais focos.', 'Não é igual todos os dias.')+'<div class="mapbox"><img class="map" src="assets/region.svg" alt="Dez municípios do Xingu"></div></div>'
        if i==1:return title('COMO FIZEMOS O RECORTE','3 maiores picos de cada mês.', 'Setembro completo e outubro até o dia 26.', '<div class="callout">Dez municípios · seis datas selecionadas · ordem cronológica</div>')
        if i in (2,3):
            dates=PEAKS[:3] if i==2 else PEAKS[3:]
            return ''.join(f'<div class="history-state" data-at="{k*5}" data-until="{(k+1)*5}" style="position:absolute;inset:0">{peak(d)}</div>' for k,d in enumerate(dates))
        if i==4:return '<div class="two"><div class="mapbox"><img class="map" src="assets/d-2026-10-09.svg" alt="Focos no Xingu em 9 de outubro"></div>'+title('09 DE OUTUBRO · ALTAMIRA','104 focos', 'Dos 336 registrados na região naquele dia.', '<div class="callout">Focos detectados não medem hectares queimados.</div>')+'</div>'
        return title('NO PRÓXIMO VÍDEO','O que mudou desde 2025?', 'Vamos comparar os mesmos períodos.', '<div class="tag">Parte 4 · Comparação e responsabilidade</div>')
    if i==0:return title('XINGU · 2025 × 2026','O que mudou de um ano para o outro?', 'Setembro + 1 a 26 de outubro.', '<div class="tag">Mesmos períodos · mesmo sensor · mesmo território</div>')
    if i==1:return '<div class="two wide"><div class="stack"><div class="eyebrow green">FOCOS DETECTADOS NO XINGU</div><h2>Nos mesmos períodos:</h2><div class="barrow"><span>2025</span><div class="bartrack"><div class="barfill old" data-ratio="0.3017896"></div></div><span class="barlabel">1.113</span></div><div class="barrow"><span>2026</span><div class="bartrack"><div class="barfill" data-ratio="1"></div></div><span class="barlabel">3.688</span></div><div class="small muted">Base zero · setembro + 1–26 de outubro</div></div><div class="stack" style="padding-left:50px"><div class="big accent">+231%</div><p>de focos detectados</p><div class="note">Mais de três vezes o total do período anterior.</div></div></div>'
    if i==2:return '<div class="stack"><div class="eyebrow accent">O PAPEL DO CLIMA</div><h2>O cenário climático mudou.</h2><div class="climate"><div class="climate-box"><strong>2025</strong><span>Sem El Niño no período</span></div><div class="climate-box"><strong>2026</strong><span>Com El Niño no período</span></div></div><div class="callout">A comparação não prova quanto do aumento se deve ao El Niño.</div></div>'
    if i==3:return '<div class="stack"><div class="eyebrow accent">LEI DE CRIMES AMBIENTAIS</div><h2>Provocar incêndio é crime ambiental.</h2><div class="lawbox"><div class="law">“Provocar incêndio em floresta ou em demais formas de vegetação:”</div></div><div class="note">Lei 9.605/1998, art. 41 · redação da Lei 14.944/2024</div></div>'
    return '<div class="two wide">'+title('O ALERTA MERECE ATENÇÃO','Prevenir incêndios é proteger a vida.', 'A floresta, a saúde e quem vive aqui.', '<div class="tag">Acompanhe as orientações oficiais.</div>')+screenshot()+'</div>'


def speech(ep, directory):
    """Fit each recorded line into its slot; derive captions from SAPI word times."""
    tracks=[]
    captions=[]
    report=[]
    units=[]
    for scene_index,scene in enumerate(ep['scenes']):
        if scene.get('phrases'):
            for j,phrase in enumerate(scene['phrases']):
                units.append((f'e{ep["episode"]}-{scene_index:02}-p{j}',phrase))
        else:units.append((f'e{ep["episode"]}-{scene_index:02}',scene))
    for i,(stem_name,scene) in enumerate(units):
        stem=ROOT/'speech'/stem_name
        with wave.open(str(stem.with_suffix('.wav'))) as f:
            duration=f.getnframes()/f.getframerate()
        window=scene['end']-scene['start']
        available=window-.75
        tempo=max(1.0,duration/available)
        assert tempo<1.55, (ep['episode'],i,tempo)
        output=directory/'assets'/f'voice-{i}.wav'
        command([FF,'-y','-i',stem.with_suffix('.wav'),'-af',f'atempo={tempo:.8f},aresample=48000','-ac','1',output])
        start=scene['start']+.22
        tracks.append((output,start))
        words=json.loads(stem.with_suffix('.json').read_text(encoding='utf-8-sig'))
        if isinstance(words,dict):words=[words]
        groups=[]
        group=[]
        for word in words:
            group.append(word)
            pos=word['char_start']+word['char_count']
            suffix=scene['text'][pos:pos+1]
            if len(group)>=8 or suffix in ['.', '?', ':', '!']:
                groups.append(group);group=[]
        if group:groups.append(group)
        for j,group in enumerate(groups):
            a=group[0]['char_start']
            b=(groups[j+1][0]['char_start'] if j+1<len(groups) else len(scene['text']))
            caption=scene['text'][a:b].strip()
            begin=start+group[0]['start']/tempo
            end=(start+groups[j+1][0]['start']/tempo if j+1<len(groups) else start+duration/tempo)
            end=min(end,scene['end']-.17)
            if end>begin:captions.append(dict(start=begin,end=end,text=caption))
        report.append(dict(scene=i,start=start,raw_duration=duration,tempo=tempo,end=start+duration/tempo))
    args=[FF,'-y']
    for path,_ in tracks:args+=['-i',path]
    filters=[]
    for i,(_,start) in enumerate(tracks):
        filters.append(f'[{i}:a]adelay={round(start*1000)}:all=1[a{i}]')
    filters.append(''.join(f'[a{i}]' for i in range(len(tracks)))+f'amix=inputs={len(tracks)}:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,apad,atrim=0:60[out]')
    command(args+['-filter_complex',';'.join(filters),'-map','[out]','-ar','48000','-ac','2',directory/'assets/narracao.wav'])
    (directory/'captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'audio-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    def tc(t):
        ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
    (directory/'legendas.srt').write_text('\n\n'.join(f'{i+1}\n{tc(c["start"])} --> {tc(c["end"])}\n{c["text"]}' for i,c in enumerate(captions)),encoding='utf-8')
    return captions


def build():
    validate_data()
    gsap=(ROOT/'episodio-1/gsap.min.js').read_bytes()
    (ROOT/'renders').mkdir(exist_ok=True)
    for ep in SCRIPT:
        n=ep['episode'];folder=ROOT/f'episodio-{n}'
        assets=folder/'assets';assets.mkdir(parents=True,exist_ok=True)
        scenes=folder/'compositions';scenes.mkdir(exist_ok=True)
        (assets/'gsap.min.js').write_bytes(gsap)
        for font in ['segoeui.ttf','segoeuib.ttf']:
            shutil.copyfile(Path('C:/Windows/Fonts')/font,assets/font)
        shutil.copyfile(ROOT.parent/'aviso_queimadas_gov.png',assets/'aviso.png')
        (assets/'overview.svg').write_text(svg_map(highlight=True),encoding='utf-8')
        (assets/'region.svg').write_text(svg_map(region=True),encoding='utf-8')
        if n==2:
            for state in DATA['historico']:
                if state['ano']>=2020:
                    (assets/f'h-{state["ano"]}-{state["mes"]}.svg').write_text(svg_map(state=state),encoding='utf-8')
        if n==3:
            for date in PEAKS:
                day=next(d for d in DATA['dias'] if d['dia_utc']==date)
                (assets/f'd-{date}.svg').write_text(svg_map(region=True,day=day),encoding='utf-8')
        captions=speech(ep,folder)
        hosts=[]
        board=[]
        for i,scene in enumerate(ep['scenes']):
            id=f'e{n}-s{i}';dur=scene['end']-scene['start']
            inner=scene_content(n,i)
            scene_html=f'''<!doctype html><html lang="pt-BR"><body><template>
<div id="{id}" data-composition-id="{id}" data-width="1920" data-height="1080"><div class="stage"><div class="inside">{inner}</div></div></div>
<script>
(()=>{{const el=document.getElementById('{id}');const tl=gsap.timeline({{paused:true}});
tl.fromTo(el.querySelector('.inside'),{{opacity:0,y:18}},{{opacity:1,y:0,duration:.45,ease:'power2.out'}},0);
el.querySelectorAll('.history-state').forEach(item=>{{const a=Number(item.dataset.at),b=Number(item.dataset.until);tl.fromTo(item,{{opacity:0}},{{opacity:1,duration:.08,immediateRender:false}},a);tl.to(item,{{opacity:0,duration:.06}},b-.06);}});
el.querySelectorAll('.barfill').forEach((item,k)=>tl.fromTo(item,{{scaleX:0}},{{scaleX:Number(item.dataset.ratio),duration:1.1,ease:'power2.out'}},.5+k*.3));
window.__timelines['{id}']=tl;}})();
</script></template></body></html>'''
            (scenes/f'{id}.html').write_text(scene_html,encoding='utf-8')
            hosts.append(f'<div id="{id}" class="clip" data-composition-id="{id}" data-composition-src="compositions/{id}.html" data-start="{scene["start"]}" data-duration="{dur}" data-track-index="0" data-width="1920" data-height="1080" style="position:absolute;inset:0"></div>')
            board.append(f'## Frame {i+1} — Cena {i+1} ({scene["start"]}–{scene["end"]}s)\n\n- status: built\n- src: compositions/{id}.html\n- duration: {dur}s\n- motion: stat-bars-and-fills / deterministic opacity entrance\n\n{scene["text"]}\n')
        caps=''.join(f'<div id="caption-{i}" class="caption clip" data-start="{c["start"]:.5f}" data-duration="{c["end"]-c["start"]:.5f}" data-track-index="3"><p>{esc(c["text"])}</p></div>' for i,c in enumerate(captions))
        stage_titles={1:'O AVISO',2:'O CONTEXTO',3:'OS PICOS NO XINGU',4:'COMPARAÇÃO E RESPONSABILIDADE'}
        foot='INPE · AQUA_M-T · Limites IBGE 2024'
        cut='Setembro e 1–26/10/2026 · UTC' if n in (3,4) else ('2020–2026 · Outubro/2026 até dia 26' if n==2 else 'Aviso recebido em 11/10/2026')
        page=f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>Fogo no Xingu — Parte {n}</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body>
<div id="root" data-composition-id="main" data-start="0" data-width="1920" data-height="1080" data-duration="60" data-fps="30">
<div class="brand">pulso<span class="accent">.</span></div><div class="series">FOGO NO XINGU</div><div class="episode">{n}/4 · {stage_titles[n]}</div><div class="rule"></div>
{''.join(hosts)}{caps}<div class="foot">{foot}</div><div class="cut">{cut}</div><div class="progress"></div>
<audio id="narracao" src="assets/narracao.wav" data-start="0" data-duration="60" data-track-index="2" data-volume="1"></audio>
</div><script>const tl=gsap.timeline({{paused:true}});tl.fromTo('.progress',{{scaleX:0}},{{scaleX:1,duration:60,ease:'none'}},0);window.__timelines['main']=tl;</script></body></html>'''
        (folder/'index.html').write_text(page,encoding='utf-8')
        (folder/'STORYBOARD.md').write_text(f'---\nformat: 1920x1080\nduration: 60s\nmessage: {ep["title"]}\n---\n\n'+'\n'.join(board),encoding='utf-8')
        spoken_scenes=[p for s in ep['scenes'] for p in s.get('phrases',[s])]
        (folder/'SCRIPT.md').write_text('\n\n'.join(f'[{s["start"]:02}–{s["end"]:02}s] {s["text"]}' for s in spoken_scenes),encoding='utf-8')
        config=dict(paths=dict(blocks='compositions',components='compositions/components',assets='assets'),authoringSkill='general-video',media=dict(autoProxy=False))
        (folder/'hyperframes.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
        (folder/'package.json').write_text(json.dumps(dict(name=f'pulso-xingu-episodio-{n}',private=True,scripts=dict(check='hyperframes check',render=f'hyperframes render --fps 30 --quality delivery --output ../renders/0{n}.mp4')),indent=2),encoding='utf-8')
        print(f'Built episode {n}: {len(ep["scenes"])} scenes, {len(captions)} captions.',flush=True)


if __name__=='__main__':build()
