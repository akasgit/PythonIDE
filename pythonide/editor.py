"""The code editor: a Text widget with line numbers, colours and auto-indent."""

import bisect
import builtins
import keyword
import re
import tkinter as tk

INDENT = "    "

THEME = {
    "bg": "#ffffff",
    "fg": "#1e1e1e",
    "gutter_bg": "#f0f0f0",
    "gutter_fg": "#8a8a8a",
    "current_line": "#f5f9ff",
    "select": "#cce4ff",
    "keyword": "#0000cc",
    "builtin": "#8a2be2",
    "string": "#067d17",
    "comment": "#8c8c8c",
    "number": "#c45200",
    "defname": "#0b6e99",
    "step_line": "#fff3a0",
    "error_line": "#ffd6d6",
}


def _make_pattern():
    kw = r"\b(?:" + "|".join(keyword.kwlist) + r")\b"
    names = [n for n in dir(builtins) if not n.startswith("_") and n not in keyword.kwlist]
    bi = r"\b(?:" + "|".join(sorted(names, key=len, reverse=True)) + r")\b"
    string = (
        r"(?P<string>[rRbBfFuU]{0,2}(?:'''[\s\S]*?(?:'''|\Z)|\"\"\"[\s\S]*?(?:\"\"\"|\Z)"
        r"|'[^'\\\n]*(?:\\.[^'\\\n]*)*'?|\"[^\"\\\n]*(?:\\.[^\"\\\n]*)*\"?))"
    )
    return re.compile(
        r"(?P<comment>#[^\n]*)|" + string +
        r"|(?P<defname>(?<=\bdef )\s*\w+|(?<=\bclass )\s*\w+)"
        r"|(?P<keyword>" + kw + r")"
        r"|(?P<builtin>" + bi + r")"
        r"|(?P<number>\b\d+\.?\d*(?:[eE][+-]?\d+)?\b)"
    )


PATTERN = _make_pattern()
TOKEN_TAGS = ("comment", "string", "defname", "keyword", "builtin", "number")


