#!/usr/bin/env python3
"""Verify the explicitly requested architecture bundles before publication."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from package import digest, SYSTEMS


def verify(directory, tag, revision, systems=SYSTEMS):
    directory = Path(directory)
    if not systems or len(set(systems)) != len(systems) or set(systems) - set(SYSTEMS):
        raise ValueError('Invalid expected architectures')
    expected = set()
    notes = [f'# nascentOS {tag} preview', '', f'Source commit: `{revision}`.', '',
             'Automated source/CLI checks, configuration/profile checks and the production installer ISO build passed.',
             '**Not release ready:** this is an experimental prerelease, not a stable hardware installer.',
             'Only the architectures listed below are included. No unbuilt x86 image is advertised.',
             'The earlier ARM development image passed graphical installation, installed-disk boot, password login,',
             'selected-app/keyring checks and logout; that evidence does not certify this new ISO hash.',
             'See docs/validation.md for the exact tested development-image identity.',
             'Graphical installation of these release bytes, physical graphics/firmware, audio and suspend remain unverified.', '',
             'Download every image part and the matching lock, manifest and SHA256SUMS file.', '']
    lock_hashes = set()
    for system in systems:
        stem = f'nascentos-{tag}-{system}'
        manifest_name = f'{stem}.manifest.json'
        manifest = json.loads((directory / manifest_name).read_text())
        if (manifest['tag'], manifest['source_revision'], manifest['system']) != (tag, revision, system):
            raise ValueError('Candidate source identity mismatch')
        if manifest['release_ready'] is not False:
            raise ValueError('Candidate must retain pending manual gates')
        for gate in ('source_and_cli', 'configuration_profiles', 'iso_build'):
            if manifest['gates'][gate] != 'passed':
                raise ValueError(f'Automated gate did not pass: {gate}')
        if manifest['gates']['nixos_boot'] not in ('passed', 'not-run'):
            raise ValueError('Invalid boot test status')
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
                      f'Output: `{manifest["nix_output"]}` (normal production compression).',
                      f'Native NixOS boot test: **{manifest["gates"]["nixos_boot"]}**.', ''])
        if len(image['parts']) > 1:
            notes.extend(['Download all numbered parts, then reconstruct in order:', '', '```sh',
                          f'cat {image["name"]}.part* > {image["name"]}', '```', ''])
        notes.extend(['Verify the downloaded assets (Linux; use `shasum -a 256 -c` on macOS):', '', '```sh',
                      f'sha256sum -c {stem}.SHA256SUMS', '```', ''])
        notes.extend(['Verify the reconstructed whole ISO:', '', '```sh',
                      f'echo "{image["sha256"]}  {image["name"]}" | sha256sum -c -', '```', ''])
    if len(lock_hashes) != 1:
        raise ValueError('Architectures used different flake locks')
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError('Unexpected candidate files')
    return '\n'.join(notes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('tag')
    parser.add_argument('revision')
    parser.add_argument('--systems', nargs='+', choices=SYSTEMS, default=list(SYSTEMS))
    args = parser.parse_args()
    Path('release-notes.md').write_text(verify(args.directory, args.tag, args.revision, args.systems))
