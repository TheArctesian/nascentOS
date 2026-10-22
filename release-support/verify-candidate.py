#!/usr/bin/env python3
"""Check both architecture bundles before creating a draft."""
import hashlib
import json
from pathlib import Path
import sys
from package import digest, SYSTEMS


def verify(directory, tag, revision):
    directory = Path(directory)
    expected = set()
    notes = [f'# nascentOS {tag} release candidate', '', f'Source commit: `{revision}`.', '',
             'Automated source/CLI, configuration/profile, VM/ISO build and native NixOS boot gates passed.',
             '**Not release ready:** graphical desktop and disposable-disk installation/reboot gates remain pending.',
             'Hardware-specific graphics, firmware and suspend behavior also remain unverified.', '',
             'Complete docs/testing.md gates for both image hashes below before manually publishing this draft.', '']
    lock_hashes = set()
    for system in SYSTEMS:
        stem = f'nascentos-{tag}-{system}'
        manifest_name = f'{stem}.manifest.json'
        manifest = json.loads((directory / manifest_name).read_text())
        if (manifest['tag'], manifest['source_revision'], manifest['system']) != (tag, revision, system):
            raise ValueError('Candidate source identity mismatch')
        if manifest['release_ready'] is not False:
            raise ValueError('Candidate must retain pending manual gates')
        for gate in ('source_and_cli', 'configuration_profiles', 'vm_and_iso_build', 'nixos_boot'):
            if manifest['gates'][gate] != 'passed':
                raise ValueError(f'Automated gate did not pass: {gate}')
        checksum_name = f'{stem}.SHA256SUMS'
        expected.add(checksum_name)
        checked = set()
        for line in (directory / checksum_name).read_text().splitlines():
            sha, name = line.split('  ', 1)
            if Path(name).name != name or name in checked:
                raise ValueError('Unsafe or duplicate checksum path')
            if digest(directory / name) != sha:
                raise ValueError(f'Checksum mismatch: {name}')
            checked.add(name)
        image = manifest['image']
        required = {manifest_name, manifest['flake_lock_asset']} | {p['name'] for p in image['parts']}
        if checked != required:
            raise ValueError('Checksum inventory differs from manifest')
        combined = hashlib.sha256()
        total = 0
        for part in image['parts']:
            path = directory / part['name']
            if path.stat().st_size != part['bytes'] or digest(path) != part['sha256']:
                raise ValueError('Image part mismatch')
            with path.open('rb') as stream:
                while chunk := stream.read(1024**2):
                    combined.update(chunk)
                    total += len(chunk)
        if combined.hexdigest() != image['sha256'] or total != image['bytes']:
            raise ValueError('Reassembled ISO identity mismatch')
        if digest(directory / manifest['flake_lock_asset']) != manifest['flake_lock_sha256']:
            raise ValueError('Lock identity mismatch')
        lock_hashes.add(manifest['flake_lock_sha256'])
        expected.update(checked)
        notes.extend([f'## {system}', '', f'ISO SHA-256: `{image["sha256"]}`.', '',
                      f'Output: `{manifest["nix_output"]}`.', ''])
        if len(image['parts']) > 1:
            notes.extend(['Download all numbered parts, then reconstruct in order:', '', '```sh',
                          f'cat {image["name"]}.part* > {image["name"]}', '```', ''])
        notes.extend(['Verify the downloaded assets first:', '', '```sh',
                      f'sha256sum -c {stem}.SHA256SUMS', '```', ''])
    if len(lock_hashes) != 1:
        raise ValueError('Architectures used different flake locks')
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError('Unexpected candidate files')
    return '\n'.join(notes)


if __name__ == '__main__':
    Path('release-notes.md').write_text(verify(*sys.argv[1:]))
