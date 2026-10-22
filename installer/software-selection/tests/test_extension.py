"""Checked Calamares patch boundaries and execution ordering."""
from pathlib import Path
import runpy
import unittest

PATCH = runpy.run_path(str(Path(__file__).resolve().parents[1] / "patch-extension.py"))["patch"]
SOURCE = '''from nascent_install import prepare
def run(root_mount_point, config):
    try:
        prepare(root_mount_point, config)
    except ValueError:
        return ("error", "message")
    install_target()
'''


class ExtensionTests(unittest.TestCase):
    def test_handoff_is_inside_checked_job_after_prepare(self):
        changed = PATCH(SOURCE, "/nix/store/manifest.json")
        self.assertIn("from nascent_software import install as install_software", changed)
        self.assertIn("        install_software(root_mount_point, config, '/nix/store/manifest.json')", changed)
        self.assertLess(changed.index("        prepare("), changed.index("        install_software("))
        self.assertLess(changed.index("        install_software("), changed.index("    except ValueError:"))

    def test_changed_missing_or_duplicate_anchors_stop_the_build(self):
        for source in (SOURCE.replace("from nascent_install", "from other_module"),
                       SOURCE.replace("        prepare(", "        new_prepare("), SOURCE + SOURCE):
            with self.subTest(source=source), self.assertRaises(ValueError):
                PATCH(source, "/nix/store/manifest.json")

    def test_patch_cannot_be_applied_twice(self):
        changed = PATCH(SOURCE, "/nix/store/manifest.json")
        with self.assertRaises(ValueError):
            PATCH(changed, "/nix/store/manifest.json")


if __name__ == "__main__":
    unittest.main()
