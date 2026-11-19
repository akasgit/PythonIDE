"""Runs a student's program in a separate process.

Usage: python -u _child.py PROGRAM.py

Normal output from the program goes to stdout. Control messages for the IDE
are written to stdout too (so they stay in order with the output), as one
line each: the MARK character followed by JSON.
"""

import builtins
import json
import linecache
import os
import sys

import _shared  # found next to this file (sys.path[0])

MARK = "\x1e"


def main():
    path = os.path.abspath(sys.argv[1])
    # On Windows, print() would write "\r\n"; the IDE expects plain "\n".
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(newline="\n")
        except (AttributeError, ValueError):
            pass
    out = sys.stdout

    def send(**msg):
        out.write(MARK + json.dumps(msg) + "\n")
        out.flush()

    real_input = builtins.input

    def ide_input(prompt=""):
        out.write(str(prompt))
        send(t="input")
        line = sys.stdin.readline()
        if not line:
            raise EOFError("No more input")
        return line.rstrip("\r\n")

    builtins.input = ide_input

    # Make the program feel like it was run directly: its own folder is the
    # current folder and the first place imports are looked up.
    folder = os.path.dirname(path)
    sys.path[0] = folder
    try:
        os.chdir(folder)
    except OSError:
        pass
    sys.argv = [path]

    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    linecache.cache[path] = (len(source), None, source.splitlines(True), path)

    namespace = {"__name__": "__main__", "__file__": path, "__builtins__": builtins}
    try:
        code = compile(source, path, "exec")
        exec(code, namespace)
        _finish_turtle()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        send(t="stopped")
    except BaseException as exc:  # noqa: B902 - we report every error
        sys.stdout.flush()
        send(t="error", info=_shared.exception_info(exc, path))
    finally:
        builtins.input = real_input
    try:
        send(t="vars", vars=_shared.describe_vars(namespace))
    except Exception:
        pass


def _finish_turtle():
    """Keep a turtle window open until the student closes it."""
    turtle = sys.modules.get("turtle")
    if turtle is None:
        return
    if getattr(getattr(turtle, "_Screen", None), "_root", None) is None:
        return  # turtle was imported but no window was opened
    try:
        turtle.done()
    except Exception:
        pass


if __name__ == "__main__":
    main()
