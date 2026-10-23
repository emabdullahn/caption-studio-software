"""Caption Studio — audio in, styled caption video out.

Pipeline: extract audio -> Whisper (Urdu, word timestamps) -> phrase plan
-> kinetic-typography render in the reference style.

Usage:
  python3 caption_studio.py AUDIO_OR_VIDEO --brand yourhandle -o out.mp4
  python3 caption_studio.py AUDIO --plan-only   (stop after plan.json)
Then optionally edit the plan (fix words / Roman / modes) and re-render:
  python3 render.py plan.json audio.wav out.mp4
"""
import argparse, json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_plan import build          # noqa: E402
from render import Renderer, urdu_engine_ok  # noqa: E402

MODEL = os.environ.get('CAPTION_MODEL', 'large-v3-turbo')


def to_audio_array(src):
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', src,
                                   '-vn', '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'])
    return np.frombuffer(raw, dtype=np.float32)


def model_ref(name):
    """Prefer the model bundled inside this package (models/<name>/), so
    nothing has to be downloaded on first use. Falls back to the
    Hugging Face name (download + cache) when no bundled copy exists."""
    local = os.path.join(HERE, 'models', name)
    if os.path.isfile(os.path.join(local, 'model.bin')):
        return local
    return name


def transcribe(audio, model_name=MODEL):
    from faster_whisper import WhisperModel
    ref = model_ref(model_name)
    print(f"  speech model: {'bundled copy (no download)' if ref != model_name else 'will download once if not cached'}", flush=True)
    m = WhisperModel(ref, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(audio, language='ur', word_timestamps=True,
                           vad_filter=True, beam_size=5)
    out = {'segments': []}
    for s in segs:
        out['segments'].append({'start': s.start, 'end': s.end, 'text': s.text.strip(),
                                'words': [{'start': w.start, 'end': w.end, 'word': w.word}
                                          for w in (s.words or [])]})
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    if not urdu_engine_ok():
        print('ERROR: Urdu text engine not installed (missing uharfbuzz / freetype-py).')
        print('Run install.bat (or: pip install -r requirements.txt), then try again.')
        sys.exit(1)
    from presets import PRESETS, DEFAULT_PRESET
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--brand', default='')
    ap.add_argument('--preset', default=DEFAULT_PRESET, choices=list(PRESETS))
    ap.add_argument('--format', default='16:9',
                    choices=['16:9', '9:16', '4:5', '1:1', '4:3'])
    ap.add_argument('--background', default=None,
                    help='override preset background: #rrggbb or an image path')
    ap.add_argument('-o', '--out', default=os.path.join(HERE, 'out', 'caption-video.mp4'))
    ap.add_argument('--workdir', default=os.path.join(HERE, 'work'))
    ap.add_argument('--plan-only', action='store_true')
    ap.add_argument('--model', default=MODEL)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    _od = os.path.dirname(a.out)
    if _od:
        os.makedirs(_od, exist_ok=True)

    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                         'format=duration', '-of', 'csv=p=0', a.src]))
    print(f'[1/3] transcribing ({a.model}) ...', flush=True)
    tr = transcribe(to_audio_array(a.src), a.model)
    tpath = os.path.join(a.workdir, 'transcript.json')
    json.dump(tr, open(tpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for s in tr['segments']:
        print(f"  [{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")

    print(f'[2/3] building plan (preset: {a.preset}) ...', flush=True)
    plan = build(tr, brand=a.brand, duration=dur, preset=a.preset)
    dims = {'16:9': (1280, 720), '9:16': (1080, 1920), '4:5': (1080, 1350),
            '1:1': (1080, 1080), '4:3': (960, 720)}
    plan['width'], plan['height'] = dims[a.format]
    if a.background:
        plan['background'] = a.background
    ppath = os.path.join(a.workdir, 'plan.json')
    json.dump(plan, open(ppath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'  {len(plan["phrases"])} phrases -> {ppath}')
    if a.plan_only:
        return

    print('[3/3] rendering ...', flush=True)
    r = Renderer(plan)
    fps = plan.get('fps', 30)
    n = int(plan['duration'] * fps) + 1
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{r.W}x{r.H}', '-r', str(fps), '-i', '-', '-i', a.src,
           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
           '-shortest', a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(r.frame_at(i / fps).tobytes())
    p.stdin.close()
    print('done ->', a.out, 'rc:', p.wait())


if __name__ == '__main__':
    main()
