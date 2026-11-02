"""Browser RED/GREEN probe: executes the real named HTTP acceptance case."""

import subprocess
import unittest


class BrowserHost(unittest.TestCase):
    def test_correct_host_capabilities(self):
        result = subprocess.run(
            [
                "node",
                "tests/browser/conditional-formsets.cjs",
                "--case",
                "gap-capability",
                "--output",
                ".planning/phases/06.4-conditional-and-formset-correctness-lifecycle/16-evidence/capability.json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
