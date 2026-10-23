"""Caption Studio — desktop app.

Pick an audio file, click Create Video, get a styled kinetic-typography
caption video (Urdu transcription with word timings -> layered Roman +
Nastaliq captions that build word by word).

Run:  python app.py     (or double-click run.bat / run.sh)
"""
import json, os, queue, shutil, subprocess, sys, threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

BACKGROUNDS = {
    'Preset default': 'PRESET',
    'Classic maroon': '#290f05',
    'Black red': '#1c0303',
    'Espresso brown': '#201004',
    'Custom image...': 'IMAGE',
}
from make_plan import FORMATS
MODELS = {'Large (accurate)': 'large-v3-turbo', 'Small (fast)': 'small'}


class App:
    def __init__(self, root):
        self.root = root
        self.q = queue.Queue()
        root.title('Caption Studio v3')
        root.geometry('640x640')
        self.custom_bg = None

        frm = ttk.Frame(root, padding=14)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text='Audio or video file').grid(row=0, column=0, sticky='w')
        self.audio = tk.StringVar()
        ttk.Entry(frm, textvariable=self.audio, width=52).grid(row=1, column=0, sticky='we')
        ttk.Button(frm, text='Browse...', command=self.pick_audio).grid(row=1, column=1, padx=6)

        ttk.Label(frm, text='Watermark / your handle (optional)').grid(row=2, column=0, sticky='w', pady=(10, 0))
        self.brand = tk.StringVar()
        ttk.Entry(frm, textvariable=self.brand, width=52).grid(row=3, column=0, sticky='we')

        ttk.Label(frm, text='Background').grid(row=4, column=0, sticky='w', pady=(10, 0))
        self.bg = tk.StringVar(value='Preset default')
        cb = ttk.Combobox(frm, textvariable=self.bg, values=list(BACKGROUNDS), state='readonly', width=30)
        cb.grid(row=5, column=0, sticky='w')
        cb.bind('<<ComboboxSelected>>', self.on_bg)

        ttk.Label(frm, text='Format').grid(row=6, column=0, sticky='w', pady=(10, 0))
        self.fmt = tk.StringVar(value='16:9  (1280x720)')
        ttk.Combobox(frm, textvariable=self.fmt, values=list(FORMATS), state='readonly', width=30).grid(row=7, column=0, sticky='w')

        ttk.Label(frm, text='Speech model').grid(row=8, column=0, sticky='w', pady=(10, 0))
        self.model = tk.StringVar(value='Large (accurate)')
        ttk.Combobox(frm, textvariable=self.model, values=list(MODELS), state='readonly', width=30).grid(row=9, column=0, sticky='w')
        ttk.Label(frm, text='The Large model is built into this package - no download needed. (Small downloads once, ~0.5 GB.)',
                  foreground='#666').grid(row=10, column=0, sticky='w')

        from presets import PRESETS, DEFAULT_PRESET
        ttk.Label(frm, text='Style preset').grid(row=11, column=0, sticky='w', pady=(10, 0))
        self.preset = tk.StringVar(value=DEFAULT_PRESET)
        pcb = ttk.Combobox(frm, textvariable=self.preset, values=list(PRESETS), state='readonly', width=30)
        pcb.grid(row=12, column=0, sticky='w')
        pcb.bind('<<ComboboxSelected>>', self.on_preset)
        self.preset_desc = ttk.Label(frm, text=PRESETS[DEFAULT_PRESET]['desc'], foreground='#666', wraplength=430)
        self.preset_desc.grid(row=12, column=1, sticky='w', padx=6)

        self.btn = ttk.Button(frm, text='Create Video', command=self.start)
        self.btn.grid(row=13, column=0, sticky='w', pady=14)
        self.open_btn = ttk.Button(frm, text='Open output folder', command=self.open_out, state='disabled')
        self.open_btn.grid(row=13, column=1, pady=14)
        self.out_dir = None

        self.log = tk.Text(frm, height=13, width=74, state='disabled')
        self.log.grid(row=14, column=0, columnspan=2, sticky='we')
        frm.columnconfigure(0, weight=1)
        try:
            import render as _r
            _ok = _r.urdu_engine_ok()
        except Exception:
            _ok = False
        self.say('Caption Studio v3' + (
            ' — Urdu engine ready (built-in HarfBuzz).'
            if _ok else
            ' — Urdu engine NOT installed: run install.bat once, then reopen this app.'))
        self.poll()

    # ---------- UI helpers ----------
    def say(self, msg):
        self.q.put(msg)

    def poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                if msg == '__ENABLE_BTN__':
                    self.btn.configure(state='normal')
                    continue
                if msg == '__ENABLE_OPEN__':
                    self.open_btn.configure(state='normal')
                    continue
                self.log.configure(state='normal')
                self.log.insert('end', msg + '\n')
                self.log.see('end')
                self.log.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(150, self.poll)

    def pick_audio(self):
        p = filedialog.askopenfilename(filetypes=[('Audio/Video', '*.mp3 *.wav *.m4a *.mp4 *.mov *.mkv'), ('All files', '*.*')])
        if p:
            self.audio.set(p)

    def on_preset(self, _=None):
        from presets import PRESETS
        self.preset_desc.configure(text=PRESETS[self.preset.get()]['desc'])

    def on_bg(self, _=None):
        if BACKGROUNDS[self.bg.get()] == 'IMAGE':
            p = filedialog.askopenfilename(filetypes=[('Images', '*.jpg *.jpeg *.png *.webp')])
            self.custom_bg = p or None
            if not p:
                self.bg.set('Preset default')

    def open_out(self):
        if not self.out_dir:
            return
        if sys.platform.startswith('win'):
            os.startfile(self.out_dir)
        elif sys.platform == 'darwin':
            subprocess.run(['open', self.out_dir])
        else:
            subprocess.run(['xdg-open', self.out_dir])

    # ---------- pipeline ----------
    def start(self):
        src = self.audio.get().strip()
        if not src or not os.path.exists(src):
            messagebox.showerror('Caption Studio', 'Please choose an audio or video file first.')
            return
        if not shutil.which('ffmpeg'):
            messagebox.showerror('Caption Studio',
                                 'ffmpeg was not found on this computer.\nInstall it (see README) and try again.')
            return
        self.btn.configure(state='disabled')
        self.open_btn.configure(state='disabled')
        threading.Thread(target=self.work, args=(src,), daemon=True).start()

    def work(self, src):
        try:
            from caption_studio import to_audio_array, transcribe
            from make_plan import build
            from render import Renderer

            stem = os.path.splitext(os.path.basename(src))[0]
            out_dir = os.path.join(os.path.dirname(src), stem + '-caption')
            os.makedirs(out_dir, exist_ok=True)
            self.out_dir = out_dir

            dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                                 'format=duration', '-of', 'csv=p=0', src]))
            model = MODELS[self.model.get()]
            import render as _r
            if not _r.urdu_engine_ok():
                self.say('ERROR: The Urdu text engine is not installed (missing uharfbuzz / freetype-py).')
                self.say('FIX: Close this app, run install.bat once, then open the app again.')
                return
            self.say('Text engine: built-in HarfBuzz (Urdu shaping OK)')
            self.say(f'[1/3] Transcribing ({model})...')
            tr = transcribe(to_audio_array(src), model)
            json.dump(tr, open(os.path.join(out_dir, 'transcript.json'), 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=1)
            for s in tr['segments']:
                self.say(f"  [{s['start']:6.2f}-{s['end']:6.2f}] {s['text']}")

            self.say(f'[2/3] Building caption plan (preset: {self.preset.get()})...')
            plan = build(tr, brand=self.brand.get().strip(), duration=dur,
                         preset=self.preset.get())
            w, h = FORMATS[self.fmt.get()]
            plan['width'], plan['height'] = w, h
            bgv = BACKGROUNDS[self.bg.get()]
            if bgv == 'IMAGE' and self.custom_bg:
                plan['background'] = self.custom_bg
            elif bgv not in ('IMAGE', 'PRESET'):
                plan['background'] = bgv
            ppath = os.path.join(out_dir, 'plan.json')
            json.dump(plan, open(ppath, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            self.say(f"  {len(plan['phrases'])} phrases -> plan.json")

            self.say('[3/3] Rendering video...')
            r = Renderer(plan)
            fps = plan.get('fps', 30)
            n = int(plan['duration'] * fps) + 1
            out = os.path.join(out_dir, stem + '-caption-video.mp4')
            cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                   '-s', f'{r.W}x{r.H}', '-r', str(fps), '-i', '-', '-i', src,
                   '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast',
                   '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                   '-shortest', out]
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            for i in range(n):
                p.stdin.write(r.frame_at(i / fps).tobytes())
                if i % 300 == 0:
                    self.say(f'  frame {i}/{n}')
            p.stdin.close()
            rc = p.wait()
            if rc == 0:
                self.say(f'DONE -> {out}')
                self.say('Tip: to fix any word, edit plan.json and re-render with:')
                self.say(f'  python render.py plan.json "{src}" "{out}"')
                self.q.put('__ENABLE_OPEN__')
            else:
                self.say('Rendering failed (ffmpeg error).')
        except Exception as e:  # surface, never crash silently
            self.say(f'ERROR: {e}')
        finally:
            self.q.put('__ENABLE_BTN__')


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
