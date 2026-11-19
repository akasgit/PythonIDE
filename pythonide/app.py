"""PythonIDE main window."""

import json
import os
import sys
import tempfile
import time
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

from . import errors, examples, examples_class10, themes
from .editor import CodeEditor
from .runner import ProcessRunner
from .stepper import StepRunner

APP_NAME = "PythonIDE"
HOME = os.path.expanduser("~")
SETTINGS_DIR = os.path.join(HOME, ".pythonide")
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "settings.json")
MY_EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
MAX_OUTPUT_LINES = 3000

DEFAULT_SETTINGS = {"font_size": 14, "language": "both", "geometry": "1100x700", "auto_delay": 700,
                    "theme": themes.DEFAULT}


def programs_folder():
    docs = os.path.join(HOME, "Documents")
    base = docs if os.path.isdir(docs) else HOME
    return os.path.join(base, "PythonIDE Programs")


def pick_font(candidates, fallback):
    available = set(tkfont.families())
    for name in candidates:
        if name in available:
            return name
    return fallback


class App:
    def __init__(self, root, path=None):
        self.root = root
        self.settings = self._load_settings()
        self.path = None
        self.runner = None
        self.mode = "idle"  # idle | run | step
        self.waiting_input = False
        self.had_error = False
        self.auto_job = None
        self.prev_values = {}
        self.run_started = 0.0
        self.theme = themes.get(self.settings.get("theme"))
        self._painted = []  # (widget, {option: theme colour name}) for theme changes

        root.title(APP_NAME)
        root.geometry(self.settings["geometry"])
        root.minsize(760, 480)
        root.report_callback_exception = self._report_bug
        icon = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if sys.platform == "win32" and os.path.exists(icon):
            try:
                root.iconbitmap(default=icon)
            except tk.TclError:
                pass
        if sys.platform == "win32":
            try:
                root.state("zoomed")
            except tk.TclError:
                pass

        mono = pick_font(["Consolas", "DejaVu Sans Mono", "Liberation Mono", "Courier New"], "Courier")
        self.code_font = tkfont.Font(family=mono, size=self.settings["font_size"])
        self.out_font = tkfont.Font(family=mono, size=self.settings["font_size"] - 1)
        self.ui_font = tkfont.nametofont("TkDefaultFont")
        self.ui_font.configure(size=11)
        self.bold_font = self.ui_font.copy()
        self.bold_font.configure(weight="bold")
        self.big_bold = self.ui_font.copy()
        self.big_bold.configure(size=12, weight="bold")
        nepali = pick_font(["Nirmala UI", "Mangal", "Noto Sans Devanagari", "Lohit Devanagari"],
                           self.ui_font.actual("family"))
        self.nepali_font = tkfont.Font(family=nepali, size=12)
        # Fonts for the error help and the Variables panel (bigger in Projector theme).
        self.help_font = self.ui_font.copy()
        self.help_bold = self.bold_font.copy()
        self.help_title = self.big_bold.copy()
        self.var_font = self.ui_font.copy()
        self.var_bold = self.bold_font.copy()

        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")  # the ttk theme that follows our colours everywhere
        except tk.TclError:
            pass
        self.style.configure("Treeview", font=self.var_font)
        self.style.configure("Treeview.Heading", font=self.var_bold, relief="flat")

        self.language = tk.StringVar(value=self.settings["language"])
        self.theme_name = tk.StringVar(value=self.settings.get("theme", themes.DEFAULT))
        self.auto_play = tk.BooleanVar(value=False)

        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self._bind_keys()
        self.apply_theme(self.theme_name.get(), first=True)

        if path and os.path.exists(path):
            self._open_path(path)
        else:
            self.editor.set(examples.WELCOME)
        self._update_title()
        self._set_mode("idle")
        self.status("Ready. Press Run (F5) to run your program.")
        root.protocol("WM_DELETE_WINDOW", self.quit)
        self._poll_job = root.after(40, self._poll)

    # ======================================================================
    # Building the window
    # ======================================================================

    def _build_menu(self):
        menubar = tk.Menu(self.root)
        f = self.ui_font

        m = tk.Menu(menubar, tearoff=False, font=f)
        m.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        m.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file)
        m.add_command(label="Save", accelerator="Ctrl+S", command=self.save)
        m.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as)
        m.add_separator()
        m.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=m)

        m = tk.Menu(menubar, tearoff=False, font=f)
        m.add_command(label="Undo", accelerator="Ctrl+Z", command=lambda: self._text_event("<<Undo>>"))
        m.add_command(label="Redo", accelerator="Ctrl+Y", command=lambda: self._text_event("<<Redo>>"))
        m.add_separator()
        m.add_command(label="Cut", accelerator="Ctrl+X", command=lambda: self._text_event("<<Cut>>"))
        m.add_command(label="Copy", accelerator="Ctrl+C", command=lambda: self._text_event("<<Copy>>"))
        m.add_command(label="Paste", accelerator="Ctrl+V", command=lambda: self._text_event("<<Paste>>"))
        m.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)
        m.add_separator()
        m.add_command(label="Comment / Uncomment", accelerator="Ctrl+/",
                      command=lambda: self.editor._toggle_comment())
        menubar.add_cascade(label="Edit", menu=m)

        m = tk.Menu(menubar, tearoff=False, font=f)
        m.add_command(label="Run", accelerator="F5", command=self.run)
        m.add_command(label="Stop", accelerator="Shift+F5", command=self.stop)
        m.add_separator()
        m.add_command(label="Step mode (one line at a time)", accelerator="F6", command=self.step_start)
        m.add_command(label="Next step", accelerator="F7", command=self.step_next)
        m.add_command(label="Run to the end", accelerator="F8", command=self.step_to_end)
        menubar.add_cascade(label="Run", menu=m)

        self.examples_menu = tk.Menu(menubar, tearoff=False, font=f, postcommand=self._fill_examples_menu)
        menubar.add_cascade(label="Examples", menu=self.examples_menu)

        m = tk.Menu(menubar, tearoff=False, font=f)
        m.add_command(label="Bigger text", accelerator="Ctrl++", command=lambda: self.zoom(1))
        m.add_command(label="Smaller text", accelerator="Ctrl+-", command=lambda: self.zoom(-1))
        m.add_separator()
        m.add_command(label="Theme:", state="disabled")
        for name, theme in themes.THEMES.items():
            m.add_radiobutton(label="   " + theme["label"], variable=self.theme_name, value=name,
                              command=lambda n=name: self.apply_theme(n))
        m.add_command(label="   Next theme", accelerator="F9", command=self.next_theme)
        m.add_separator()
        m.add_radiobutton(label="Error help in English", variable=self.language, value="en",
                          command=self._save_settings)
        m.add_radiobutton(label="Error help in Nepali (नेपाली)", variable=self.language, value="ne",
                          command=self._save_settings)
        m.add_radiobutton(label="Error help in both", variable=self.language, value="both",
                          command=self._save_settings)
        menubar.add_cascade(label="View", menu=m)

        m = tk.Menu(menubar, tearoff=False, font=f)
        m.add_command(label="Python cheat sheet", accelerator="F1", command=self.show_cheat_sheet)
        m.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=m)

        self.root.config(menu=menubar)

    def _fill_examples_menu(self):
        menu = self.examples_menu
        menu.delete(0, "end")
        for group, items in examples.EXAMPLES:
            sub = tk.Menu(menu, tearoff=False, font=self.ui_font)
            for title, code in items:
                sub.add_command(label=title, command=lambda t=title, c=code: self.load_example(t, c))
            menu.add_cascade(label=group, menu=sub)
        menu.add_separator()
        class10 = tk.Menu(menu, tearoff=False, font=self.ui_font)
        for group, items in examples_class10.CLASS10:
            sub = tk.Menu(class10, tearoff=False, font=self.ui_font)
            for title, code in items:
                sub.add_command(label=title, command=lambda t=title, c=code: self.load_example(t, c))
            class10.add_cascade(label=group, menu=sub)
        menu.add_cascade(label="Class 10", menu=class10)
        mine = self._my_examples()
        if mine:
            menu.add_separator()
            sub = tk.Menu(menu, tearoff=False, font=self.ui_font)
            for name, path in mine:
                sub.add_command(label=name, command=lambda p=path: self._load_my_example(p))
            menu.add_cascade(label="My examples (from teacher)", menu=sub)

    def _my_examples(self):
        if not os.path.isdir(MY_EXAMPLES_DIR):
            return []
        found = []
        for name in sorted(os.listdir(MY_EXAMPLES_DIR)):
            if name.lower().endswith(".py"):
                found.append((name[:-3].replace("_", " "), os.path.join(MY_EXAMPLES_DIR, name)))
        return found

    def _paint(self, widget, **roles):
        """Colour ``widget`` from the theme now and whenever the theme changes.

        ``roles`` maps a widget option to a theme colour name,
        e.g. ``bg="panel", fg="text"``.
        """
        self._painted.append((widget, roles))
        widget.configure(**{opt: self.theme[key] for opt, key in roles.items()})
        return widget

    def _build_toolbar(self):
        bar = self._paint(tk.Frame(self.root, padx=6, pady=5), bg="toolbar")
        bar.pack(side="top", fill="x")

        def button(text, command, colour=None):
            b = tk.Button(bar, text=text, command=command, font=self.big_bold if colour else self.ui_font,
                          padx=10, pady=3, relief="flat", bd=0, cursor="hand2")
            if colour:
                b.configure(fg="white", activeforeground="white", disabledforeground="#dddddd")
                self._paint(b, bg=colour, activebackground=colour)
            else:
                self._paint(b, bg="button", fg="text", activebackground="button_active",
                            activeforeground="text")
            b.colour = colour
            b.pack(side="left", padx=3)
            return b

        def gap():
            self._paint(tk.Frame(bar, width=12), bg="toolbar").pack(side="left")

        button("New", self.new_file)
        button("Open", self.open_file)
        button("Save", self.save)
        mb = tk.Menubutton(bar, text="Examples \u25be", font=self.ui_font, relief="flat",
                           padx=10, pady=4, cursor="hand2", menu=self.examples_menu)
        self._paint(mb, bg="button", fg="text", activebackground="button_active", activeforeground="text")
        mb.pack(side="left", padx=3)
        gap()
        self.run_btn = button("Run (F5)", self.run, "run")
        self.stop_btn = button("Stop", self.stop, "stop")
        gap()
        self.step_btn = button("Step (F6)", self.step_start, "step")
        self.next_btn = button("Next (F7)", self.step_next, "step")
        self.end_btn = button("To end", self.step_to_end, "step")
        self.auto_chk = tk.Checkbutton(bar, text="Auto", variable=self.auto_play, font=self.ui_font,
                                       command=self._auto_toggled)
        self._paint(self.auto_chk, bg="toolbar", fg="text", activebackground="toolbar",
                    activeforeground="text", selectcolor="button")
        self.auto_chk.pack(side="left", padx=(6, 0))
        self.speed = tk.Scale(bar, from_=1500, to=150, orient="horizontal", showvalue=False,
                              length=70, highlightthickness=0, bd=0, resolution=50)
        self._paint(self.speed, bg="toolbar", troughcolor="button", activebackground="button_active")
        self.speed.set(self.settings.get("auto_delay", 700))
        self.speed.pack(side="left")

        for label, delta in (("A-", -1), ("A+", 1)):
            b = button(label, lambda d=delta: self.zoom(d))
            b.configure(padx=5)
            b.pack(side="right", padx=1)

    def _build_body(self):
        P = self._paint
        outer = P(tk.PanedWindow(self.root, orient="horizontal", sashwidth=6, bd=0), bg="sash")
        outer.pack(side="top", fill="both", expand=True)

        left = P(tk.PanedWindow(outer, orient="vertical", sashwidth=6, bd=0), bg="sash")
        self.editor = CodeEditor(left, self.code_font, self.theme, on_change=self._on_code_change)
        left.add(self.editor, minsize=150, stretch="always")

        out_frame = P(tk.Frame(left), bg="out_bg")
        head = P(tk.Frame(out_frame), bg="header")
        head.pack(side="top", fill="x")
        P(tk.Label(head, text="Output", font=self.bold_font, padx=8, pady=2),
          bg="header", fg="text").pack(side="left")
        P(tk.Button(head, text="Clear", command=self.clear_output, relief="flat", cursor="hand2",
                    bd=0, highlightthickness=0, padx=8),
          bg="header", fg="text", activebackground="header_active",
          activeforeground="text").pack(side="right", padx=4)

        input_row = P(tk.Frame(out_frame, pady=4, padx=6), bg="header")
        input_row.pack(side="bottom", fill="x")
        self.input_label = P(tk.Label(input_row, text="Input:", font=self.ui_font), bg="header", fg="text")
        self.input_label.pack(side="left")
        self.input_entry = P(tk.Entry(input_row, font=self.out_font, relief="flat"),
                             fg="text", disabledbackground="entry_disabled", insertbackground="cursor")
        self.input_entry.pack(side="left", fill="x", expand=True, padx=6, ipady=3)
        self.input_entry.bind("<Return>", self._send_input)
        self.input_entry.bind("<KP_Enter>", self._send_input)
        self.send_btn = tk.Button(input_row, text="Enter", command=self._send_input, relief="flat",
                                  fg="white", padx=10, cursor="hand2")
        P(self.send_btn, bg="run", activebackground="run")
        self.send_btn.pack(side="left")

        self.output = tk.Text(out_frame, font=self.out_font, wrap="word", height=10, bd=0,
                              highlightthickness=0, padx=8, pady=4, state="disabled", cursor="arrow")
        P(self.output, bg="out_bg", fg="out_fg", selectbackground="select", insertbackground="cursor")
        out_scroll = ttk.Scrollbar(out_frame, command=self.output.yview)
        self.output.configure(yscrollcommand=out_scroll.set)
        out_scroll.pack(side="right", fill="y")
        self.output.pack(side="left", fill="both", expand=True)
        o = self.output
        o.tag_configure("typed", font=self._font_variant(self.out_font, "bold"))
        o.tag_configure("err_title", font=self.help_title, spacing1=6)
        o.tag_configure("err_text", font=self.help_font, lmargin1=12, lmargin2=12)
        o.tag_configure("err_ne", font=self.nepali_font, lmargin1=12, lmargin2=12)
        o.tag_configure("hint", font=self.help_bold, lmargin1=12, lmargin2=12, spacing1=4)
        o.tag_configure("hint_ne", font=self.nepali_font, lmargin1=12, lmargin2=12)
        o.tag_configure("tech", lmargin1=12, lmargin2=12, spacing1=4)
        # Let students select and copy from the output with the keyboard too.
        o.bind("<1>", lambda e: o.focus_set())

        left.add(out_frame, minsize=120, stretch="always")
        outer.add(left, minsize=400, stretch="always")

        right = P(tk.Frame(outer), bg="panel")
        P(tk.Label(right, text="Variables", font=self.bold_font, anchor="w", padx=8, pady=2),
          bg="header", fg="text").pack(side="top", fill="x")
        self.var_hint = tk.Label(right, text="Run or Step your program to see its variables here.",
                                 wraplength=260, justify="left", anchor="w", padx=8, pady=4)
        P(self.var_hint, bg="panel", fg="muted")
        self.var_hint.pack(side="top", fill="x")
        tree_frame = P(tk.Frame(right), bg="panel")
        tree_frame.pack(side="top", fill="both", expand=True)
        self.vars = ttk.Treeview(tree_frame, columns=("value", "type"), selectmode="browse")
        self.vars.heading("#0", text="Name", anchor="w")
        self.vars.heading("value", text="Value", anchor="w")
        self.vars.heading("type", text="Type", anchor="w")
        self.vars.column("#0", width=128, stretch=False)
        self.vars.column("value", width=90, stretch=True)
        self.vars.column("type", width=140, stretch=False)
        self.vars.tag_configure("scope", font=self.var_bold)
        vs = ttk.Scrollbar(tree_frame, orient="vertical", command=self.vars.yview)
        self.vars.configure(yscrollcommand=vs.set)
        vs.pack(side="right", fill="y")
        self.vars.pack(side="left", fill="both", expand=True)
        outer.add(right, minsize=220, width=370, stretch="never")

        self.root.update_idletasks()
        try:
            left.paneconfigure(self.editor, height=int(self.root.winfo_height() * 0.6))
        except tk.TclError:
            pass

    def _build_statusbar(self):
        self.status_var = tk.StringVar()
        bar = tk.Label(self.root, textvariable=self.status_var, anchor="w", padx=8, pady=3,
                       font=self.ui_font)
        self._paint(bar, bg="status_bg", fg="text")
        bar.pack(side="bottom", fill="x", before=self.root.pack_slaves()[0])
        self.status_bar = bar

    def _bind_keys(self):
        r = self.root
        r.bind_all("<F5>", lambda e: self.run())
        r.bind_all("<Shift-F5>", lambda e: self.stop())
        r.bind_all("<F6>", lambda e: self.step_start())
        r.bind_all("<F7>", lambda e: self.step_next())
        r.bind_all("<F8>", lambda e: self.step_to_end())
        r.bind_all("<F1>", lambda e: self.show_cheat_sheet())
        r.bind_all("<F9>", lambda e: self.next_theme())
        for key, action in (("n", self.new_file), ("o", self.open_file), ("s", self.save)):
            r.bind_all("<Control-{}>".format(key), lambda e, a=action: (a(), "break")[1])
            r.bind_all("<Control-{}>".format(key.upper()), lambda e, a=action: (a(), "break")[1])
        r.bind_all("<Control-Shift-S>", lambda e: (self.save_as(), "break")[1])
        for key in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            r.bind_all(key, lambda e: self.zoom(1))
        for key in ("<Control-minus>", "<Control-KP_Subtract>"):
            r.bind_all(key, lambda e: self.zoom(-1))
        r.bind_all("<Control-MouseWheel>", lambda e: self.zoom(1 if e.delta > 0 else -1))
        r.bind_all("<Control-Button-4>", lambda e: self.zoom(1))
        r.bind_all("<Control-Button-5>", lambda e: self.zoom(-1))
        # The text box has its own Ctrl+O / Ctrl+N bindings; ours must win.
        for key, action in (("n", self.new_file), ("o", self.open_file), ("s", self.save)):
            self.editor.text.bind("<Control-{}>".format(key), lambda e, a=action: (a(), "break")[1])
        self.editor.text.bind("<Control-y>", lambda e: (self._text_event("<<Redo>>"), "break")[1])
        self.editor.text.bind("<Control-a>", lambda e: (self._select_all(), "break")[1])

    # ======================================================================
    # Files
    # ======================================================================

    def _confirm_discard(self):
        """Ask to save changes. Returns False if the student cancels."""
        if not self.editor.is_modified():
            return True
        answer = messagebox.askyesnocancel(
            APP_NAME, "Do you want to save the changes to your program first?", parent=self.root)
        if answer is None:
            return False
        if answer:
            return self.save()
        return True

    def new_file(self):
        if self.mode != "idle":
            self.stop()
        if not self._confirm_discard():
            return
        self.path = None
        self.editor.set("")
        self.editor.clear_marks()
        self._update_title()
        self.editor.text.focus_set()

    def open_file(self):
        if not self._confirm_discard():
            return
        folder = programs_folder()
        path = filedialog.askopenfilename(
            parent=self.root, title="Open a Python program",
            initialdir=folder if os.path.isdir(folder) else HOME,
            filetypes=[("Python programs", "*.py"), ("All files", "*.*")])
        if path:
            self._open_path(path)

    def _open_path(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                source = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                source = f.read()
        except OSError as exc:
            messagebox.showerror(APP_NAME, "Could not open the file:\n{}".format(exc), parent=self.root)
            return
        if self.mode != "idle":
            self.stop()
        self.path = os.path.abspath(path)
        self.editor.set(source.replace("\r\n", "\n"))
        self._update_title()
        self.status("Opened " + os.path.basename(path))

    def save(self):
        if not self.path:
            return self.save_as()
        return self._write(self.path)

    def save_as(self):
        folder = programs_folder()
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError:
            folder = HOME
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save your program", initialdir=folder,
            initialfile=os.path.basename(self.path) if self.path else "my_program.py",
            defaultextension=".py", filetypes=[("Python programs", "*.py")])
        if not path:
            return False
        if self._write(path):
            self.path = os.path.abspath(path)
            self._update_title()
            return True
        return False

    def _write(self, path):
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.editor.get())
        except OSError as exc:
            messagebox.showerror(APP_NAME, "Could not save the file:\n{}".format(exc), parent=self.root)
            return False
        self.editor.mark_saved()
        self._update_title()
        self.status("Saved " + path)
        return True

    def load_example(self, title, code):
        if not self._confirm_discard():
            return
        if self.mode != "idle":
            self.stop()
        self.path = None
        self.editor.set(code)
        self.editor.clear_marks()
        self._update_title(title)
        self.status("Example loaded: {}. Press Run (F5) or Step (F6).".format(title))

    def _load_my_example(self, path):
        if not self._confirm_discard():
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
        except OSError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self.root)
            return
        self.load_example(os.path.basename(path)[:-3], code)
        self.editor.mark_saved()

    def _update_title(self, name=None):
        if name is None:
            name = os.path.basename(self.path) if self.path else "Untitled"
        self._title_name = name
        star = "*" if self.editor.is_modified() else ""
        self.root.title("{}{} - {}".format(star, name, APP_NAME))

    def _on_code_change(self):
        if self.mode == "idle":
            self.editor.show_line("error_line", None)
        name = getattr(self, "_title_name", None)
        self._update_title(name)

    def quit(self):
        if self.mode != "idle":
            self.stop()
        if not self._confirm_discard():
            return
        self.settings["geometry"] = self.root.geometry() if self.root.state() == "normal" else \
            self.settings["geometry"]
        self._save_settings()
        self.close()

    def close(self):
        """Stop timers and the running program, then close the window."""
        if self.runner is not None:
            self.runner.stop()
        self._cancel_auto()
        self.root.after_cancel(self._poll_job)
        self.editor.cancel_jobs()
        self.root.destroy()

    # ======================================================================
    # Running
    # ======================================================================

    def _prepare_run(self):
        if self.mode != "idle":
            self.stop()
            self._finish()
        self.clear_output()
        self.editor.clear_marks()
        self._clear_vars()
        self.had_error = False
        self.prev_values = {}
        self.run_started = time.time()

    def run(self):
        self._prepare_run()
        source = self.editor.get()
        if self.path:
            if not self._write(self.path):
                return
            path, cwd = self.path, None
        else:
            folder = os.path.join(tempfile.gettempdir(), "pythonide")
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "program.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(source)
            cwd = self._work_folder()
        self._source = source
        self.runner = ProcessRunner(path, cwd)
        try:
            self.runner.start()
        except OSError as exc:
            messagebox.showerror(APP_NAME, "Could not start Python:\n{}".format(exc), parent=self.root)
            self.runner = None
            return
        self._set_mode("run")
        self.status("Running...  Press Stop (Shift+F5) to stop it.")

    def _work_folder(self):
        """The folder a program reads and writes its files in."""
        if self.path:
            return os.path.dirname(self.path)
        folder = programs_folder()
        try:
            os.makedirs(folder, exist_ok=True)
            return folder
        except OSError:
            return HOME

    def step_start(self):
        if self.mode == "step":
            self.step_next()
            return
        self._prepare_run()
        self._source = self.editor.get()
        if "import turtle" in self._source or "from turtle" in self._source:
            messagebox.showinfo(
                APP_NAME, "Turtle drawings cannot be shown in Step mode.\nUse Run (F5) for turtle programs.",
                parent=self.root)
            return
        # Files the program opens (e.g. students.txt) are in the same folder
        # as with Run, not in PythonIDE's own folder.
        try:
            os.chdir(self._work_folder())
        except OSError:
            pass
        self.runner = StepRunner(self._source)
        self.runner.start()
        self._set_mode("step")
        self.var_hint.configure(text="Green rows changed in the last step.")
        self.status("Step mode: the yellow line runs next. Press Next step (F7).")

    def step_next(self):
        if self.mode != "step":
            if self.mode == "idle":
                self.step_start()
            return
        if self.waiting_input:
            self.input_entry.focus_set()
            return
        self.runner.next_step()

    def step_to_end(self):
        if self.mode == "step":
            self.auto_play.set(False)
            self._cancel_auto()
            self.editor.show_line("step_line", None)
            self.runner.run_to_end()

    def stop(self):
        if self.runner is not None and self.mode != "idle":
            self.runner.stop()
            self._cancel_auto()

    def _auto_toggled(self):
        self.settings["auto_delay"] = int(self.speed.get())
        if self.auto_play.get() and self.mode == "step" and not self.waiting_input:
            self._schedule_auto()
        else:
            self._cancel_auto()

    def _schedule_auto(self):
        self._cancel_auto()
        self.auto_job = self.root.after(int(self.speed.get()), self._auto_next)

    def _auto_next(self):
        self.auto_job = None
        if self.mode == "step" and self.auto_play.get() and not self.waiting_input:
            self.runner.next_step()

    def _cancel_auto(self):
        if self.auto_job is not None:
            self.root.after_cancel(self.auto_job)
            self.auto_job = None

    def _send_input(self, event=None):
        if not self.waiting_input or self.runner is None:
            return "break"
        text = self.input_entry.get()
        self.input_entry.delete(0, "end")
        self._append(text + "\n", "typed")
        self._set_waiting(False)
        self.runner.send_input(text)
        if self.mode == "step":
            self.status("Step mode: press Next step (F7).")
            if self.auto_play.get():
                self._schedule_auto()
        else:
            self.status("Running...")
        return "break"

    def _set_waiting(self, waiting):
        self.waiting_input = waiting
        if waiting:
            self.input_entry.configure(state="normal", bg=self.theme["input_wait"])
            self.input_label.configure(text="Type here and press Enter:", font=self.bold_font)
            self.send_btn.configure(state="normal")
            self.input_entry.focus_set()
            self.status("Your program is waiting for you to type something below and press Enter.")
        else:
            self.input_entry.configure(state="disabled")
            self.input_label.configure(text="Input:", font=self.ui_font)
            self.send_btn.configure(state="disabled")

    def _set_mode(self, mode):
        self.mode = mode
        idle = mode == "idle"
        self._enable(self.run_btn, True)
        self._enable(self.stop_btn, not idle)
        self._enable(self.step_btn, mode != "run")
        self._enable(self.next_btn, mode == "step")
        self._enable(self.end_btn, mode == "step")
        self.auto_chk.configure(state="normal" if mode == "step" else "disabled")
        self.editor.set_readonly(mode == "step")
        self._set_waiting(False)

    def _enable(self, button, on):
        button.enabled = on
        colour = self.theme[button.colour if on else "button_disabled"]
        button.configure(state="normal" if on else "disabled", bg=colour, activebackground=colour)

    def _poll(self):
        try:
            if self.runner is not None:
                for _ in range(300):
                    try:
                        event = self.runner.events.get_nowait()
                    except Exception:
                        break
                    self._handle(event)
                    if self.runner is None:
                        break
        finally:
            self._poll_job = self.root.after(40, self._poll)

    def _handle(self, event):
        kind = event[0]
        if kind == "out":
            self._append(event[1])
        elif kind == "err":
            self._append(event[1], "stderr")
        elif kind == "input":
            self._cancel_auto()
            self._set_waiting(True)
        elif kind == "line":
            self._show_step(event[1], event[2])
        elif kind == "error":
            self.had_error = True
            self._show_error(event[1])
        elif kind == "vars":
            self._show_final_vars(event[1])
        elif kind == "stopped":
            self._append("\nProgram stopped.\n", "info")
            self.status("Program stopped.")
            self.had_error = True
        elif kind == "exit":
            self._finish()

    def _finish(self):
        if self.runner is None:
            return
        seconds = time.time() - self.run_started
        if not self.had_error:
            self._append("\n--- Program finished ({:.1f} s) ---\n".format(seconds), "info")
            self.status("Program finished.")
        if self.mode == "step":
            self.editor.show_line("step_line", None)
        self.runner = None
        self._cancel_auto()
        self._set_mode("idle")
        if not self.had_error:
            self.editor.text.focus_set()

    def _show_step(self, lineno, scopes):
        self.editor.show_line("step_line", lineno)
        self._show_scopes(scopes)
        steps = self.runner.steps if self.runner is not None else 0
        self.status("Step {}: line {} (yellow) runs next.  Press Next step (F7).".format(steps, lineno))
        if self.auto_play.get():
            self._schedule_auto()

    # ======================================================================
    # Output, errors and variables
    # ======================================================================

    def _append(self, text, tag=None):
        o = self.output
        o.configure(state="normal")
        o.insert("end", text, tag)
        lines = int(o.index("end-1c").split(".")[0])
        if lines > MAX_OUTPUT_LINES:
            o.delete("1.0", "{}.0".format(lines - MAX_OUTPUT_LINES))
        o.configure(state="disabled")
        o.see("end")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _show_error(self, info):
        lineno = info.get("line")
        help_ = errors.explain(info, getattr(self, "_source", self.editor.get()))
        lang = self.language.get()
        where = "Error on line {}: ".format(lineno) if lineno else "Error: "
        error_start = self.output.index("end-1c")
        last_char = self.output.get("end-2c", "end-1c")
        if last_char and last_char != "\n":
            self._append("\n")
        self._append(where + help_.title + "\n", "err_title")
        if lang in ("en", "both"):
            self._append(help_.en + "\n", "err_text")
        if lang in ("ne", "both") and help_.ne:
            self._append(help_.ne + "\n", "err_ne")
        if help_.hint_en and lang in ("en", "both"):
            self._append("Tip: " + help_.hint_en + "\n", "hint")
        if help_.hint_ne and lang in ("ne", "both"):
            self._append("सुझाव: " + help_.hint_ne + "\n", "hint_ne")
        self._append("Python says: {}: {}\n".format(info.get("type"), info.get("msg")), "tech")
        self.output.see(error_start)
        if lineno:
            self.editor.show_line("step_line", None)
            self.editor.show_line("error_line", lineno)
        self.status("There is an error on line {}. Read the help in the Output box.".format(lineno)
                    if lineno else "Your program has an error.")

    def _clear_vars(self):
        self.vars.delete(*self.vars.get_children())
        self.var_hint.configure(text="Run or Step your program to see its variables here.")

    def _show_final_vars(self, rows):
        if self.mode == "step":
            self._show_scopes([("Main program (finished)", rows)])
            return
        self.vars.delete(*self.vars.get_children())
        if rows:
            self.var_hint.configure(text="Variables when the program ended:")
        else:
            self.var_hint.configure(text="Your program has no variables.")
        for name, typ, value in rows:
            self.vars.insert("", "end", text=name, values=(value, typ))

    def _show_scopes(self, scopes):
        tree = self.vars
        tree.delete(*tree.get_children())
        new_values = {}
        for title, rows in scopes:
            parent = tree.insert("", "end", text=title, open=True, tags=("scope",))
            for name, typ, value in rows:
                key = (title, name)
                new_values[key] = value
                changed = self.prev_values.get(key) != value
                tree.insert(parent, "end", text=name, values=(value, typ),
                            tags=("changed",) if changed else ())
        self.prev_values = new_values

    # ======================================================================
    # Misc
    # ======================================================================

    def next_theme(self):
        names = list(themes.THEMES)
        current = names.index(self.theme_name.get()) if self.theme_name.get() in names else 0
        self.apply_theme(names[(current + 1) % len(names)])
        return "break"

    def apply_theme(self, name, first=False):
        """Switch every colour in the window to the theme ``name``."""
        old = self.theme
        self.theme = theme = themes.get(name)
        self.theme_name.set(name if name in themes.THEMES else themes.DEFAULT)
        for widget, roles in self._painted:
            widget.configure(**{opt: theme[key] for opt, key in roles.items()})
        for b in (self.run_btn, self.stop_btn, self.step_btn, self.next_btn, self.end_btn):
            self._enable(b, getattr(b, "enabled", True))
        if not self.waiting_input:
            self.input_entry.configure(bg=theme["entry"])
        else:
            self.input_entry.configure(bg=theme["input_wait"])

        o = self.output
        for tag, key in (("stderr", "stderr"), ("typed", "typed"), ("info", "info"),
                         ("err_title", "err_title"), ("err_text", "err_text"), ("err_ne", "err_text"),
                         ("hint", "hint"), ("hint_ne", "hint"), ("tech", "tech")):
            o.tag_configure(tag, foreground=theme[key])

        st = self.style
        st.configure("Treeview", background=theme["panel"], fieldbackground=theme["panel"],
                     foreground=theme["text"], bordercolor=theme["sash"])
        st.map("Treeview", background=[("selected", theme["select"])],
               foreground=[("selected", theme["text"])])
        st.configure("Treeview.Heading", background=theme["header"], foreground=theme["text"])
        st.map("Treeview.Heading", background=[("active", theme["header_active"])])
        st.configure("TScrollbar", background=theme["button"], troughcolor=theme["panel"],
                     arrowcolor=theme["text"], bordercolor=theme["sash"])
        st.map("TScrollbar", background=[("active", theme["button_active"])])
        self.vars.tag_configure("changed", background=theme["changed"])

        # Bold, bigger code for the projector theme; back to normal afterwards.
        weight = "bold" if theme["bold_code"] else "normal"
        self.code_font.configure(weight=weight)
        self.out_font.configure(weight=weight)
        size = self.code_font.cget("size")
        if theme["min_font"] and size < theme["min_font"]:
            self.settings["font_size_before_theme"] = size
            self._set_font_size(theme["min_font"])
        elif not theme["min_font"] and old["min_font"] and not first:
            before = self.settings.pop("font_size_before_theme", None)
            if before:
                self._set_font_size(before)
        boost = theme["text_boost"]
        base = self.ui_font.cget("size")
        for font, size in ((self.help_font, base), (self.help_bold, base), (self.help_title, base + 1),
                           (self.var_font, base), (self.var_bold, base), (self.nepali_font, base + 1)):
            font.configure(size=size + boost)
        st.configure("Treeview", rowheight=int(self.var_font.metrics("linespace") * 1.5))
        self.editor.apply_theme(theme)
        self.editor.set_font(self.code_font)
        if not first:
            self.settings["theme"] = self.theme_name.get()
            self._save_settings()
            self.status("Theme: {}".format(theme["label"]))

    def status(self, text):
        self.status_var.set(text)

    def zoom(self, delta):
        self._set_font_size(self.code_font.cget("size") + delta)
        self.settings.pop("font_size_before_theme", None)
        self._save_settings()
        return "break"

    def _set_font_size(self, size):
        size = max(9, min(36, size))
        self.code_font.configure(size=size)
        self.out_font.configure(size=size - 1)
        self.editor.set_font(self.code_font)
        self.settings["font_size"] = size

    def _text_event(self, name):
        widget = self.root.focus_get()
        if not isinstance(widget, (tk.Text, tk.Entry)):
            widget = self.editor.text
        try:
            widget.event_generate(name)
        except tk.TclError:
            pass

    def _select_all(self):
        t = self.editor.text
        t.tag_add("sel", "1.0", "end-1c")
        t.mark_set("insert", "end-1c")

    @staticmethod
    def _font_variant(font, weight):
        f = font.copy()
        f.configure(weight=weight)
        return f

    def show_cheat_sheet(self):
        win = tk.Toplevel(self.root)
        win.title("Python cheat sheet")
        win.geometry("640x600")
        text = tk.Text(win, font=self.out_font, wrap="word", padx=12, pady=10, bd=0)
        scroll = tk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True)
        text.configure(bg=self.theme["bg"], fg=self.theme["fg"])
        text.tag_configure("h", font=self.big_bold, foreground=self.theme["heading"], spacing1=10)
        for line in CHEAT_SHEET.splitlines(True):
            if line.startswith("## "):
                text.insert("end", line[3:], "h")
            else:
                text.insert("end", line)
        text.configure(state="disabled")

    def show_about(self):
        messagebox.showinfo(
            APP_NAME,
            "PythonIDE\n\nA simple Python editor for students.\n\n"
            "Python {}\n".format(sys.version.split()[0]),
            parent=self.root)

    def _report_bug(self, exc, value, tb):
        text = "".join(traceback.format_exception(exc, value, tb))
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(os.path.join(SETTINGS_DIR, "error.log"), "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + text + "\n")
        except OSError:
            pass
        sys.stderr.write(text) if sys.stderr else None
        self.status("Something went wrong inside PythonIDE (details saved in error.log).")

    def _load_settings(self):
        settings = dict(DEFAULT_SETTINGS)
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings.update(json.load(f))
        except (OSError, ValueError):
            pass
        return settings

    def _save_settings(self):
        self.settings["language"] = self.language.get()
        try:
            self.settings["auto_delay"] = int(self.speed.get())
        except (AttributeError, tk.TclError):
            pass
        try:
            os.makedirs(SETTINGS_DIR, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
        except OSError:
            pass


CHEAT_SHEET = """\
## Show something
print("Hello")
print("Sum is", 5 + 3)
print("A", "B", sep="-")        # A-B
print("no new line", end=" ")

## Get input from the keyboard
name = input("Your name: ")       # text
age = int(input("Your age: "))     # whole number
price = float(input("Price: "))    # decimal number

## Maths
+  -  *  /       add, subtract, multiply, divide
//               whole-number division  (7 // 2 = 3)
%                remainder               (7 % 2 = 1)
**               power                   (2 ** 3 = 8)
round(3.14159, 2)  ->  3.14
import math  ->  math.sqrt(16), math.pi

## Compare
==  equal          !=  not equal
>   greater         <   smaller
>=  greater or equal  <=  smaller or equal
and   or   not

## if / elif / else
if marks >= 40:
    print("Pass")
elif marks >= 35:
    print("Almost")
else:
    print("Fail")

## for loop
for i in range(5):          # 0 1 2 3 4
    print(i)
for i in range(1, 11):      # 1 to 10
    print(i)
for i in range(10, 0, -1):  # 10 down to 1
    print(i)

## while loop
n = 1
while n <= 5:
    print(n)
    n = n + 1

## Text (strings)
s = "Nepal"
len(s)  s.upper()  s.lower()  s[0]  s[-1]  s[1:3]

## Lists
nums = [4, 7, 1]
nums.append(9)   len(nums)   sum(nums)   max(nums)   min(nums)
nums[0]          sorted(nums)

## Functions
def area(l, b):
    return l * b

print(area(5, 3))

## Remember
* Lines after a colon : must be indented (4 spaces / Tab).
* Python cares about Capital letters: print, not Print.
* input() always gives text. Use int() or float() for numbers.
"""


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    root = tk.Tk()
    App(root, path)
    root.mainloop()


if __name__ == "__main__":
    main()
