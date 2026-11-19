"""The website must use the same error help and examples as the desktop app."""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WebAssetsTest(unittest.TestCase):
    def test_web_copies_are_up_to_date(self):
        result = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "export_web_assets.py"), "--check"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
