import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from package import package, digest, SYSTEMS
from resolve import resolve

spec = importlib.util.spec_from_file_location('candidate', Path(__file__).with_name('verify-candidate.py'))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class ReleaseTests(unittest.TestCase):
    def test_tag_rejects_injection_and_missing_tag(self):
        for tag in ('main', 'v1', 'v1.0.0\nfoo=bar', 'v1.0.0;echo bad', '--help'):
            with self.assertRaises(ValueError):
                resolve(tag)
        with patch('resolve.subprocess.check_output', return_value='a' * 40 + '\n') as git:
            self.assertEqual(resolve('v1.2.3-rc.1'), 'a' * 40)
            self.assertEqual(git.call_args.args[0][-1], 'refs/tags/v1.2.3-rc.1^{commit}')

    def test_split_reassemble_and_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            iso = root / 'input.iso'
            iso.write_bytes(b'example installer bytes')
            lock = root / 'flake.lock'
            lock.write_text(json.dumps({'version': 7, 'nodes': {}}))
            bundle = root / 'bundle'
            bundle.mkdir()
            for index, system in enumerate(SYSTEMS):
                output = root / system
                manifest = package(iso, lock, output, 'v1.0.0', 'a'*40, system,
                                   '/nix/store/example', part_bytes=4 if index == 0 else 100)
                self.assertEqual(manifest['image']['sha256'], digest(iso))
                self.assertFalse(manifest['release_ready'])
                for file in output.iterdir():
                    file.rename(bundle / file.name)
            notes = candidate.verify(bundle, 'v1.0.0', 'a'*40)
            self.assertIn('Not release ready', notes)
            self.assertIn('.part*', notes)
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
            with self.assertRaisesRegex(ValueError, 'Automated gate did not pass'):
                candidate.verify(bundle, 'v1.0.0', 'a'*40)
            manifest_path.write_text(original)
            part = next(bundle.glob('*.part0000'))
            part.write_bytes(b'bad')
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
