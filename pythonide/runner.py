"""Run a student's program in a child process and stream its output."""

import codecs
import json
import os
import queue
import subprocess
import sys
import threading
import time

CHILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_child.py")
MARK = "\x1e"


def python_executable():
    """The console Python (python.exe), even when the IDE runs under pythonw."""
    exe = sys.executable
    folder, name = os.path.split(exe)
    if name.lower() == "pythonw.exe":
        candidate = os.path.join(folder, "python.exe")
        if os.path.exists(candidate):
            return candidate
    return exe


class ProcessRunner:
    """Events put on ``self.events``:

    ("out", text)       normal program output
    ("err", text)       text the program wrote to stderr
    ("input",)          the program is waiting for a line of input
    ("error", info)     the program crashed; ``info`` from _shared.exception_info
    ("vars", rows)      the program's variables when it ended
    ("stopped",)        the program was stopped by the user
    ("exit", seconds)   the process has ended (always the last event)
    """

    def __init__(self, path, cwd=None):
        self.path = path
        self.cwd = cwd
        # Bounded, so a program printing in an endless loop slows down
        # instead of filling up memory.
        self.events = queue.Queue(maxsize=500)
        self.proc = None
        self._stopped = False

    def start(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        flags = 0
        if os.name == "nt":
            flags = 0x08000000  # CREATE_NO_WINDOW: no black console window
        self.proc = subprocess.Popen(
            [python_executable(), "-u", CHILD, self.path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=env,
            bufsize=0,
            creationflags=flags,
        )
        self._started = time.time()
        self._out_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._err_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._out_thread.start()
        self._err_thread.start()
        threading.Thread(target=self._wait, daemon=True).start()

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def send_input(self, text):
        if not self.is_running():
            return
        try:
            self.proc.stdin.write((text + "\n").encode("utf-8"))
            self.proc.stdin.flush()
        except (OSError, ValueError):
            pass

    def stop(self):
        if self.is_running():
            self._stopped = True
            try:
                self.proc.kill()
            except OSError:
                pass

    # -- background threads -------------------------------------------------

    def _put(self, event):
        while True:
            try:
                self.events.put(event, timeout=0.5)
                return
            except queue.Full:
                # After Stop, drop leftover output but keep the final events.
                if self._stopped and event[0] in ("out", "err"):
                    return

    def _read_stdout(self):
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        buf = ""
        stream = self.proc.stdout
        while True:
            data = stream.read(4096)
            if not data:
                break
            buf += decoder.decode(data)
            buf = self._parse(buf)
        buf += decoder.decode(b"", final=True)
        if buf:
            self._put(("out", buf))

    def _parse(self, buf):
        """Split ``buf`` into output and control messages; return leftovers."""
        while buf:
            i = buf.find(MARK)
            if i == -1:
                self._put(("out", buf))
                return ""
            if i > 0:
                self._put(("out", buf[:i]))
                buf = buf[i:]
            j = buf.find("\n")
            if j == -1:
                return buf  # rest of the message has not arrived yet
            raw, buf = buf[1:j], buf[j + 1:]
            try:
                msg = json.loads(raw)
            except ValueError:
                self._put(("out", raw + "\n"))
                continue
            kind = msg.get("t")
            if kind == "input":
                self._put(("input",))
            elif kind == "error":
                self._put(("error", msg["info"]))
            elif kind == "vars":
                self._put(("vars", msg["vars"]))
            elif kind == "stopped":
                self._put(("stopped",))
        return ""

    def _read_stderr(self):
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        stream = self.proc.stderr
        while True:
            data = stream.read(4096)
            if not data:
                break
            text = decoder.decode(data)
            if text:
                self._put(("err", text))

    def _wait(self):
        self.proc.wait()
        self._out_thread.join()
        self._err_thread.join()
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            try:
                stream.close()
            except OSError:
                pass
        if self._stopped:
            self._put(("stopped",))
        self._put(("exit", time.time() - self._started))
