import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from package import package, digest, SYSTEMS
from version import format_version, version, version_number

spec = importlib.util.spec_from_file_location('candidate', Path(__file__).with_name('verify-candidate.py'))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class ReleaseTests(unittest.TestCase):
    def test_single_architecture_and_honest_boot_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso, lock = root / 'input.iso', root / 'flake.lock'
            iso.write_bytes(b'ISO fixture')
            lock.write_text('{}')
            out = root / 'bundle'
            manifest = package(iso, lock, out, 'v0.1.0-alpha.1', 'a'*40,
                               'aarch64-linux', '/nix/store/example')
            self.assertEqual(manifest['gates']['nixos_boot'], 'not-run')
            notes = candidate.verify(out, 'v0.1.0-alpha.1', 'a'*40, ['aarch64-linux'])
            self.assertIn('**not-run**', notes)
            with self.assertRaises(FileNotFoundError):
                candidate.verify(out, 'v0.1.0-alpha.1', 'a'*40)
            with self.assertRaisesRegex(ValueError, 'Invalid expected architectures'):
                candidate.verify(out, 'v0.1.0-alpha.1', 'a'*40, [])

    def test_version_counts_first_parent_commits(self):
        def git(args, text):
            return 'a' * 40 + '\n' if args[1] == 'rev-parse' else '6\n'
        with patch('version.subprocess.check_output', side_effect=git) as call:
            self.assertEqual(version(), ('v0.0.6', 'a' * 40))
            self.assertIn('--first-parent', call.call_args.args[0])
        with patch('version.subprocess.check_output', side_effect=['a' * 40, '0']):
            with self.assertRaises(ValueError):
                version()
        with patch('version.subprocess.check_output', return_value='not-a-sha'):
            with self.assertRaises(ValueError):
                version()

    def test_version_digits_roll_over_every_hundred(self):
        for count, tag in ((1, 'v0.0.1'), (6, 'v0.0.6'), (99, 'v0.0.99'), (100, 'v0.1.0'),
                           (101, 'v0.1.1'), (9999, 'v0.99.99'), (10000, 'v1.0.0'),
                           (3222222, 'v322.22.22')):
            with self.subTest(count=count):
                self.assertEqual(format_version(count), tag)
                self.assertEqual(version_number(tag), count)
        for bad in ('v0.0.100', 'v1.2', '1.2.3', 'v1.2.3\nx'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                version_number(bad)

    def test_unsplit_by_default_with_download_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso, lock = root / 'input.iso', root / 'flake.lock'
            iso.write_bytes(b'x' * 4096)
            lock.write_text('{}')
            out = root / 'bundle'
            manifest = package(iso, lock, out, 'v0.0.6', 'a'*40, 'x86_64-linux', '/nix/store/example')
            self.assertEqual([p['name'] for p in manifest['image']['parts']],
                             ['nascentos-v0.0.6-x86_64-linux.iso'])
            notes = candidate.verify(out, 'v0.0.6', 'a'*40, ['x86_64-linux'], 'https://iso.example')
            self.assertIn('https://iso.example/v0.0.6/nascentos-v0.0.6-x86_64-linux.iso', notes)
            self.assertNotIn('.part*', notes)

    def test_two_architectures_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso = root / 'input.iso'
            iso.write_bytes(b'example installer bytes')
            lock = root / 'flake.lock'
            lock.write_text(json.dumps({'version': 7, 'nodes': {}}))
            bundle = root / 'bundle'
            bundle.mkdir()
            for system in SYSTEMS:
                output = root / system
                manifest = package(iso, lock, output, 'v1.0.0', 'a'*40, system, '/nix/store/example')
                self.assertEqual(manifest['image']['sha256'], digest(iso))
                self.assertFalse(manifest['release_ready'])
                for file in output.iterdir():
                    file.rename(bundle / file.name)
            notes = candidate.verify(bundle, 'v1.0.0', 'a'*40)
            self.assertIn('Not release ready', notes)
            with self.assertRaises(ValueError):
                candidate.verify(bundle, 'v1.0.0', 'b'*40)
            unexpected = bundle / 'unexpected.txt'
            unexpected.write_text('extra')
            with self.assertRaisesRegex(ValueError, 'Unexpected candidate files'):
                candidate.verify(bundle, 'v1.0.0', 'a'*40)
            unexpected.unlink()
            manifest_path = next(bundle.glob('*.manifest.json'))
            original = manifest_path.read_text()
            changed = json.loads(original)
            changed['gates']['nixos_boot'] = 'pending'
            manifest_path.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'Invalid boot test status'):
                candidate.verify(bundle, 'v1.0.0', 'a'*40)
            manifest_path.write_text(original)
            next(bundle.glob('*.iso')).write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                candidate.verify(bundle, 'v1.0.0', 'a'*40)

    def test_empty_image_and_existing_directory_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso, lock = root / 'a.iso', root / 'flake.lock'
            iso.touch()
            lock.write_text('{}')
            args = (iso, lock, root / 'out', 'v1.0.0', 'a'*40, SYSTEMS[0], '/nix/store/example')
            with self.assertRaisesRegex(ValueError, 'Empty ISO'):
                package(*args)
            iso.write_bytes(b'iso')
            package(*args)
            with self.assertRaises(FileExistsError):
                package(*args)
