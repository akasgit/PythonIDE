"""Double-click this file to start PythonIDE (no black console window)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pythonide.app import main  # noqa: E402

main()
