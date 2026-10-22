import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from installer_adapter import available_providers, render_selection


class SelectionTests(unittest.TestCase):
    def test_choices_and_architecture(self):
        self.assertTrue(all(p["available"] for p in available_providers("x86_64-linux")))
        self.assertEqual([p["id"] for p in available_providers("aarch64-linux") if not p["available"]], ["ivpn"])
        self.assertIn("= null;", render_selection(None, "aarch64-linux"))
        self.assertIn('= "proton";', render_selection("proton", "aarch64-linux"))

    def test_invalid_conflicting_and_injected_values(self):
        for value in (["mullvad", "proton"], "unknown", 'proton"; builtins.abort "oops', True, ""):
            with self.assertRaises(ValueError):
                render_selection(value, "x86_64-linux")
        with self.assertRaises(ValueError):
            render_selection("ivpn", "aarch64-linux")
        with self.assertRaises(ValueError):
            render_selection(None, "aarch64-darwin")


if __name__ == "__main__":
    unittest.main()
