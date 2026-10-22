"""Selection boundary and target handoff tests; no Nix or Qt dependency.

Run: python3 -m unittest discover -s installer/software-selection/tests -v
"""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import handoff
import nascent_software_model as model
from nascent_optional_profiles import gaming_defaults, providers, render_gaming


def manifest_for(system="x86_64-linux"):
    """Model tests use explicit evaluated availability, as the Nix build does."""
    return {
        "schemaVersion": 1,
        "system": system,
        "nixpkgsRevision": "test-pinned-revision",
        "apps": [
            {"id": "neovim", "name": "Neovim", "kind": "package",
             "available": True, "proprietary": False, "default": True},
            {"id": "firefox", "name": "Firefox", "kind": "package",
             "available": True, "proprietary": False, "default": True},
            {"id": "cursor", "name": "Cursor", "kind": "package",
             "available": True, "proprietary": True, "default": False},
            {"id": "chatgpt-web", "name": "ChatGPT (web)", "kind": "web",
             "available": True, "proprietary": True, "default": False},
            {"id": "slack", "name": "Slack", "kind": "package",
             "available": system == "x86_64-linux", "proprietary": True,
             "default": False},
            {"id": "unity", "name": "Unity", "kind": "manual",
             "available": False, "proprietary": True, "default": False},
            {"id": "unavailable", "name": "Unavailable", "kind": "package",
             "available": False, "proprietary": False, "default": True},
        ],
    }


def choices(selected=(), accepted=()):
    return {"selected": list(selected), "acceptedProprietary": list(accepted)}


