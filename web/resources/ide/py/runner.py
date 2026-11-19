"""Runs a student's program in the browser (Pyodide inside a Web Worker).

The worker gives us a module called ``ide`` with three functions:

    ide.post(json_text)   send a message to the page
    ide.wait()            block until the page sends a command; returns JSON
    ide.sleep(seconds)    block for a while; returns a command number or 0

Messages sent to the page (as JSON, key "t"):
    out / err     program output            {"text": ...}
    input         waiting for a line of input
    line          step mode: about to run   {"line": n, "scopes": [[title, rows], ...]}
    error         the program crashed        {"info": {...}, "help": {...}}
    stopped       stopped by the student
    vars          variables at the end       {"vars": rows}
    done          finished                   {"seconds": s, "steps": n}
"""

import builtins
import json
import linecache
import sys
import time

import _shared
import errors
import ide

FILENAME = "<your program>"
CMD_NEXT, CMD_TO_END, CMD_STOP, CMD_INPUT = 1, 2, 3, 4

_real_sleep = time.sleep


class Stopped(BaseException):
    """Raised inside the program when the student presses Stop."""


def post(**msg):
    ide.post(json.dumps(msg))


def wait():
    reply = json.loads(ide.wait())
    if reply["cmd"] == CMD_STOP:
        raise Stopped()
    return reply


class Output:
    """sys.stdout / sys.stderr that sends text to the page in batches."""

    def __init__(self, kind):
        self.kind = kind
        self.parts = []
        self.size = 0
        self.last = time.monotonic()

    def write(self, text):
        if not isinstance(text, str):
            raise TypeError("write() argument must be str, not " + type(text).__name__)
        if text:
            self.parts.append(text)
            self.size += len(text)
            if self.size > 8192 or time.monotonic() - self.last > 0.05:
                self.flush()
        return len(text)

    def flush(self):
        if self.parts:
            post(t=self.kind, text="".join(self.parts))
            self.parts = []
            self.size = 0
        self.last = time.monotonic()

    def isatty(self):
        return False

    @property
    def encoding(self):
        return "utf-8"


class Session:
    def __init__(self, source, step_mode):
        self.source = source
        self.step_mode = step_mode
        self.free_run = False
        self.steps = 0
        self.out = Output("out")
        self.err = Output("err")

    # -- replacements for input() and time.sleep() ---------------------------

    def flush(self):
        self.out.flush()
        self.err.flush()
        turtle = sys.modules.get("turtle")
        if turtle is not None and hasattr(turtle, "_flush"):
            turtle._flush()

    def input(self, prompt=""):
        self.out.write(str(prompt))
        self.flush()
        post(t="input")
        while True:
            reply = wait()
            if reply["cmd"] == CMD_INPUT:
                return reply["text"]

    def sleep(self, seconds):
        self.flush()
        end = time.monotonic() + max(0.0, float(seconds))
        while True:
            left = end - time.monotonic()
            if left <= 0:
                return
            if ide.sleep(min(left, 0.25)) == CMD_STOP:
                raise Stopped()

    # -- step mode -------------------------------------------------------------

    def trace_calls(self, frame, event, arg):
        if frame.f_code.co_filename != FILENAME or self.free_run:
            return None
        return self.trace_lines

    def trace_lines(self, frame, event, arg):
        if self.free_run:
            return None
        if event == "line":
            self.steps += 1
            self.flush()
            post(t="line", line=frame.f_lineno, scopes=self.scopes(frame))
            while True:
                reply = wait()
                if reply["cmd"] == CMD_NEXT:
                    break
                if reply["cmd"] == CMD_TO_END:
                    self.free_run = True
                    sys.settrace(None)
                    return None
        return self.trace_lines

    def scopes(self, frame):
        scopes = []
        f = frame
        while f is not None and f.f_code.co_filename == FILENAME and f.f_code.co_name != "<module>":
            scopes.append(["Inside {}()".format(f.f_code.co_name), _shared.describe_vars(dict(f.f_locals))])
            f = f.f_back
        scopes.append(["Main program", _shared.describe_vars(dict(frame.f_globals))])
        return scopes

    # -- running ---------------------------------------------------------------

    def report(self, exc):
        self.flush()
        info = _shared.exception_info(exc, FILENAME)
        h = errors.explain(info, self.source)
        post(t="error", info=info, help={
            "title": h.title, "en": h.en, "ne": h.ne, "hint_en": h.hint_en, "hint_ne": h.hint_ne,
        })

    def run(self):
        started = time.monotonic()
        old = (sys.stdout, sys.stderr, builtins.input, time.sleep)
        sys.stdout, sys.stderr = self.out, self.err
        builtins.input = self.input
        time.sleep = self.sleep
        sys.modules.pop("turtle", None)  # a fresh drawing for every run
        linecache.cache[FILENAME] = (len(self.source), None, self.source.splitlines(True), FILENAME)
        namespace = {"__name__": "__main__", "__builtins__": builtins}
        try:
            try:
                code = compile(self.source, FILENAME, "exec")
            except SyntaxError as exc:
                self.report(exc)
                return
            if self.step_mode:
                sys.settrace(self.trace_calls)
            try:
                exec(code, namespace)
            except (Stopped, KeyboardInterrupt):
                self.flush()
                post(t="stopped")
            except SystemExit:
                pass
            except BaseException as exc:  # noqa: B902 - every error is explained
                self.report(exc)
            finally:
                sys.settrace(None)
            self.flush()
            try:
                post(t="vars", vars=_shared.describe_vars(namespace))
            except Exception:
                pass
        finally:
            self.flush()
            sys.stdout, sys.stderr, builtins.input, time.sleep = old
            post(t="done", seconds=round(time.monotonic() - started, 2), steps=self.steps)


def run(source, step_mode=False):
    Session(source, bool(step_mode)).run()
