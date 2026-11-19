"""Drives the real PythonIDE window. Skipped when there is no display."""
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None

NO_DISPLAY = sys.platform.startswith("linux") and not os.environ.get("DISPLAY")


@unittest.skipIf(tk is None or NO_DISPLAY, "needs tkinter and a display")
class AppTest(unittest.TestCase):
    def setUp(self):
        from pythonide import app as appmod
        self.appmod = appmod
        home = tempfile.mkdtemp()
        appmod.HOME = home
        appmod.SETTINGS_DIR = os.path.join(home, ".pythonide")
        appmod.SETTINGS_FILE = os.path.join(appmod.SETTINGS_DIR, "settings.json")
        self.root = tk.Tk()
        self.app = appmod.App(self.root)

    def tearDown(self):
        self.root.update()
        self.app.close()

    def wait_for(self, condition, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            self.root.update()
            if condition():
                return
            time.sleep(0.02)
        self.fail("timed out; output was:\n" + self.output())

    def output(self):
        return self.app.output.get("1.0", "end-1c")

    def type_input(self, text):
        self.wait_for(lambda: self.app.waiting_input)
        self.app.input_entry.insert(0, text)
        self.app._send_input()

    def test_run_with_input(self):
        self.app.editor.set('a = int(input("A: "))\nb = int(input("B: "))\nprint("Sum =", a + b)\n')
        self.app.run()
        self.type_input("2")
        self.type_input("3")
        self.wait_for(lambda: self.app.mode == "idle")
        self.assertIn("Sum = 5", self.output())
        names = [self.app.vars.item(i, "text") for i in self.app.vars.get_children()]
        self.assertEqual(names, ["a", "b"])

    def test_error_is_explained(self):
        self.app.editor.set('x = 10\nprint(x / 0)\n')
        self.app.run()
        self.wait_for(lambda: self.app.mode == "idle")
        self.assertIn("Error on line 2: Cannot divide by zero", self.output())
        self.assertTrue(self.app.editor.text.tag_ranges("error_line"))

    def test_step_mode(self):
        self.app.editor.set('x = 1\nx = x + 1\nprint(x)\n')
        self.app.step_start()
        self.wait_for(lambda: self.app.editor.text.tag_ranges("step_line"))
        for _ in range(3):
            self.app.step_next()
            self.root.update()
            time.sleep(0.05)
        self.wait_for(lambda: self.app.mode == "idle")
        self.assertIn("2", self.output())

    def test_every_example_compiles(self):
        from pythonide import examples
        for _, items in examples.EXAMPLES:
            for title, code in items:
                compile(code, title, "exec")


if __name__ == "__main__":
    unittest.main()
