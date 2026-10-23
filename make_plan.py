"""Caption Studio plan builder.

Turns a faster-whisper transcript JSON (segments with word timestamps) into a
render plan: words grouped into phrases by pauses, each phrase assigned a
caption mode from the style catalog. Roman transliteration is filled from a
provided map (word_ur -> ROMAN) or left as TODO for review.

Usage: python3 make_plan.py transcript.json plan.json [brand]
"""
import json, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from transliterate import transliterate
from presets import get_preset, DEFAULT_PRESET

FORMATS = {
    '16:9  (1280x720)': (1280, 720),
    '9:16 vertical  (1080x1920)': (1080, 1920),
    '4:5 portrait  (1080x1350)': (1080, 1350),
    '1:1 square  (1080x1080)': (1080, 1080),
    '4:3  (960x720)': (960, 720),
}


def build(transcript, brand='mysticnayn', duration=None, preset=DEFAULT_PRESET):
    pr = get_preset(preset)
    rotation = pr['rotation']
    # group into phrases: segment boundary, gap > 0.55s, or 5 words max
    phrases, cur = [], []
    for seg in transcript['segments']:
        for w in seg.get('words', []):
            txt = w['word'].strip()
            if not txt:
                continue
            word = {'ur': txt, 'start': round(w['start'], 2),
                    'end': round(w['end'], 2), 'ro': transliterate(txt)}
            if cur and (word['start'] - cur[-1]['end'] > 0.55 or len(cur) >= 5):
                phrases.append(cur); cur = []
            cur.append(word)
        if cur:
            phrases.append(cur); cur = []
    out_phrases = []
    rot = 0
    for i, pw in enumerate(phrases):
        if len(pw) > pr['plain_over']:
            mode = 'plain'
        elif 1 <= len(pw) <= pr['giant_max']:
            mode = 'giant'
        else:
            mode = rotation[rot % len(rotation)]
            rot += 1
        end = pw[-1]['end'] + 0.55
        if i + 1 < len(phrases):
            end = min(end, phrases[i + 1][0]['start'] - 0.05)
        out_phrases.append({'start': round(pw[0]['start'], 2), 'end': round(end, 2),
                            'mode': mode, 'words': pw})
    if duration is None:
        duration = out_phrases[-1]['end'] + 0.6 if out_phrases else 0
    return {'width': 1280, 'height': 720, 'fps': 30, 'duration': round(duration, 2),
            'background': pr['background'], 'theme': pr['theme'],
            'brand': brand, 'phrases': out_phrases}


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    tr = json.load(open(sys.argv[1], encoding='utf-8'))
    brand = sys.argv[3] if len(sys.argv) > 3 else 'mysticnayn'
    plan = build(tr, brand=brand)
    json.dump(plan, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"{len(plan['phrases'])} phrases, duration {plan['duration']}s")
    for p in plan['phrases']:
        print(f"[{p['start']:6.2f}-{p['end']:6.2f}] {p['mode']:10s} " +
              ' '.join(w['ur'] for w in p['words']))
