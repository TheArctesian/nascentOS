#!/usr/bin/env python3
"""Create bounded GitHub Release assets with a whole-image identity."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

PART_BYTES = 1024**3  # Strictly below GitHub's per-asset 2 GiB limit.
SYSTEMS = ('aarch64-linux', 'x86_64-linux')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def package(iso, lock, output, tag, revision, system, store_path, part_bytes=PART_BYTES):
    if system not in SYSTEMS or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Invalid system or source revision')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9][A-Za-z0-9.-]*)?', tag):
        raise ValueError('Invalid release tag')
    iso, lock, output = Path(iso), Path(lock), Path(output)
    if not iso.stat().st_size:
        raise ValueError('Empty ISO')
    # Validate the lock rather than silently packaging a nonexistent source pin.
    json.loads(lock.read_text())
    output.mkdir(parents=True, exist_ok=False)
    stem = f'nascentos-{tag}-{system}'
    image_name = f'{stem}.iso'
    assets = []
    if iso.stat().st_size <= part_bytes:
        shutil.copyfile(iso, output / image_name)
        assets.append(output / image_name)
    else:
        with iso.open('rb') as source:
            index = 0
            while True:
                chunk = source.read(part_bytes)
                if not chunk:
                    break
                target = output / f'{image_name}.part{index:04d}'
                target.write_bytes(chunk)
                assets.append(target)
                index += 1
    lock_name = f'{stem}.flake.lock'
    shutil.copyfile(lock, output / lock_name)
    manifest = {
        'schema': 1, 'tag': tag, 'source_revision': revision, 'system': system,
        'flake_lock_sha256': digest(lock), 'flake_lock_asset': lock_name,
        'nix_output': f'packages.{system}.installer', 'store_path': store_path,
        'image': {'name': image_name, 'bytes': iso.stat().st_size, 'sha256': digest(iso),
                  'parts': [{'name': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)}
                            for p in assets]},
        'gates': {'source_and_cli': 'passed', 'configuration_profiles': 'passed',
                  'vm_and_iso_build': 'passed', 'nixos_boot': 'passed',
                  'graphical_desktop': 'pending', 'installer_disk_and_reboot': 'pending',
                  'physical_hardware': 'pending'},
        'release_ready': False,
    }
    manifest_path = output / f'{stem}.manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    assets.extend([output / lock_name, manifest_path])
    (output / f'{stem}.SHA256SUMS').write_text(''.join(
        f'{digest(p)}  {p.name}\n' for p in sorted(assets)))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('tag', 'revision', 'system', 'iso-dir', 'lock', 'store-path', 'output'):
        parser.add_argument(f'--{name}', required=True)
    args = parser.parse_args()
    images = list(Path(args.iso_dir).glob('*.iso'))
    if len(images) != 1:
        raise SystemExit('Expected exactly one installer ISO')
    package(images[0], args.lock, args.output, args.tag, args.revision, args.system, args.store_path)
