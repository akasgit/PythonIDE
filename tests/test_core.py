import os
import queue
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pythonide import errors  # noqa: E402
from pythonide.runner import ProcessRunner  # noqa: E402
from pythonide.stepper import StepRunner  # noqa: E402


def collect(runner, inputs=(), timeout=15, stop_after=None):
    """Drive a runner to the end and return its events."""
    inputs = list(inputs)
    events = []
    deadline = time.time() + timeout
    started = time.time()
    while time.time() < deadline:
        if stop_after is not None and time.time() - started > stop_after:
            runner.stop()
            stop_after = None
        try:
            event = runner.events.get(timeout=0.1)
        except queue.Empty:
            continue
        events.append(event)
        if event[0] == "input":
            runner.send_input(inputs.pop(0))
        elif event[0] == "line":
            runner.next_step()
        elif event[0] == "exit":
            return events
    raise AssertionError("program did not finish: {}".format(events[-5:]))


def output(events):
    return "".join(e[1] for e in events if e[0] == "out")


def first(events, kind):
    for e in events:
        if e[0] == kind:
            return e
    return None


class ProcessRunnerTest(unittest.TestCase):
    def run_code(self, code, **kw):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "prog.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        runner = ProcessRunner(path)
        runner.start()
        return collect(runner, **kw)

    def test_output_and_vars(self):
        events = self.run_code('x = 5\nname = "नेपाल"\nprint("hi", x, name)\n')
        self.assertEqual(output(events), "hi 5 नेपाल\n")
        rows = first(events, "vars")[1]
        self.assertIn(["x", "int (whole number)", "5"], rows)

    def test_input(self):
        events = self.run_code('a = int(input("A? "))\nb = int(input("B? "))\nprint(a + b)\n',
                               inputs=["2", "40"])
        self.assertEqual(output(events), "A? B? 42\n")
        self.assertEqual(len([e for e in events if e[0] == "input"]), 2)

    def test_runtime_error_line(self):
        events = self.run_code('x = 1\ny = 0\nprint(x / y)\n')
        info = first(events, "error")[1]
        self.assertEqual(info["type"], "ZeroDivisionError")
        self.assertEqual(info["line"], 3)

    def test_syntax_error_line(self):
        events = self.run_code('x = 1\nif x == 1\n    print(x)\n')
        info = first(events, "error")[1]
        self.assertEqual(info["type"], "SyntaxError")
        self.assertEqual(info["line"], 2)

    def test_stop_endless_loop(self):
        events = self.run_code('while True:\n    print("again")\n', stop_after=1.0)
        self.assertIsNotNone(first(events, "stopped"))


class StepRunnerTest(unittest.TestCase):
    def test_steps_and_variables(self):
        runner = StepRunner('total = 0\nfor i in range(3):\n    total = total + i\nprint(total)\n')
        runner.start()
        events = collect(runner)
        lines = [e[1] for e in events if e[0] == "line"]
        self.assertEqual(lines, [1, 2, 3, 2, 3, 2, 3, 2, 4])
        self.assertEqual(output(events), "3\n")
        last_scopes = [e for e in events if e[0] == "line"][-1][2]
        self.assertIn(["total", "int (whole number)", "3"], last_scopes[-1][1])

    def test_function_scope(self):
        runner = StepRunner('def add(a, b):\n    return a + b\n\nprint(add(2, 3))\n')
        runner.start()
        events = collect(runner)
        inner = [e[2] for e in events if e[0] == "line" and e[1] == 2][0]
        self.assertEqual(inner[0][0], "Inside add()")
        self.assertIn(["a", "int (whole number)", "2"], inner[0][1])

    def test_input_and_error(self):
        runner = StepRunner('n = int(input("n? "))\nprint(10 / n)\n')
        runner.start()
        events = collect(runner, inputs=["0"])
        info = first(events, "error")[1]
        self.assertEqual((info["type"], info["line"]), ("ZeroDivisionError", 2))

    def test_stop(self):
        runner = StepRunner('while True:\n    pass\n')
        runner.start()
        event = runner.events.get(timeout=5)
        self.assertEqual(event[0], "line")
        runner.stop()
        kinds = [runner.events.get(timeout=5)[0] for _ in range(3)]
        self.assertEqual(kinds, ["stopped", "vars", "exit"])


class ExplainTest(unittest.TestCase):
    def title(self, type_, msg, text, source=""):
        return errors.explain({"type": type_, "msg": msg, "text": text, "line": 1}, source).title

    def test_missing_colon(self):
        self.assertIn("Colon", self.title("SyntaxError", "invalid syntax", "if x > 5"))
        self.assertIn("Colon", self.title("SyntaxError", "expected ':'", "for i in range(5)"))

    def test_single_equals(self):
        self.assertIn("==", self.title("SyntaxError", "invalid syntax", "if x = 5:"))

    def test_unclosed_string(self):
        self.assertIn("not closed", self.title("SyntaxError", "EOL while scanning string literal",
                                               'print("hi)'))

    def test_print_without_brackets(self):
        self.assertIn("brackets", self.title(
            "SyntaxError", "Missing parentheses in call to 'print'", 'print "hi"'))

    def test_name_capital_letters(self):
        h = errors.explain({"type": "NameError", "msg": "name 'Print' is not defined",
                            "text": 'Print("hi")', "line": 1}, 'Print("hi")')
        self.assertIn("print", h.hint_en)

    def test_name_misspelled_variable(self):
        src = 'total = 5\nprint(totl)\n'
        h = errors.explain({"type": "NameError", "msg": "name 'totl' is not defined",
                            "text": "print(totl)", "line": 2}, src)
        self.assertIn("total", h.hint_en)

    def test_text_plus_number(self):
        self.assertIn("text and numbers", self.title(
            "TypeError", 'can only concatenate str (not "int") to str', 'print("a" + 1)'))

    def test_not_a_number(self):
        self.assertIn("not a number", self.title(
            "ValueError", "invalid literal for int() with base 10: 'abc'", "x = int(input())"))

    def test_every_help_has_nepali(self):
        cases = [("ZeroDivisionError", "division by zero"), ("IndexError", "list index out of range"),
                 ("IndentationError", "expected an indented block"), ("Weird", "?")]
        for type_, msg in cases:
            h = errors.explain({"type": type_, "msg": msg, "text": "", "line": 1})
            self.assertTrue(h.ne, type_)


if __name__ == "__main__":
    unittest.main()
