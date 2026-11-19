"""Helpers shared by the program runner (child process) and the step runner.

This module must only use the standard library and must stay importable on
its own, because ``_child.py`` imports it as a plain module (not as part of
the ``pythonide`` package).
"""

import reprlib
import traceback
import types

FRIENDLY_TYPES = {
    "int": "int (whole number)",
    "float": "float (decimal number)",
    "str": "str (text)",
    "bool": "bool (True / False)",
    "list": "list",
    "tuple": "tuple",
    "dict": "dict",
    "set": "set",
    "NoneType": "None (nothing)",
    "function": "function",
    "range": "range",
}

_repr = reprlib.Repr()
_repr.maxstring = 60
_repr.maxother = 60
_repr.maxlist = 15
_repr.maxtuple = 15
_repr.maxdict = 10
_repr.maxset = 10
_repr.maxlevel = 3


def friendly_type(value):
    name = type(value).__name__
    return FRIENDLY_TYPES.get(name, name)


def short_repr(value):
    try:
        if isinstance(value, types.FunctionType):
            return "function {}()".format(value.__name__)
        return _repr.repr(value)
    except Exception:
        return "<cannot show>"


def describe_vars(namespace):
    """Return [[name, type, value], ...] for the user's own variables."""
    rows = []
    for name, value in namespace.items():
        if name.startswith("__"):
            continue
        if isinstance(value, (types.ModuleType, type)):
            continue
        if isinstance(value, types.BuiltinFunctionType):
            continue
        rows.append([name, friendly_type(value), short_repr(value)])
    return rows


def exception_info(exc, filename):
    """Turn an exception into a JSON-friendly dict about the student's code."""
    info = {
        "type": type(exc).__name__,
        "msg": str(exc),
        "line": None,
        "col": None,
        "text": None,
        "traceback": "",
    }
    if isinstance(exc, SyntaxError):
        info["msg"] = exc.msg or ""
        if exc.filename == filename:
            info["line"] = exc.lineno
            info["col"] = exc.offset
            info["text"] = (exc.text or "").rstrip("\n")
        info["traceback"] = "".join(traceback.format_exception_only(type(exc), exc))
        return info

    frames = [f for f in traceback.extract_tb(exc.__traceback__) if f.filename == filename]
    if frames:
        last = frames[-1]
        info["line"] = last.lineno
        info["text"] = last.line
    info["traceback"] = "Traceback (most recent call last):\n" + "".join(
        traceback.format_list(frames)
    ) + "".join(traceback.format_exception_only(type(exc), exc))
    return info
