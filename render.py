"""Caption Studio renderer v1.

Reads a plan JSON (phrases of timed Urdu+Roman words) and renders a video in
the reference kinetic-typography style: layered Roman caps + Nastaliq
overlays that build word by word, fades, particles, watermark.

Usage: python3 render.py plan.json audio.wav out.mp4
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

_HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(_HERE, 'fonts')


def _pick(bundled, system):
    p = os.path.join(FONTS, bundled)
    return p if os.path.exists(p) else system


ANTON = _pick('Anton-Regular.ttf', 'Anton-Regular.ttf')
NAST = _pick('NotoNastaliqUrdu-Regular.ttf',
             '/usr/share/fonts/truetype/noto/NotoNastaliqUrdu-Regular.ttf')
NAST_B = _pick('NotoNastaliqUrdu-Bold.ttf',
               '/usr/share/fonts/truetype/noto/NotoNastaliqUrdu-Bold.ttf')
SANS_B = _pick('NotoSans-Bold.ttf',
               '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf')

MAROON = (101, 19, 17)        # #651311 roman base (ref 1)
BRIGHT_RED = (196, 16, 12)    # nastaliq overlay (ref 2)
GOLD_HI = (240, 192, 112)     # #F0C070
GOLD_LO = (146, 106, 58)
WHITE = (244, 240, 239)
FADE = 0.30                   # phrase fade in/out seconds
WORD_POP = 0.16               # per-word appear time


try:
    from PIL import features as _features
    HAS_RAQM = bool(_features.check('raqm'))
except Exception:
    HAS_RAQM = False


def font(path, size):
    return ImageFont.truetype(
        path, size,
        layout_engine=ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC)


_HB = None          # (uharfbuzz, freetype) modules, or False when unavailable
_FT_FACES = {}      # (font_path, size) -> freetype Face
_HB_FONTS = {}      # font_path -> (hb Font, upem)


def _hb_mods():
    global _HB
    if _HB is None:
        try:
            import uharfbuzz
            import freetype
            _HB = (uharfbuzz, freetype)
        except Exception:
            _HB = False
    return _HB


def _hb_font(font_path):
    if font_path not in _HB_FONTS:
        hb, _ft = _hb_mods()
        blob = hb.Blob.from_file_path(font_path)
        hface = hb.Face(blob)
        hfont = hb.Font(hface)
        hfont.scale = (hface.upem, hface.upem)
        _HB_FONTS[font_path] = (hfont, hface.upem)
    return _HB_FONTS[font_path]


def hb_measure(text, font_path, size):
    """Advance width of the shaped text at `size` px, or None when the
    HarfBuzz stack is unavailable. Used for size fitting so measurements
    do not depend on Pillow's layout engine either."""
    if not _hb_mods():
        return None
    hb, _ft = _hb_mods()
    hfont, upem = _hb_font(font_path)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hfont, buf, {})
    return sum(p.x_advance for p in buf.glyph_positions) * size / upem


def hb_text_layer(text, font_path, size, fill):
    """Shape and draw Arabic/Urdu text with HarfBuzz + FreeType, with no
    dependence on Pillow's layout engine. Returns an ink-cropped RGBA
    layer like text_layer(), or None if the HB stack is unavailable."""
    mods = _hb_mods()
    if not mods:
        return None
    hb, freetype = mods
    key = (font_path, size)
    if key not in _FT_FACES:
        _FT_FACES[key] = freetype.Face(font_path)
    hfont, upem = _hb_font(font_path)
    face = _FT_FACES[key]
    face.set_char_size(size * 64)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hfont, buf, {})
    sc = size / upem
    pen = 0.0
    rects = []
    minx = miny = None
    maxx = maxy = 0.0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        face.load_glyph(info.codepoint)
        g = face.glyph
        bmp = g.bitmap
        data = None
        if bmp.width and bmp.rows:
            # copy the bytes immediately: the face's glyph slot (and its
            # bitmap buffer) is reused by the next load_glyph call
            rows = []
            for r in range(bmp.rows):
                s = r * abs(bmp.pitch)
                rows.append(bytes(bmp.buffer[s:s + bmp.width]))
            data = b''.join(rows)
        x0 = pen + pos.x_offset * sc + g.bitmap_left
        y0 = -pos.y_offset * sc - g.bitmap_top
        rects.append((bmp.width, bmp.rows, data, x0, y0))
        if data:
            minx = x0 if minx is None else min(minx, x0)
            miny = y0 if miny is None else min(miny, y0)
            maxx = max(maxx, x0 + bmp.width)
            maxy = max(maxy, y0 + bmp.rows)
        pen += pos.x_advance * sc
    if minx is None:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    from PIL import ImageChops
    W = int(math.ceil(maxx - minx)) + 8
    H = int(math.ceil(maxy - miny)) + 8
    mask = Image.new('L', (W, H), 0)
    for w, h, data, x0, y0 in rects:
        if not data:
            continue
        gim = Image.frombytes('L', (w, h), data)
        gx, gy = int(round(x0 - minx)) + 4, int(round(y0 - miny)) + 4
        region = mask.crop((gx, gy, gx + w, gy + h))
        mask.paste(ImageChops.lighter(region, gim), (gx, gy))
    layer = Image.new('RGBA', (W, H), fill + (255,))
    layer.putalpha(mask)
    return layer


