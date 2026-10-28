"""Confere metadados, decodificação e hashes dos MP4s Amazônia/Xingu."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

import imageio_ffmpeg

if __package__:
    from .coletar_xingu import atomic_json, sha256
else:
    from coletar_xingu import atomic_json, sha256

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'entregas/amazonia-xingu'


def verify():
    data = json.loads((ROOT / 'remotion/src/xingu-dados.json').read_text(encoding='utf-8'))
    visual_folder = 'visual-v2' if data['video'].get('versao_edicao', 1) > 1 else 'visual'
    probe = shutil.which('ffprobe')
    if not probe:
        probe = next((p for p in (ROOT / 'remotion/node_modules/@remotion').glob('compositor-*/ffprobe*')
                      if p.name in ['ffprobe', 'ffprobe.exe']), None)
    if not probe:
        raise FileNotFoundError('ffprobe não encontrado no PATH nem na instalação Remotion.')
    results = []
    duration = data['video']['duracao_segundos']
    preview_duration = data['video'].get('duracao_previa_segundos', 25)
    for name, seconds, frames in [(data['video']['arquivo_futuro'], duration, duration*30),
                                   (data['video']['arquivo_previa'], preview_duration, preview_duration*30)]:
        path = OUT / name
        metadata = json.loads(subprocess.run([str(probe), '-v', 'error', '-show_streams', '-show_format',
                                              '-of', 'json', str(path)], capture_output=True, text=True, check=True).stdout)
        video = [s for s in metadata['streams'] if s['codec_type'] == 'video']
        if len(video) != 1:
            raise ValueError(f'Número inesperado de faixas de vídeo: {name}')
        stream = video[0]
        if (stream['width'], stream['height'], stream['codec_name'], stream['pix_fmt']) != (1920, 1080, 'h264', 'yuv420p'):
            raise ValueError(f'Formato inesperado: {name}')
        numerator, denominator = map(int, stream['avg_frame_rate'].split('/'))
        if numerator / denominator != 30 or int(stream['nb_frames']) != frames or abs(float(metadata['format']['duration']) - seconds) > .05:
            raise ValueError(f'Duração/fps/frames divergentes: {name}')
        decoded = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'error', '-i', str(path), '-f', 'null', '-'],
                                 capture_output=True, text=True, check=True)
        if decoded.stderr.strip():
            raise ValueError(f'Erro de decodificação: {name}: {decoded.stderr}')
        results.append(dict(arquivo=name, bytes=path.stat().st_size, sha256=sha256(path), largura=1920, altura=1080,
                            fps=30, duracao_segundos=seconds, frames=frames, codec='h264', pixel_format='yuv420p',
                            audio=any(s['codec_type']=='audio' for s in metadata['streams']), decodificacao='ok'))
    qa = json.loads((OUT / visual_folder / 'render-qa.json').read_text(encoding='utf-8'))
    if qa['logs'] or any(m['outsideText'] for m in qa['measurements']):
        raise ValueError('Pendências no QA do navegador.')
    report = dict(verificado_utc=datetime.now(timezone.utc).isoformat(), snapshot_id=data['snapshot_id'],
                  corte_exclusivo_utc=data['corte_exclusivo_utc'], estado='aprovado',
                  quadros_revisados=qa['frames'], arquivos=results,
                  fontes_sha256={name:sha256(ROOT / 'remotion/src' / name)
                                 for name in ['xingu-video.jsx','xingu-model.cjs','xingu-dados.json']})
    atomic_json(OUT / visual_folder / 'video-qa.json', report)
    return report


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