@contextmanager
def root_owned_metadata():
    """Keep real type/mode checks while simulating root ownership on macOS."""
    original = Path.lstat

    def root_stat(path, *args, **kwargs):
        actual = original(path, *args, **kwargs)
        return SimpleNamespace(st_mode=actual.st_mode, st_uid=0)

    with patch.object(Path, "lstat", root_stat):
        yield


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.manifest = manifest_for()

    def test_defaults_are_available_open_source_and_automatic_only(self):
        for app in self.manifest["apps"]:
            if app["id"] in ("cursor", "unity"):
                app["default"] = True
        self.assertEqual(model.defaults(self.manifest), ["neovim", "firefox"])

    def test_empty_selection_is_valid(self):
        self.assertEqual(model.validate(self.manifest, choices()), choices())

    def test_valid_selection_is_sorted_without_mutating_input(self):
        value = choices(["neovim", "slack", "cursor"], ["slack", "cursor"])
        before = deepcopy(value)
        self.assertEqual(model.validate(self.manifest, value),
                         choices(["cursor", "neovim", "slack"], ["cursor", "slack"]))
        self.assertEqual(value, before)

    def test_unknown_and_injection_ids_are_rejected(self):
        for value in ("unknown", '${builtins.abort "injected"}', 'neovim"; }'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Unknown"):
                model.validate(self.manifest, choices([value]))

    def test_duplicate_selected_or_confirmation_ids_are_rejected(self):
        for value in (choices(["neovim", "neovim"]),
                      choices(["cursor"], ["cursor", "cursor"])):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "unique"):
                model.validate(self.manifest, value)

    def test_bad_record_shapes_are_rejected(self):
        for value in (None, [], {}, {"selected": []},
                      {**choices(), "extra": True},
                      {"selected": "neovim", "acceptedProprietary": []},
                      {"selected": [42], "acceptedProprietary": []},
                      {"selected": [], "acceptedProprietary": [None]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.validate(self.manifest, value)

    def test_unavailable_and_manual_choices_are_rejected(self):
        for app in ("unavailable", "unity", "chatgpt-web"):
            with self.subTest(app=app), self.assertRaisesRegex(ValueError, "cannot be installed"):
                model.validate(self.manifest, choices([app], [app] if app in ("unity", "chatgpt-web") else []))

    def test_manual_kind_remains_rejected_if_marked_available(self):
        next(app for app in self.manifest["apps"] if app["id"] == "unity")["available"] = True
        with self.assertRaisesRegex(ValueError, "cannot be installed"):
            model.validate(self.manifest, choices(["unity"], ["unity"]))

    def test_architecture_unavailable_is_rejected_with_system_reason(self):
        with self.assertRaisesRegex(ValueError, "aarch64-linux"):
            model.validate(manifest_for("aarch64-linux"), choices(["slack"], ["slack"]))
        self.assertEqual(model.validate(self.manifest, choices(["slack"], ["slack"])),
                         choices(["slack"], ["slack"]))

    def test_each_proprietary_choice_requires_confirmation(self):
        for selected in (["cursor"], ["slack"], ["cursor", "slack"]):
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "Confirm"):
                model.validate(self.manifest, choices(selected))

    def test_extra_unknown_or_open_source_confirmation_is_rejected(self):
        for accepted in (["neovim"], ["unknown"], ["cursor"]):
            with self.subTest(accepted=accepted), self.assertRaisesRegex(ValueError, "Confirm"):
                model.validate(self.manifest, choices(["neovim"], accepted))

    def test_optional_defaults_and_legacy_record_compatibility(self):
        self.assertEqual(model.validate(self.manifest, choices()), choices())
        value = {**choices(), "vpn": None, "gaming": {}}
        self.assertEqual(model.validate(self.manifest, value)["gaming"], gaming_defaults())
        enabled = model.validate(self.manifest, {**value, "gaming": {"enable": True}})["gaming"]
        self.assertTrue(enabled["gamemode"] and enabled["gamescope"])
        self.assertFalse(enabled["steam"] or enabled["maxMapCount"])

    def test_vpn_single_choice_and_native_architecture(self):
        for provider in (None, "mullvad", "proton", "ivpn", "networkmanager"):
            self.assertEqual(model.validate(self.manifest, {**choices(), "vpn": provider})["vpn"], provider)
        for provider in (["mullvad", "proton"], True, "unknown", '${builtins.abort "evil"}'):
            with self.subTest(provider=provider), self.assertRaises(ValueError):
                model.validate(self.manifest, {**choices(), "vpn": provider})
        with self.assertRaisesRegex(ValueError, "architecture"):
            model.validate(manifest_for("aarch64-linux"), {**choices(), "vpn": "ivpn"})
        self.assertFalse(next(item for item in providers("aarch64-linux") if item["id"] == "ivpn")["available"])

    def test_gaming_strict_shapes_and_dependencies(self):
        invalid = (None, [], {"enable": 1}, {"extra": False}, {"gamemode": True},
                   {"enable": False, "steam": True},
                   {"enable": True, "steamGamescopeSession": True},
                   {"enable": True, "gamescope": False, "steam": True, "steamGamescopeSession": True})
        for gaming in invalid:
            with self.subTest(gaming=gaming), self.assertRaises(ValueError):
                model.validate(self.manifest, {**choices(accepted=["steam"]), "gaming": gaming})

    def test_steam_requires_explicit_confirmation_and_x86(self):
        value = {**choices(), "gaming": {"enable": True, "steam": True}}
        with self.assertRaisesRegex(ValueError, "Confirm"):
            model.validate(self.manifest, value)
        value["acceptedProprietary"] = ["steam"]
        self.assertTrue(model.validate(self.manifest, value)["gaming"]["steam"])
        with self.assertRaisesRegex(ValueError, "x86_64"):
            model.validate(manifest_for("aarch64-linux"), value)
        with self.assertRaisesRegex(ValueError, "Confirm"):
            model.validate(self.manifest, {**choices(accepted=["steam"]), "gaming": {}})

    def test_gaming_render_emits_only_fixed_boolean_options(self):
        text = render_gaming({"enable": True, "steam": True, "steamGamescopeSession": True,
                              "maxMapCount": True}, "x86_64-linux")
        self.assertIn("nascent.gaming.steam.gamescopeSession.enable = true;", text)
        self.assertIn("nascent.gaming.tuning.maxMapCount.enable = true;", text)
        self.assertNotIn("allowUnfree", text)

    def test_password_managers_are_exclusive_before_install(self):
        for app in self.manifest["apps"][:2]:
            app["group"] = "Passwords"
        with self.assertRaisesRegex(ValueError, "at most one password manager"):
            model.validate(self.manifest, choices(["neovim", "firefox"]))
        self.assertEqual(model.validate(self.manifest, choices(["neovim"])), choices(["neovim"]))

    def test_digest_is_key_order_independent_and_content_sensitive(self):
        reordered = dict(reversed(list(self.manifest.items())))
        self.assertEqual(model.digest(self.manifest), model.digest(reordered))
        reordered["system"] = "aarch64-linux"
        self.assertNotEqual(model.digest(self.manifest), model.digest(reordered))

    def test_manifest_loader_checks_schema_system_ids_kind_and_availability(self):
        mutations = [
            lambda m: m.update(schemaVersion=2),
            lambda m: m.update(system="darwin"),
            lambda m: m.update(apps=[]),
            lambda m: m["apps"].append(deepcopy(m["apps"][0])),
            lambda m: m["apps"][0].update(id='${evil}'),
            lambda m: m["apps"][0].update(kind="script"),
            lambda m: m["apps"][0].update(available=1),
            lambda m: m["apps"][0].pop("available"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(self.manifest))
            self.assertEqual(model.load_manifest(path), self.manifest)
            for index, mutate in enumerate(mutations):
                invalid = deepcopy(self.manifest)
                mutate(invalid)
                path.write_text(json.dumps(invalid))
                with self.subTest(index=index), self.assertRaises(ValueError):
                    model.load_manifest(path)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.state = self.base / "state/software.json"
        self.manifest = manifest_for()
        self.manifest_path = self.base / "manifest.json"
        self.manifest_path.write_text(json.dumps(self.manifest))
        self.target = self.base / "target"
        self.nixos = self.target / "etc/nixos"
        self.nixos.mkdir(parents=True)
        catalog = self.nixos / "nascentos/installer/software-selection/catalog.json"
        catalog.parent.mkdir(parents=True)
        catalog.write_text(json.dumps({"nixpkgsRevision": self.manifest["nixpkgsRevision"]}))
        (self.nixos / "nascentos/flake.lock").write_text(json.dumps({
            "nodes": {"nixpkgs": {"locked": {"rev": self.manifest["nixpkgsRevision"]}}}}))
        self.config = self.nixos / "configuration.nix"
        self.original_config = "{ ... }: { imports = [ ./nascent-desktop.nix ]; }\n"
        self.config.write_text(self.original_config)

    def record(self, value=None):
        with patch.object(handoff.os, "geteuid", return_value=0), \
                patch.object(handoff, "host_system", return_value=self.manifest["system"]), \
                root_owned_metadata():
            handoff.record(self.manifest, choices(["neovim"]) if value is None else value, self.state)

    def load(self):
        with root_owned_metadata():
            return handoff.load_record(self.manifest, self.state)

    def install(self):
        with root_owned_metadata():
            handoff.install(self.target, self.config, self.manifest_path, self.state)

    def test_record_round_trip_binds_manifest_and_system_and_uses_private_mode(self):
        self.record(choices(["neovim", "cursor"], ["cursor"]))
        self.assertEqual(self.load(), choices(["cursor", "neovim"], ["cursor"]))
        raw = json.loads(self.state.read_text())
        self.assertEqual(raw["manifestDigest"], model.digest(self.manifest))
        self.assertEqual(raw["system"], self.manifest["system"])
        self.assertEqual(stat.S_IMODE(self.state.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.state.parent.stat().st_mode), 0o700)

    def test_record_requires_privilege_and_matching_host_architecture(self):
        with patch.object(handoff.os, "geteuid", return_value=501):
            with self.assertRaisesRegex(ValueError, "privilege helper"):
                handoff.record(self.manifest, choices(), self.state)
        with patch.object(handoff.os, "geteuid", return_value=0), \
                patch.object(handoff, "host_system", return_value="aarch64-linux"):
            with self.assertRaisesRegex(ValueError, "live system"):
                handoff.record(self.manifest, choices(), self.state)
        self.assertFalse(self.state.exists())

    def test_record_invalid_choice_does_not_create_state(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.record(choices(["evil"]))
        self.assertFalse(self.state.exists())

    def test_record_replaces_previous_state_without_leaving_temporary_files(self):
        self.record()
        self.record(choices())
        self.assertEqual(self.load(), choices())
        self.assertEqual([path.name for path in self.state.parent.iterdir()], ["software.json"])

    def test_load_rejects_digest_or_system_tampering(self):
        self.record()
        original = json.loads(self.state.read_text())
        for key, value in (("manifestDigest", "tampered"), ("system", "aarch64-linux")):
            self.state.write_text(json.dumps({**original, key: value}))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "catalog changed"):
                self.load()

    def test_load_revalidates_root_owned_records(self):
        self.record()
        raw = json.loads(self.state.read_text())
        for value in (choices(["unknown"]), choices(["cursor"]),
                      choices(["unity"], ["unity"]), choices(["neovim", "neovim"])):
            self.state.write_text(json.dumps({**raw, **value}))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.load()

    def test_state_file_rejects_public_permissions_and_symlink(self):
        self.record()
        for mode in (0o644, 0o620, 0o601):
            self.state.chmod(mode)
            with self.subTest(mode=oct(mode)), self.assertRaisesRegex(ValueError, "Unsafe software"):
                self.load()
        self.state.chmod(0o600)
        original = self.state.with_suffix(".original")
        self.state.rename(original)
        self.state.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "Unsafe software"):
            self.load()

    def test_state_file_rejects_nonroot_owner(self):
        self.record()
        original = Path.lstat

        def nonroot_state(path):
            result = original(path)
            return SimpleNamespace(st_mode=result.st_mode, st_uid=501 if path == self.state else 0)

        with patch.object(Path, "lstat", nonroot_state):
            with self.assertRaisesRegex(ValueError, "Unsafe software"):
                handoff.load_record(self.manifest, self.state)

    def test_directory_rejects_nonroot_writable_and_symlink_metadata(self):
        for mode, uid in ((stat.S_IFDIR | 0o700, 501),
                          (stat.S_IFDIR | 0o720, 0),
                          (stat.S_IFDIR | 0o702, 0),
                          (stat.S_IFLNK | 0o700, 0),
                          (stat.S_IFREG | 0o600, 0)):
            with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=mode, st_uid=uid)):
                with self.subTest(mode=oct(mode), uid=uid), \
                        self.assertRaisesRegex(ValueError, "Unsafe installer state directory"):
                    handoff.check_directory(self.state.parent)

    def test_install_writes_real_nix_module_import_and_auditable_receipt(self):
        self.record(choices(["neovim", "slack", "cursor"], ["cursor", "slack"]))
        self.install()
        self.assertEqual((self.nixos / "nascent-software.nix").read_text(),
                         '{ ... }: {\n'
                         '  imports = [ ./nascentos/installer/software-selection/integration.nix ];\n'
                         '  nascent.software.enable = true;\n'
                         '  nascent.software.selected = [ "cursor" "neovim" "slack" ];\n'
                         '}\n')
        self.assertEqual(self.config.read_text(), self.original_config.replace(
            "./nascent-desktop.nix", "./nascent-desktop.nix\n      ./nascent-software.nix\n      ./nascent-vpn.nix\n      ./nascent-gaming.nix"))
        receipt = json.loads((self.nixos / "nascent-software.json").read_text())
        self.assertEqual(receipt["acceptedProprietary"], ["cursor", "slack"])
        self.assertEqual(receipt["manifestDigest"], model.digest(self.manifest))
        self.assertEqual(receipt["system"], "x86_64-linux")

    def test_install_empty_selection_is_explicit(self):
        self.record(choices())
        self.install()
        self.assertIn("nascent.software.selected = [  ];", (self.nixos / "nascent-software.nix").read_text())

    def test_install_rejects_tampered_unknown_or_nix_injection_before_writes(self):
        self.record()
        raw = json.loads(self.state.read_text())
        for selected in (["unknown"], ['${builtins.abort "injected"}']):
            self.state.write_text(json.dumps({**raw, "selected": selected}))
            with self.subTest(selected=selected), self.assertRaisesRegex(ValueError, "Unknown"):
                self.install()
            self.assertEqual(self.config.read_text(), self.original_config)
            self.assertFalse((self.nixos / "nascent-software.nix").exists())

    def test_install_refuses_overwrite_of_either_existing_output(self):
        self.record()
        for name in ("nascent-software.nix", "nascent-software.json", "nascent-vpn.nix", "nascent-gaming.nix"):
            path = self.nixos / name
            path.write_text("keep me")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                self.install()
            self.assertEqual(path.read_text(), "keep me")
            self.assertEqual(self.config.read_text(), self.original_config)
            path.unlink()

    def test_install_refuses_dangling_output_symlink(self):
        self.record()
        (self.nixos / "nascent-software.nix").symlink_to(self.base / "missing")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            self.install()

    def test_install_refuses_missing_or_ambiguous_import_anchor(self):
        self.record()
        for text in ("{ imports = []; }", "./nascent-desktop.nix ./nascent-desktop.nix"):
            self.config.write_text(text)
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "import list"):
                self.install()
            self.assertEqual(self.config.read_text(), text)
            self.assertFalse((self.nixos / "nascent-software.nix").exists())
            self.assertFalse((self.nixos / "nascent-software.json").exists())

    def test_install_refuses_catalog_revision_mismatch(self):
        self.record()
        path = self.nixos / "nascentos/installer/software-selection/catalog.json"
        path.write_text(json.dumps({"nixpkgsRevision": "different"}))
        with self.assertRaisesRegex(ValueError, "revisions differ"):
            self.install()
        self.assertEqual(self.config.read_text(), self.original_config)
        self.assertFalse((self.nixos / "nascent-software.nix").exists())

    def test_install_refuses_actual_source_lock_revision_mismatch(self):
        self.record()
        path = self.nixos / "nascentos/flake.lock"
        path.write_text(json.dumps({"nodes": {"nixpkgs": {"locked": {"rev": "different"}}}}))
        with self.assertRaisesRegex(ValueError, "revision"):
            self.install()
        self.assertEqual(self.config.read_text(), self.original_config)
        self.assertFalse((self.nixos / "nascent-software.nix").exists())
        self.assertFalse((self.nixos / "nascent-software.json").exists())

    def test_optional_profiles_round_trip_into_target_modules(self):
        value = {**choices(accepted=["steam"]), "vpn": "mullvad",
                 "gaming": {"enable": True, "steam": True, "maxMapCount": True}}
        self.record(value)
        self.assertEqual(self.load(), model.validate(self.manifest, value))
        self.install()
        self.assertEqual((self.nixos / "nascent-vpn.nix").read_text(),
                         '{ ... }: { nascent.vpn.provider = "mullvad"; }\n')
        self.assertIn("nascent.gaming.steam.enable = true;", (self.nixos / "nascent-gaming.nix").read_text())
        self.assertIn("nascent.gaming.tuning.maxMapCount.enable = true;", (self.nixos / "nascent-gaming.nix").read_text())
        receipt = json.loads((self.nixos / "nascent-software.json").read_text())
        self.assertEqual(receipt["vpn"], "mullvad")
        self.assertTrue(receipt["gaming"]["steam"])
        self.assertEqual(receipt["acceptedProprietary"], ["steam"])

    def test_optional_state_tampering_fails_before_target_writes(self):
        self.record()
        raw = json.loads(self.state.read_text())
        for update in ({"vpn": "injected"}, {"gaming": {"enable": True, "steam": True}}):
            self.state.write_text(json.dumps({**raw, **update}))
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.install()
            self.assertEqual(self.config.read_text(), self.original_config)
            for name in ("nascent-software.nix", "nascent-vpn.nix", "nascent-gaming.nix"):
                self.assertFalse((self.nixos / name).exists())

    def test_legacy_selection_emits_disabled_optional_profiles(self):
        self.record()
        self.install()
        self.assertIn("nascent.vpn.provider = null;", (self.nixos / "nascent-vpn.nix").read_text())
        text = (self.nixos / "nascent-gaming.nix").read_text()
        self.assertIn("nascent.gaming.enable = false;", text)
        self.assertNotIn("= true", text)

    def test_atomic_write_failure_preserves_old_file_and_cleans_temporary(self):
        path = self.base / "atomic"
        path.write_text("original")
        before = set(self.base.iterdir())
        with patch.object(handoff.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                handoff.atomic_write(path, "replacement")
        self.assertEqual(path.read_text(), "original")
        self.assertEqual(set(self.base.iterdir()), before)


if __name__ == "__main__":
    unittest.main()
