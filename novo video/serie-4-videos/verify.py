"""Inspect actual MP4s, decode them fully, and preserve final-frame evidence."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
FF=ROOT/'tools/ffmpeg.exe'
PROBE=ROOT/'tools/ffprobe.exe'
OUTPUT=ROOT/'renders'
NAMES=['01-o-aviso','02-o-contexto','03-os-picos-no-xingu','04-comparacao-e-responsabilidade']
TIMES=[[3,14,26,41,55],[4,10,20,28,36,48,56],[4,11,18,23,28,33,38,43,49,57],[3,13,27,42,55]]


def main():
    evidence=OUTPUT/'verificacao'
    evidence.mkdir(exist_ok=True)
    results=[]
    for i,name in enumerate(NAMES,1):
        video=OUTPUT/f'{name}.mp4'
        probe=json.loads(subprocess.check_output([str(PROBE),'-v','error','-show_format','-show_streams','-of','json',str(video)]))
        vs=next(s for s in probe['streams'] if s['codec_type']=='video')
        au=next(s for s in probe['streams'] if s['codec_type']=='audio')
        assert vs['codec_name']=='h264'
        assert au['codec_name']=='aac'
        assert vs['width']==1920 and vs['height']==1080
        assert vs['pix_fmt']=='yuv420p'
        assert abs(float(probe['format']['duration'])-60)<.1
        assert int(vs['nb_frames'])==1800
        decode=subprocess.run([str(FF),'-v','error','-i',str(video),'-map','0','-f','null','-'],capture_output=True,text=True)
        assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
        sound=subprocess.run([str(FF),'-hide_banner','-i',str(video),'-vn','-af','volumedetect','-f','null','-'],capture_output=True,text=True)
        mean=re.search(r'mean_volume: ([-\d.]+) dB',sound.stderr)
        peak=re.search(r'max_volume: ([-\d.]+) dB',sound.stderr)
        assert mean and peak and -35<float(mean[1])<-8 and float(peak[1])<0
        folder=evidence/f'episodio-{i}';folder.mkdir(exist_ok=True)
        tiles=[]
        for t in TIMES[i-1]:
            path=folder/f'frame-{t:02}s.jpg'
            subprocess.run([str(FF),'-v','error','-y','-ss',str(t),'-i',str(video),'-frames:v','1','-q:v','2',str(path)],check=True)
            image=Image.open(path).convert('RGB');image.thumbnail((640,360))
            tile=Image.new('RGB',(640,396),'#10282d');tile.paste(image,(0,36))
            draw=ImageDraw.Draw(tile)
            draw.text((12,6),f'Parte {i} | {t:02}s',fill='#f5f1e8',font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',20))
            tiles.append(tile)
        rows=(len(tiles)+2)//3
        sheet=Image.new('RGB',(1920,396*rows),'#10282d')
        for j,tile in enumerate(tiles):sheet.paste(tile,((j%3)*640,(j//3)*396))
        sheet.save(evidence/f'episodio-{i}-quadros.jpg',quality=90)
        result=dict(file=video.name,bytes=video.stat().st_size,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),duration=float(probe['format']['duration']),width=vs['width'],height=vs['height'],fps=vs['avg_frame_rate'],frames=vs['nb_frames'],video_codec=vs['codec_name'],audio_codec=au['codec_name'],mean_volume_db=float(mean[1]),peak_db=float(peak[1]),full_decode_ok=True)
        results.append(result)
        print(json.dumps(result),flush=True)
    (OUTPUT/'verificacao.json').write_text(json.dumps(dict(ok=True,voice='Microsoft Maria Desktop, pt-BR, offline',data_snapshot='xingu-74d0fdff5980abae3d40',videos=results),ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':main()