def urdu_engine_ok():
    """The app shapes Urdu itself with HarfBuzz (uharfbuzz + freetype-py).
    If those packages are missing there is no reliable fallback, so callers
    check this first and stop with instructions instead of rendering a
    video with broken Urdu."""
    return bool(_hb_mods())


def text_layer(text, fnt, fill, src=None):
    """Render text to a tightly cropped RGBA layer (ink box). `src` is the
    (font_path, size) the font was made from; Arabic text is ALWAYS shaped
    with the built-in HarfBuzz engine, never left to Pillow's layout
    engine (whose optional raqm component is missing or broken on many
    Windows installs, which drew the letters isolated and out of order)."""
    if (src and text and any('\u0590' <= c <= '\u08ff' for c in text)):
        layer = hb_text_layer(text, src[0], src[1], fill)
        if layer is not None:
            return layer
    tmp = Image.new('RGBA', (10, 10))
    d = ImageDraw.Draw(tmp)
    box = d.textbbox((0, 0), text, font=fnt)
    w, h = box[2] - box[0] + 8, box[3] - box[1] + 8
    im = Image.new('RGBA', (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((4 - box[0], 4 - box[1]), text, font=fnt, fill=fill + (255,))
    return im


def gold_gradient(layer, top=None, bot=None):
    """Recolor a white text layer with a vertical gold gradient via its alpha."""
    top = top or GOLD_HI
    bot = bot or GOLD_LO
    w, h = layer.size
    grad = Image.new('L', (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        grad.putpixel((0, y), 255)
    grad = grad.resize((w, h))
    color = Image.new('RGBA', (w, h))
    px = color.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,)
        for x in range(w):
            px[x, y] = c
    color.putalpha(layer.split()[3])
    return color


def fit_size(text, fnt_path, target_w, start_size):
    arabic = any('\u0590' <= c <= '\u08ff' for c in text)
    s = start_size
    while s > 20:
        w = hb_measure(text, fnt_path, s) if arabic else None
        if w is None:
            f = font(fnt_path, s)
            tmp = ImageDraw.Draw(Image.new('RGBA', (10, 10)))
            w = tmp.textlength(text, font=f)
        if w <= target_w:
            return s
        s -= 6
    return s


def alpha_scale(layer, a):
    if a >= 0.999:
        return layer
    out = layer.copy()
    al = out.split()[3].point(lambda v: int(v * max(a, 0.0)))
    out.putalpha(al)
    return out


def paste_c(base, layer, cx, cy):
    base.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def _rgb(c):
    if isinstance(c, (list, tuple)):
        return tuple(c[:3])
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


class Renderer:
    def __init__(self, plan):
        self.p = plan
        self.W = plan.get('width', 1280)
        self.H = plan.get('height', 720)
        th = {'base': MAROON, 'on_base_overlay': GOLD_HI,
              'on_gold_overlay': BRIGHT_RED, 'gold_hi': GOLD_HI, 'gold_lo': GOLD_LO,
              'line_ur': GOLD_HI, 'line_ro': MAROON, 'only': GOLD_HI}
        for k, v in (plan.get('theme') or {}).items():
            if k in th:
                th[k] = _rgb(v)
        self.theme = th
        bgc = plan.get('background', '#290f05')
        if bgc.startswith('#'):
            rgb = tuple(int(bgc[i:i + 2], 16) for i in (1, 3, 5))
            self.bg = Image.new('RGBA', (self.W, self.H), rgb + (255,))
        else:
            im = Image.open(bgc).convert('RGB')
            sc = max(self.W / im.width, self.H / im.height)
            im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
            x, y = (im.width - self.W) // 2, (im.height - self.H) // 2
            self.bg = im.crop((x, y, x + self.W, y + self.H)).convert('RGBA')
            dark = Image.new('RGBA', (self.W, self.H), (10, 2, 0, 110))
            self.bg.alpha_composite(dark)
        self.brand = plan.get('brand', '')
        random.seed(42)
        self.particles = [(random.uniform(0, self.W), random.uniform(0, self.H),
                           random.uniform(0.4, 1.4), random.uniform(6, 20)) for _ in range(46)]
        self._prep_phrases()

    # ---------- layout prep ----------
    def _prep_phrases(self):
        for ph in self.p['phrases']:
            mode = ph['mode']
            words = ph['words']
            if mode in ('stack_red', 'stack_gold'):
                longest = max((w['ro'] for w in words), key=len)
                tw = int(self.W * (0.82 if self.H > self.W else 0.66))
                size = fit_size(longest, ANTON, tw, 190 if len(words) <= 3 else 150)
                if len(words) > 1:
                    cap = int((self.H * 0.84) / (1 + 1.04 * (len(words) - 1)))
                    size = min(size, cap)
                ph['_size'] = size
                ph['_step'] = int(size * 1.04)
                nf = font(NAST, int(size * 0.55))
                ph['_nf'] = nf
            elif mode == 'giant':
                longest = max((w['ro'] for w in words), key=len)
                size = fit_size(longest, ANTON, int(self.W * 0.86), 430)
                ph['_size'] = size
                ph['_nf'] = font(NAST, int(size * 0.42))
            elif mode == 'line_pair':
                ur = ' '.join(w['ur'] for w in words)
                ro = ' '.join(w['ro'] for w in words)
                usz = fit_size(ur, NAST_B, int(self.W * 0.92), 96)
                ph['_uf'] = font(NAST_B, usz)
                ph['_u_src'] = (NAST_B, usz)
                ph['_rf'] = font(ANTON, fit_size(ro, ANTON, int(self.W * 0.92), 58))
            elif mode == 'urdu_only':
                ur = ' '.join(w['ur'] for w in words)
                usz = fit_size(ur, NAST_B, int(self.W * 0.92), 118)
                ph['_uf'] = font(NAST_B, usz)
                ph['_u_src'] = (NAST_B, usz)
            elif mode == 'plain':
                size = max(30, int(46 * self.W / 1280))
                ph['_f'] = font(SANS_B, size)
                ph['_wrap'] = max(14, int(self.W * 0.86 / (0.70 * size)))
                ph['_step'] = int(size * 1.39)

    # ---------- per-phrase drawing ----------
    def _phrase_alpha(self, ph, t):
        a_in = min(1.0, (t - ph['start']) / FADE) if t >= ph['start'] else 0.0
        a_out = min(1.0, (ph['end'] - t) / FADE) if t <= ph['end'] else 0.0
        return max(0.0, min(a_in, a_out))

    def _word_alpha(self, w, t, extra=0.0):
        st = w['start'] + extra
        if t < st:
            return 0.0
        return min(1.0, (t - st) / WORD_POP)

    def draw_phrase(self, frame, ph, t):
        a = self._phrase_alpha(ph, t)
        if a <= 0:
            return
        mode, words = ph['mode'], ph['words']
        cx = self.W // 2
        if mode in ('stack_red', 'stack_gold', 'giant'):
            self._draw_stack(frame, ph, t, a, giant=(mode == 'giant'))
        elif mode == 'line_pair':
            ur = ' '.join(w['ur'] for w in words)
            ro = ' '.join(w['ro'] for w in words)
            portrait = self.H > self.W
            ul = text_layer(ur, ph['_uf'], self.theme['line_ur'], src=ph.get('_u_src'))
            paste_c(frame, alpha_scale(ul, a), cx, int(self.H * (0.42 if portrait else 0.40)))
            rl = text_layer(ro, ph['_rf'], WHITE if ph.get('invert') else self.theme['line_ro'])
            paste_c(frame, alpha_scale(rl, a), cx, int(self.H * (0.575 if portrait else 0.66)))
        elif mode == 'urdu_only':
            ur = ' '.join(w['ur'] for w in words)
            ul = text_layer(ur, ph['_uf'], self.theme['only'], src=ph.get('_u_src'))
            paste_c(frame, alpha_scale(ul, a), cx, int(self.H * (0.48 if self.H > self.W else 0.46)))
        elif mode == 'plain':
            ro = ' '.join(w['ro'] for w in words)
            wrap = ph.get('_wrap', 34)
            lines, cur = [], ''
            for wd in ro.split():
                if len(cur) + len(wd) + 1 <= wrap:
                    cur = (cur + ' ' + wd).strip()
                else:
                    lines.append(cur); cur = wd
            if cur:
                lines.append(cur)
            y = int(self.H * 0.60)
            for ln in lines[:3]:
                lay = text_layer(ln, ph['_f'], WHITE)
                frame.alpha_composite(alpha_scale(lay, a), (int(self.W * 0.07), y))
                y += ph.get('_step', 64)

    def _draw_stack(self, frame, ph, t, a_phrase, giant=False):
        words = ph['words']
        size, nf = ph['_size'], ph['_nf']
        if giant and len(words) == 1:
            centers = [self.H // 2]
        elif giant:
            step = int(size * 1.02)
            total_h = step * (len(words) - 1) + size
            y0 = self.H // 2 - total_h // 2 + size // 2
            centers = [y0 + i * step for i in range(len(words))]
        else:
            step = ph['_step']
            total_h = step * (len(words) - 1) + size
            y0 = self.H // 2 - total_h // 2 + size // 2
            centers = [y0 + i * step for i in range(len(words))]
        gold_base = ph['mode'] == 'stack_gold' or (giant and ph.get('_gold', True))
        for i, w in enumerate(words):
            wa = self._word_alpha(w, t) * a_phrase
            if wa <= 0:
                continue
            lay = text_layer(w['ro'], font(ANTON, size), WHITE)
            if gold_base:
                lay = gold_gradient(lay, self.theme['gold_hi'], self.theme['gold_lo'])
            else:
                lay = text_layer(w['ro'], font(ANTON, size), self.theme['base'])
            paste_c(frame, alpha_scale(lay, wa), self.W // 2, centers[i])
            # nastaliq overlay, slight rotation, appears a beat later
            na = self._word_alpha(w, t, extra=0.14) * a_phrase
            if na > 0 and w.get('ur'):
                nl = text_layer(w['ur'], nf, self.theme['on_base_overlay'] if not gold_base
                                else self.theme['on_gold_overlay'],
                                src=(NAST, int(size * 0.55)))
                ang = (-3.5, 2.5, -2.0, 3.0)[i % 4]
                nl = nl.rotate(ang, expand=True, resample=Image.BICUBIC)
                paste_c(frame, alpha_scale(nl, na), self.W // 2, centers[i] - int(size * 0.06))

    # ---------- frame ----------
    def frame_at(self, t):
        frame = self.bg.copy()
        for ph in self.p['phrases']:
            if ph['start'] - 0.01 <= t <= ph['end'] + 0.01:
                self.draw_phrase(frame, ph, t)
        # particles
        d = ImageDraw.Draw(frame, 'RGBA')
        for (x, y, sp, ph_) in self.particles:
            yy = (y - t * sp * 6) % self.H
            tw = 0.5 + 0.5 * math.sin(t * 0.7 + ph_)
            d.ellipse([x, yy, x + 2.2, yy + 2.2], fill=(255, 240, 220, int(26 * tw)))
        # watermark: red bar + brand
        if self.brand:
            d.rectangle([26, 24, 30, 46], fill=(200, 30, 20, 255))
            bf = font(SANS_B, max(20, int(25 * self.W / 1280)))
            d.text((38, 22), self.brand, font=bf, fill=(244, 240, 239, 235))
        return frame.convert('RGB')


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    if not urdu_engine_ok():
        print('ERROR: Urdu text engine not installed (missing uharfbuzz / freetype-py).')
        print('Run install.bat (or: pip install -r requirements.txt), then try again.')
        sys.exit(1)
    plan = json.load(open(sys.argv[1], encoding='utf-8'))
    audio, out = sys.argv[2], sys.argv[3]
    r = Renderer(plan)
    dur = plan['duration']
    fps = plan.get('fps', 30)
    n = int(dur * fps) + 1
    cmd = ['ffmpeg', '-y', '-v', 'error',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{r.W}x{r.H}', '-r', str(fps), '-i', '-',
           '-i', audio, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(r.frame_at(i / fps).tobytes())
        if i % 300 == 0:
            print(f'frame {i}/{n}', flush=True)
    p.stdin.close()
    print('ffmpeg rc:', p.wait())


if __name__ == '__main__':
    main()
