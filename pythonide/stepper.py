"""Run a program one line at a time so students can watch it work.

The program runs in a background thread of the IDE itself, under
``sys.settrace``. Before each line runs, the tracer reports the line and the
current variables, then waits until the IDE says "next".
"""

import builtins
import linecache
import queue
import sys
import threading

from . import _shared

FILENAME = "<your program>"


class _Stopped(BaseException):
    """Raised inside the program to end it when the student presses Stop."""


class _OutputWriter:
    def __init__(self, runner):
        self._runner = runner

    def write(self, text):
        if text:
            self._runner.events.put(("out", text))
        return len(text)

    def flush(self):
        pass


class StepRunner:
    """Events put on ``self.events``:

    ("line", lineno, scopes)  about to run ``lineno``; scopes is a list of
                              (title, rows) from the innermost scope outwards
    ("out", text)             program output
    ("input",)                the program is waiting for input
    ("error", info)           the program crashed
    ("vars", rows)            global variables when the program ended
    ("stopped",)              stopped by the user
    ("exit", steps)           finished (always the last event)
    """

    def __init__(self, source):
        self.source = source
        self.events = queue.Queue()
        self.steps = 0
        self._go = threading.Event()
        self._inputs = queue.Queue()
        self._stop = False
        self._free_run = False
        self._waiting_input = False
        self._thread = None

    # -- called from the IDE --------------------------------------------------

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def next_step(self):
        self._go.set()

    def run_to_end(self):
        """Stop pausing and let the rest of the program run."""
        self._free_run = True
        self._go.set()

    def send_input(self, text):
        self._inputs.put(text)

    def stop(self):
        self._stop = True
        self._inputs.put(None)
        self._go.set()

    # -- the program thread ---------------------------------------------------

    def _run(self):
        lines = self.source.splitlines(True)
        linecache.cache[FILENAME] = (len(self.source), None, lines, FILENAME)
        writer = _OutputWriter(self)

        def ide_print(*args, **kwargs):
            if kwargs.get("file") is None:
                kwargs["file"] = writer
            builtins.print(*args, **kwargs)

        def ide_input(prompt=""):
            writer.write(str(prompt))
            self.events.put(("input",))
            text = self._inputs.get()
            if text is None or self._stop:
                raise _Stopped()
            return text

        program_builtins = dict(builtins.__dict__)
        program_builtins["print"] = ide_print
        program_builtins["input"] = ide_input
        namespace = {"__name__": "__main__", "__builtins__": program_builtins}

        try:
            code = compile(self.source, FILENAME, "exec")
        except SyntaxError as exc:
            self.events.put(("error", _shared.exception_info(exc, FILENAME)))
            self.events.put(("exit", 0))
            return

        sys.settrace(self._trace_calls)
        try:
            exec(code, namespace)
        except _Stopped:
            self.events.put(("stopped",))
        except SystemExit:
            pass
        except BaseException as exc:  # noqa: B902 - we report every error
            self.events.put(("error", _shared.exception_info(exc, FILENAME)))
        finally:
            sys.settrace(None)
        self.events.put(("vars", _shared.describe_vars(namespace)))
        self.events.put(("exit", self.steps))

    def _trace_calls(self, frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None  # don't step through Python's own code
        return self._trace_lines

    def _trace_lines(self, frame, event, arg):
        if self._stop:
            raise _Stopped()
        if event == "line" and not self._free_run:
            self.steps += 1
            self.events.put(("line", frame.f_lineno, self._scopes(frame)))
            self._go.wait()
            self._go.clear()
            if self._stop:
                raise _Stopped()
        return self._trace_lines

    def _scopes(self, frame):
        scopes = []
        f = frame
        while f is not None and f.f_code.co_filename == FILENAME:
            if f.f_code.co_name == "<module>":
                break
            scopes.append(
                ("Inside {}()".format(f.f_code.co_name), _shared.describe_vars(dict(f.f_locals)))
            )
            f = f.f_back
        scopes.append(("Main program", _shared.describe_vars(dict(frame.f_globals))))
        return scopes