class CodeEditor(tk.Frame):
    def __init__(self, master, font, on_change=None, **kw):
        tk.Frame.__init__(self, master, bg=THEME["bg"], **kw)
        self.font = font
        self.on_change = on_change
        self._highlight_job = None

        self.gutter = tk.Canvas(self, width=40, bg=THEME["gutter_bg"],
                                highlightthickness=0, bd=0)
        self.text = tk.Text(
            self, undo=True, maxundo=-1, autoseparators=True, wrap="none",
            font=font, bg=THEME["bg"], fg=THEME["fg"], insertbackground="#000000",
            selectbackground=THEME["select"], inactiveselectbackground=THEME["select"],
            bd=0, highlightthickness=0, padx=6, pady=4, insertwidth=2,
            tabs=(font.measure(INDENT),),
        )
        self.vbar = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.hbar = tk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self.hbar.set)

        self.gutter.grid(row=0, column=0, sticky="ns")
        self.text.grid(row=0, column=1, sticky="nsew")
        self.vbar.grid(row=0, column=2, sticky="ns")
        self.hbar.grid(row=1, column=1, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        for tag in TOKEN_TAGS:
            self.text.tag_configure(tag, foreground=THEME[tag])
        self.text.tag_configure("keyword", font=self._bold())
        self.text.tag_configure("current_line", background=THEME["current_line"])
        self.text.tag_configure("step_line", background=THEME["step_line"])
        self.text.tag_configure("error_line", background=THEME["error_line"])
        self.text.tag_raise("sel")

        t = self.text
        t.bind("<Return>", self._on_return)
        t.bind("<KP_Enter>", self._on_return)
        t.bind("<Tab>", self._on_tab)
        t.bind("<Shift-Tab>", self._on_shift_tab)
        try:
            t.bind("<ISO_Left_Tab>", self._on_shift_tab)  # Shift+Tab on Linux
        except tk.TclError:
            pass  # this key name does not exist on Windows
        t.bind("<BackSpace>", self._on_backspace)
        t.bind("<Control-slash>", self._toggle_comment)
        t.bind("<<TextChanged>>", self._on_modified)
        t.bind("<KeyRelease>", lambda e: self._update_current_line())
        t.bind("<ButtonRelease-1>", lambda e: self._update_current_line())
        t.bind("<Configure>", lambda e: self.redraw_gutter())

        # Watch every insert/delete (typing, paste, undo...) by wrapping the
        # widget's Tcl command, the same way IDLE does.
        self._orig_cmd = t._w + "_orig"
        self.tk.call("rename", t._w, self._orig_cmd)
        self.tk.createcommand(t._w, self._proxy)

    def _proxy(self, *args):
        try:
            result = self.tk.call((self._orig_cmd,) + args)
        except tk.TclError:
            return ""
        if args and args[0] in ("insert", "delete", "replace"):
            self.text.event_generate("<<TextChanged>>", when="tail")
        return result

    # -- public ---------------------------------------------------------------

    def get(self):
        return self.text.get("1.0", "end-1c")

    def set(self, source):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", source)
        self.text.edit_reset()
        self.text.edit_modified(False)
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self.highlight()
        self.redraw_gutter()
        self._update_current_line()

    def is_modified(self):
        return bool(self.text.edit_modified())

    def mark_saved(self):
        self.text.edit_modified(False)

    def set_font(self, font):
        self.font = font
        self.text.configure(font=font, tabs=(font.measure(INDENT),))
        self.text.tag_configure("keyword", font=self._bold())
        self.redraw_gutter()

    def set_readonly(self, readonly):
        self.text.configure(state="disabled" if readonly else "normal")

    def show_line(self, tag, lineno):
        """Highlight one line with ``tag`` (step_line / error_line)."""
        self.text.tag_remove(tag, "1.0", "end")
        if lineno:
            self.text.tag_add(tag, "{}.0".format(lineno), "{}.0+1l".format(lineno))
            self.text.see("{}.0".format(lineno))
        self.redraw_gutter()

    def clear_marks(self):
        for tag in ("step_line", "error_line"):
            self.text.tag_remove(tag, "1.0", "end")
        self.redraw_gutter()

    # -- syntax colours -------------------------------------------------------

    def cancel_jobs(self):
        if self._highlight_job is not None:
            self.after_cancel(self._highlight_job)
            self._highlight_job = None

    def schedule_highlight(self):
        if self._highlight_job is not None:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(150, self.highlight)

    def highlight(self):
        self._highlight_job = None
        source = self.get()
        starts = [0]
        for m in re.finditer("\n", source):
            starts.append(m.end())

        def index(offset):
            line = bisect.bisect_right(starts, offset) - 1
            return "{}.{}".format(line + 1, offset - starts[line])

        t = self.text
        for tag in TOKEN_TAGS:
            t.tag_remove(tag, "1.0", "end")
        for m in PATTERN.finditer(source):
            kind = m.lastgroup
            if kind:
                t.tag_add(kind, index(m.start()), index(m.end()))

    # -- gutter ---------------------------------------------------------------

    def _on_yscroll(self, first, last):
        self.vbar.set(first, last)
        self.redraw_gutter()

    def redraw_gutter(self):
        g = self.gutter
        g.delete("all")
        last_line = int(self.text.index("end-1c").split(".")[0])
        width = self.font.measure("0" * max(2, len(str(last_line)))) + 16
        if int(g.cget("width")) != width:
            g.configure(width=width)
        step = self.text.tag_ranges("step_line")
        error = self.text.tag_ranges("error_line")
        step_line = int(str(step[0]).split(".")[0]) if step else None
        error_line = int(str(error[0]).split(".")[0]) if error else None

        index = self.text.index("@0,0")
        while True:
            info = self.text.dlineinfo(index)
            if info is None:
                break
            y, height = info[1], info[3]
            lineno = int(index.split(".")[0])
            colour = THEME["gutter_fg"]
            if lineno == step_line:
                g.create_rectangle(0, y, width, y + height, fill=THEME["step_line"], width=0)
                colour = "#000000"
            elif lineno == error_line:
                g.create_rectangle(0, y, width, y + height, fill=THEME["error_line"], width=0)
                colour = "#b00000"
            g.create_text(width - 8, y + height // 2, anchor="e", text=str(lineno),
                          font=self.font, fill=colour)
            nxt = self.text.index("{}+1line".format(index))
            if nxt == index:
                break
            index = nxt

    # -- editing helpers ------------------------------------------------------

    def _on_modified(self, event=None):
        self.schedule_highlight()
        self.redraw_gutter()
        if self.on_change:
            self.on_change()

    def _update_current_line(self):
        self.text.tag_remove("current_line", "1.0", "end")
        self.text.tag_add("current_line", "insert linestart", "insert linestart+1l")
        self.text.tag_lower("current_line")

    def _on_return(self, event):
        t = self.text
        if t.cget("state") == "disabled":
            return "break"
        line = t.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        code = line.split("#")[0].rstrip()
        if code.endswith(":"):
            indent += INDENT
        elif re.match(r"\s*(return|break|continue|pass|raise)\b", code):
            indent = indent[:-len(INDENT)] if indent.endswith(INDENT) else indent
        t.edit_separator()
        if t.tag_ranges("sel"):
            t.delete("sel.first", "sel.last")
        t.insert("insert", "\n" + indent)
        t.see("insert")
        t.edit_separator()
        self._update_current_line()
        return "break"

    def _selected_lines(self):
        t = self.text
        if t.tag_ranges("sel"):
            first = int(t.index("sel.first").split(".")[0])
            last_index = t.index("sel.last")
            last = int(last_index.split(".")[0])
            if last_index.endswith(".0") and last > first:
                last -= 1
            return first, last
        return None

    def _on_tab(self, event):
        t = self.text
        lines = self._selected_lines()
        if lines:
            for n in range(lines[0], lines[1] + 1):
                t.insert("{}.0".format(n), INDENT)
        else:
            col = int(t.index("insert").split(".")[1])
            t.insert("insert", " " * (len(INDENT) - col % len(INDENT)))
        return "break"

    def _on_shift_tab(self, event):
        t = self.text
        lines = self._selected_lines() or (int(t.index("insert").split(".")[0]),) * 2
        for n in range(lines[0], lines[1] + 1):
            start = "{}.0".format(n)
            lead = re.match(r" {0,4}", t.get(start, "{} lineend".format(start))).group(0)
            if lead:
                t.delete(start, "{}+{}c".format(start, len(lead)))
        return "break"

    def _on_backspace(self, event):
        t = self.text
        if t.tag_ranges("sel"):
            return None
        before = t.get("insert linestart", "insert")
        if before and before.strip(" ") == "" and len(before) >= 1:
            remove = len(before) % len(INDENT) or len(INDENT)
            t.delete("insert-{}c".format(remove), "insert")
            return "break"
        return None

    def _toggle_comment(self, event=None):
        t = self.text
        first, last = self._selected_lines() or (int(t.index("insert").split(".")[0]),) * 2
        lines = [t.get("{}.0".format(n), "{}.end".format(n)) for n in range(first, last + 1)]
        uncomment = all(l.lstrip().startswith("#") for l in lines if l.strip())
        for n, line in zip(range(first, last + 1), lines):
            if not line.strip():
                continue
            if uncomment:
                pos = line.index("#")
                length = 2 if line[pos:pos + 2] == "# " else 1
                t.delete("{}.{}".format(n, pos), "{}.{}".format(n, pos + length))
            else:
                t.insert("{}.0".format(n), "# ")
        return "break"

    def _bold(self):
        bold = self.font.copy()
        bold.configure(weight="bold")
        self._bold_font = bold  # keep a reference
        return bold
