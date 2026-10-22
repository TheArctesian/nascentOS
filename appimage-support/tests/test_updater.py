import base64
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("updater", Path(__file__).parents[1] / "updater.py")
updater = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(updater)


class WatchdogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.seed = self.root / "store-seed"
        self.built = self.root / "store-built"
        for package in (self.seed, self.built):
            (package / "bin").mkdir(parents=True)
            executable = package / "bin/demo"
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
        self.pin = {"id": "demo", "repository": "vendor/demo", "version": "v1",
                    "url": "https://github.com/vendor/demo/releases/download/v1/demo.AppImage",
                    "hash": "sha256-" + base64.b64encode(bytes(32)).decode(),
                    "platform": "x86_64-linux", "license": "mit"}
        self.app = {"repository": "vendor/demo", "assetName": "demo.AppImage",
                    "maxBytes": 1000, "pin": self.pin, "initialPackage": str(self.seed),
                    "autoActivate": True}
        self.config = {"stateDir": str(self.root / "state"), "apps": {"demo": self.app},
                       "nixpkgsPath": "/nix/store/pinned-nixpkgs", "buildFile": "/source/build.nix",
                       "recipePath": "/source"}
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config))
        self.app_dir = Path(self.config["stateDir"]) / "demo"
        self.next_pin = dict(self.pin, version="v2", url=self.pin["url"].replace("v1", "v2"))

    def fake_nix(self, command):
        flag = "--out-link" if command[0] == "nix-build" else "--add-root"
        output = Path(command[command.index(flag) + 1])
        output.symlink_to(self.built if command[0] == "nix-build" else Path(command[2]))

    def invoke(self, *args, pin=None, build=None):
        self.config_path.write_text(json.dumps(self.config))
        with patch.object(sys, "argv", ["updater", "--config", str(self.config_path), *args]), \
             patch.object(updater, "discover", return_value=pin or self.next_pin), \
             patch.object(updater, "run", side_effect=build or self.fake_nix), \
             patch("sys.stdout", new_callable=io.StringIO), \
             patch("sys.stderr", new_callable=io.StringIO):
            return updater.main()

    def status(self):
        return json.loads((self.app_dir / "status.json").read_text())

    def test_activation_and_rollback_hold(self):
        self.assertEqual(self.invoke("update"), 0)
        self.assertEqual((self.app_dir / "current/package").resolve(), self.built)
        self.assertEqual(self.status()["state"], "activated")
        history = json.loads((self.app_dir / "history.json").read_text())
        self.assertEqual(len(history), 2)
        self.assertEqual(json.loads((self.app_dir / "current/build-context.json").read_text()),
                         {"nixpkgsPath": self.config["nixpkgsPath"], "recipePath": "/source"})
        # Both packages remain present and rooted by stable generation symlinks.
        self.assertTrue((self.app_dir / "generations" / history[0] / "package").exists())
        self.assertEqual(self.invoke("rollback", "demo"), 0)
        self.assertEqual((self.app_dir / "current/package").resolve(), self.seed)
        self.assertEqual(self.invoke("update"), 0)
        self.assertEqual(self.status()["state"], "held")
        self.assertEqual(self.invoke("resume", "demo"), 0)
        self.assertFalse((self.app_dir / "hold").exists())

    def test_build_failure_keeps_last_known_good(self):
        def fail_build(command):
            if command[0] == "nix-build":
                raise subprocess.CalledProcessError(102, command)
            self.fake_nix(command)
        self.assertEqual(self.invoke("update", build=fail_build), 1)
        self.assertEqual((self.app_dir / "current/package").resolve(), self.seed)
        self.assertEqual(self.status()["state"], "failed")

    def test_missing_executable_keeps_seed(self):
        (self.built / "bin/demo").unlink()
        self.assertEqual(self.invoke("update"), 1)
        self.assertEqual((self.app_dir / "current/package").resolve(), self.seed)

    def test_staging_never_enters_activation_history(self):
        self.app["autoActivate"] = False
        self.assertEqual(self.invoke("update"), 0)
        self.assertEqual(self.status()["state"], "staged")
        self.assertEqual((self.app_dir / "current/package").resolve(), self.seed)
        self.assertEqual(self.invoke("rollback", "demo"), 1)

    def test_same_pin_does_not_build(self):
        self.assertEqual(self.invoke("update", pin=self.pin), 0)
        self.assertEqual(self.status()["state"], "current")
        self.assertEqual(len(list((self.app_dir / "generations").iterdir())), 1)

    def test_reuploaded_version_rejected(self):
        changed = dict(self.pin, hash="sha256-" + base64.b64encode(bytes([1]) * 32).decode())
        self.assertEqual(self.invoke("update", pin=changed), 1)
        self.assertIn("existing version", self.status()["error"])

    def test_one_failed_app_does_not_hide_other_app_status(self):
        other_pin = dict(self.pin, id="other")
        self.config["apps"]["other"] = dict(self.app, pin=other_pin)
        self.config_path.write_text(json.dumps(self.config))
        with patch.object(sys, "argv", ["updater", "--config", str(self.config_path), "update"]), \
             patch.object(updater, "discover", side_effect=[ValueError("API unavailable"), other_pin]), \
             patch.object(updater, "run", side_effect=self.fake_nix), \
             patch("sys.stdout", new_callable=io.StringIO), \
             patch("sys.stderr", new_callable=io.StringIO):
            self.assertEqual(updater.main(), 1)
        other_status = json.loads((Path(self.config["stateDir"]) / "other/status.json").read_text())
        self.assertEqual(other_status["state"], "current")
        self.assertEqual(self.status()["state"], "failed")

    def release(self, **changes):
        asset = {"name": "demo.AppImage", "size": 100,
                 "digest": "sha256:" + "00" * 32,
                 "browser_download_url": self.next_pin["url"]}
        asset.update(changes)
        return {"tag_name": "v2", "draft": False, "prerelease": False, "assets": [asset]}

    def discover(self, release):
        with patch.object(updater.urllib.request, "urlopen") as fetch:
            fetch.return_value.__enter__.return_value.read.return_value = json.dumps(release).encode()
            return updater.discover(self.app)

    def test_discovery_converts_digest(self):
        self.assertEqual(self.discover(self.release()), self.next_pin)

    def test_missing_digest_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "did not publish"):
            self.discover(self.release(digest=None))

    def test_external_asset_url_rejected(self):
        with self.assertRaisesRegex(ValueError, "asset URL"):
            self.discover(self.release(browser_download_url="https://evil.example/demo.AppImage"))

    def test_oversized_asset_rejected(self):
        with self.assertRaisesRegex(ValueError, "size limit"):
            self.discover(self.release(size=1001))

    def test_duplicate_asset_rejected(self):
        release = self.release()
        release["assets"] *= 2
        with self.assertRaisesRegex(ValueError, "exactly one"):
            self.discover(release)

    def test_prerelease_rejected(self):
        release = dict(self.release(), prerelease=True)
        with self.assertRaisesRegex(ValueError, "prerelease"):
            self.discover(release)

    def test_tag_path_injection_rejected(self):
        with self.assertRaises(ValueError):
            updater.validate_pin(dict(self.pin, version="../../bad"), "vendor/demo")

    def test_unknown_app_rejected(self):
        with self.assertRaises(SystemExit):
            self.invoke("rollback", "../bad")

    def test_process_launch_is_never_part_of_validation(self):
        with patch.object(updater.subprocess, "run") as process:
            updater.run(["nix-build", "/source/build.nix"])
            process.assert_called_once_with(["nix-build", "/source/build.nix"],
                                            check=True, timeout=5400)


if __name__ == "__main__":
    unittest.main()
