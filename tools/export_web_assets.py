"""Copy the desktop app's shared Python code and examples into the website.

    python tools/export_web_assets.py          write the files
    python tools/export_web_assets.py --check  fail if they are out of date

The online IDE reuses pythonide/errors.py and pythonide/_shared.py exactly,
and gets every example from pythonide/examples*.py, so both versions stay
the same. Run this after changing any of those files.
"""

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pythonide import examples, examples_class10  # noqa: E402

PY_DIR = os.path.join(ROOT, "web", "resources", "ide", "py")
EXAMPLES_JSON = os.path.join(ROOT, "web", "public", "ide-assets", "examples.json")
COPIED = ["_shared.py", "errors.py"]


def examples_json():
    def groups(items):
        return [{"title": title, "items": [{"title": t, "code": c} for t, c in entries]}
                for title, entries in items]

    data = {
        "welcome": examples.WELCOME,
        "sections": [
            {"title": None, "groups": groups(examples.EXAMPLES)},
            {"title": "Class 10", "groups": groups(examples_class10.CLASS10)},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def main(check):
    stale = []
    for name in COPIED:
        src = os.path.join(ROOT, "pythonide", name)
        dst = os.path.join(PY_DIR, name)
        with open(src, encoding="utf-8") as f:
            wanted = f.read()
        current = open(dst, encoding="utf-8").read() if os.path.exists(dst) else None
        if current != wanted:
            stale.append(dst)
            if not check:
                os.makedirs(PY_DIR, exist_ok=True)
                shutil.copyfile(src, dst)
    wanted = examples_json()
    current = open(EXAMPLES_JSON, encoding="utf-8").read() if os.path.exists(EXAMPLES_JSON) else None
    if current != wanted:
        stale.append(EXAMPLES_JSON)
        if not check:
            with open(EXAMPLES_JSON, "w", encoding="utf-8", newline="\n") as f:
                f.write(wanted)
    if check and stale:
        print("Out of date (run python tools/export_web_assets.py):")
        for path in stale:
            print("  " + os.path.relpath(path, ROOT))
        return 1
    print("Up to date." if not stale else "Updated {} file(s).".format(len(stale)))
    return 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
