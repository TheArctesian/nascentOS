"""Offline installer checks: fixture sysfs and temporary install targets only."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get('NASCENT_SOURCE', Path(__file__).resolve().parents[1]))


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, SOURCE / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


hardware = load('hardware', 'lib/hardware.py')
install = load('install_target', 'lib/install_target.py')
extension = load('patch_extension', 'modules/installer/patch-extension.py')


class HardwareTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def device(self, slot, vendor, ident, kind='0x030000'):
        directory = self.root / 'bus/pci/devices' / slot
        directory.mkdir(parents=True)
        for name, value in (('class', kind), ('vendor', vendor), ('device', ident)):
            (directory / name).write_text(value)

    def test_only_display_classes_and_actual_vendor_are_used(self):
        self.device('0000:01:00.0', '0x1002', '0x73bf')
        self.device('0000:02:00.0', '0x8086', '0x9a49', '0x038000')
        self.device('0000:03:00.0', '0x10de', '0x2206', '0x040300')
        self.device('broken', 'not-hex', '0x0000')
        report = hardware.scan(self.root, 'x86_64')
        self.assertEqual([(gpu['vendor'], gpu['device']) for gpu in report['gpus']],
                         [('1002', '73bf'), ('8086', '9a49')])
        self.assertEqual(report['recommended'], 'generic')
        self.assertFalse(any('NVIDIA' in warning for warning in report['warnings']))

    def test_modern_and_older_nvidia_recommendations(self):
        self.device('0000:01:00.0', '0x10de', '0x2206')
        self.assertEqual(hardware.scan(self.root, 'x86_64')['recommended'], 'nvidia-open')
        self.assertEqual(hardware.scan(self.root, 'aarch64')['recommended'], 'generic')
        self.device('0000:02:00.0', '0x10de', '0x1b80')
        report = hardware.scan(self.root, 'x86_64')
        self.assertEqual(report['recommended'], 'generic')
        self.assertTrue(any('Older/unknown' in warning for warning in report['warnings']))

    def test_hybrid_requires_review(self):
        self.device('0000:01:00.0', '0x10de', '0x2206')
        self.device('0000:00:02.0', '0x8086', '0x9a49')
        report = hardware.scan(self.root, 'x86_64')
        self.assertTrue(any('Hybrid graphics' in warning and 'bus IDs' in warning
                            for warning in report['warnings']))

    def test_arm_device_tree_platforms_and_unknown_architecture(self):
        compatible = self.root / 'firmware/devicetree/base/compatible'
        compatible.parent.mkdir(parents=True)
        for value, family in (('apple,j274\0apple,t8103\0', 'apple-silicon'),
                              ('qcom,sc8280xp\0', 'qualcomm'), ('linux,dummy-virt\0', 'generic')):
            with self.subTest(family=family):
                compatible.write_text(value)
                report = hardware.scan(self.root, 'arm64')
                self.assertEqual(report['system'], 'aarch64-linux')
                self.assertEqual(report['family'], family)
                if family != 'generic':
                    self.assertTrue(any('platform-specific' in warning for warning in report['warnings']))
        self.assertIsNone(hardware.scan(self.root, 'riscv64')['system'])

    def test_profile_validation_auto_selection_and_no_overwrite(self):
        report = hardware.scan(self.root, 'x86_64')
        target = self.root / 'generated'
        with self.assertRaises(ValueError):
            hardware.write_profile(target, report, 'unexpected')
        self.assertFalse(target.exists())
        self.assertEqual(hardware.write_profile(target, report, 'auto'), 'generic')
        before = {path.name: path.read_bytes() for path in target.iterdir()}
        with self.assertRaises(ValueError):
            hardware.write_profile(target, report, 'nvidia-open')
        self.assertEqual(before, {path.name: path.read_bytes() for path in target.iterdir()})
        self.assertEqual(json.loads((target / 'nascent-hardware.json').read_text())['selected'], 'generic')
        self.assertNotIn('nvidia', (target / 'nascent-hardware.nix').read_text())

    def test_profile_refuses_existing_summary_or_dangling_symlink(self):
        report = hardware.scan(self.root, 'x86_64')
        for name in ('nascent-hardware.nix', 'nascent-hardware.json'):
            for symlink in (False, True):
                with self.subTest(name=name, symlink=symlink):
                    target = self.root / (name + str(symlink))
                    target.mkdir()
                    path = target / name
                    if symlink:
                        path.symlink_to(target / 'missing')
                    else:
                        path.write_text('personal')
                    with self.assertRaises(ValueError):
                        hardware.write_profile(target, report, 'generic')
                    self.assertEqual(list(target.iterdir()), [path])


class InstallTargetTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.target = self.root / 'target/etc/nixos'
        self.target.mkdir(parents=True)
        self.config = self.target / 'configuration.nix'
        self.generated = '''{ ... }: {
  imports = [ ./hardware-configuration.nix ];
  users.users.alice = { isNormalUser = true; extraGroups = [ "wheel" ]; };
  boot.loader.systemd-boot.enable = true;
  networking.hostName = "my-machine";
}
'''
        self.config.write_text(self.generated)
        self.hardware_config = self.target / 'hardware-configuration.nix'
        self.hardware_config.write_text('# generated disks and hardware\n{ fileSystems."/".device = "/dev/disk/by-uuid/example"; }\n')
        self.source = self.root / 'source'
        (self.source / 'modules').mkdir(parents=True)
        (self.source / 'modules/default.nix').write_text('# actual desktop module fixture\n')
        self.revision = 'a' * 40
        self.lock = {'nodes': {'nixpkgs': {'locked': {'rev': self.revision}}}}
        (self.source / 'flake.lock').write_text(json.dumps(self.lock))
        self.choice = {'profile': 'generic', 'report': hardware.scan(self.root / 'sys', 'x86_64')}

    def prepare(self):
        install.prepare(self.root / 'target', self.config, self.source, self.choice)

    def test_prepare_preserves_generated_settings_and_propagates_pinned_desktop(self):
        hardware_before = self.hardware_config.read_bytes()
        self.prepare()
        updated = self.config.read_text()
        added = '\n      ./nascentos/modules\n      ./nascent-desktop.nix\n      ./nascent-hardware.nix'
        self.assertEqual(updated.replace(added, ''), self.generated)
        self.assertEqual(self.hardware_config.read_bytes(), hardware_before)
        self.assertEqual((self.target / 'nascentos/modules/default.nix').read_bytes(),
                         (self.source / 'modules/default.nix').read_bytes())
        flake = (self.target / 'flake.nix').read_text()
        self.assertIn('github:NixOS/nixpkgs/' + self.revision, flake)
        self.assertIn('system = "x86_64-linux"', flake)
        self.assertIn('modules = [ ./configuration.nix ]', flake)
        self.assertEqual((self.target / 'flake.lock').read_bytes(), (self.source / 'flake.lock').read_bytes())
        desktop = (self.target / 'nascent-desktop.nix').read_text()
        self.assertIn('nascent.desktop.enable = true', desktop)
        self.assertIn('nascent-session', desktop)
        self.assertIn('services.greetd.enable = true', desktop)

    def test_prepare_refuses_existing_owned_files_without_touching_generated_config(self):
        for name in ('nascentos', 'nascent-desktop.nix', 'nascent-hardware.nix',
                     'nascent-hardware.json', 'flake.nix', 'flake.lock'):
            with self.subTest(name=name):
                existing = self.target / name
                existing.write_text('personal')
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertEqual(existing.read_text(), 'personal')
                self.assertEqual(self.config.read_text(), self.generated)
                self.assertEqual(sorted(path.name for path in self.target.iterdir()),
                                 sorted(['configuration.nix', 'hardware-configuration.nix', name]))
                existing.unlink()

    def test_prepare_refuses_platforms_and_unexpected_config_before_writes(self):
        for system, family in (('riscv64-linux', 'generic'), ('aarch64-linux', 'apple-silicon')):
            with self.subTest(system=system, family=family):
                self.choice['report'].update(system=system, family=family)
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertFalse((self.target / 'nascentos').exists())
        self.choice['report'].update(system='aarch64-linux', family='generic')
        self.config.write_text('{ imports = []; }')
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse((self.target / 'nascentos').exists())

    def test_invalid_profile_or_pin_leaves_target_untouched(self):
        before = {path.name: path.read_bytes() for path in self.target.iterdir()}
        for profile, revision in (('unexpected', self.revision),
                                  ('generic', 'main'),
                                  ('generic', 'a' * 39),
                                  ('generic', 'a' * 40 + '\n')):
            with self.subTest(profile=profile, revision=revision):
                self.choice['profile'] = profile
                self.lock['nodes']['nixpkgs']['locked']['rev'] = revision
                (self.source / 'flake.lock').write_text(json.dumps(self.lock))
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertEqual(before, {path.name: path.read_bytes()
                                          for path in self.target.iterdir()})


class CalamaresPatchTests(unittest.TestCase):
    def test_checked_patch_of_pinned_extension(self):
        nixpkgs = Path(os.environ.get('NIXPKGS_SOURCE', '/nix/store/x605rbj3d9bjxd3zdnqy0iphq7g6ly50-source'))
        source = nixpkgs / 'pkgs/by-name/ca/calamares-nixos-extensions/src/modules/nixos/main.py'
        self.assertTrue(source.is_file(), 'Environment failure: provide pinned NIXPKGS_SOURCE for Calamares patch test')
        original = source.read_text()
        patched = extension.patch(original)
        tree = ast.parse(patched)
        prepare_calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                         and isinstance(node.func, ast.Name) and node.func.id == 'prepare']
        self.assertEqual(len(prepare_calls), 1)
        self.assertEqual([node.id for node in prepare_calls[0].args], ['root_mount_point', 'config'])
        commands = [node for node in ast.walk(tree) if isinstance(node, ast.List)
                    and any(isinstance(item, ast.Constant) and item.value == 'nixos-install' for item in node.elts)]
        self.assertEqual(len(commands), 1)
        values = commands[0].elts
        start = next(index for index, value in enumerate(values)
                     if isinstance(value, ast.Constant) and value.value == 'nixos-install')
        self.assertEqual(values[start + 1].value, '--flake')
        target = values[start + 2]
        self.assertIsInstance(target, ast.BinOp)
        self.assertEqual(target.left.id, 'root_mount_point')
        self.assertEqual(target.right.value, '/etc/nixos#nascent')
        self.assertIn('services.greetd.settings.initial_session', patched)
        self.assertNotIn('services.displayManager.autoLogin.enable', patched)
        with self.assertRaises(ValueError):
            extension.patch(patched)
        with self.assertRaises(ValueError):
            extension.patch(original.replace('import re\n', ''))


if __name__ == '__main__':
    unittest.main()
