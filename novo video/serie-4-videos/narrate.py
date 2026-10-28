"""Generate Portuguese speech and retain word timing for the approved storyboard."""
import asyncio
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'python-vendor'))
import edge_tts


def script():
    text = (ROOT.parent / 'STORYBOARD-4-VIDEOS.md').read_text(encoding='utf-8')
    episodes = []
    for n, part in enumerate(re.split(r'## Vídeo \d — ', text)[1:], 1):
        scenes = []
        for row in part.split('\n## ', 1)[0].splitlines():
            if not re.match(r'\| \d\d–\d\ds', row):
                continue
            cells = row.split('|')
            start, end = map(int, re.search(r'(\d+)–(\d+)s', cells[1]).groups())
            spoken = cells[-2].strip().strip('“”')
            scenes.append(dict(start=start, end=end, text=spoken))
        episodes.append(dict(episode=n, title=part.splitlines()[0], scenes=scenes))
    return episodes


async def main():
    episodes = script()
    (ROOT / 'script.json').write_text(json.dumps(episodes, ensure_ascii=False, indent=2), encoding='utf-8')
    target = ROOT / 'speech'
    target.mkdir(exist_ok=True)
    sem = asyncio.Semaphore(3)

    async def line(ep, i, scene):
        stem = target / f'e{ep}-{i:02}'
        if stem.with_suffix('.json').exists() and stem.with_suffix('.mp3').exists():
            return
        async with sem:
            for attempt in range(3):
                try:
                    voice = edge_tts.Communicate(scene['text'], 'pt-BR-FranciscaNeural', rate='+0%', boundary='WordBoundary')
                    words = []
                    with stem.with_suffix('.mp3').open('wb') as out:
                        async for packet in voice.stream():
                            if packet['type'] == 'audio':
                                out.write(packet['data'])
                            elif packet['type'] == 'WordBoundary':
                                words.append(dict(text=packet['text'], start=packet['offset']/1e7, duration=packet['duration']/1e7))
                    if not words or stem.with_suffix('.mp3').stat().st_size < 1000:
                        raise RuntimeError('Empty speech')
                    stem.with_suffix('.json').write_text(json.dumps(words, ensure_ascii=False), encoding='utf-8')
                    print(f'VOICE e{ep}-{i:02}: {len(words)} words', flush=True)
                    return
                except Exception as error:
                    if attempt == 2:
                        raise
                    print(f'Retry e{ep}-{i:02}: {type(error).__name__}', flush=True)

    await asyncio.gather(*(line(ep['episode'], i, scene) for ep in episodes for i, scene in enumerate(ep['scenes'])))


if __name__ == '__main__':
    asyncio.run(main())
