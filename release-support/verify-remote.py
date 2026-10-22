#!/usr/bin/env python3
"""Check GitHub's uploaded asset inventory and server-computed SHA-256 digests."""
import argparse
import json
from pathlib import Path
from package import digest


def verify(directory, release):
    files = {p.name: p for p in Path(directory).iterdir() if p.is_file()}
    assets = release['assets']
    if len(assets) != len({a['name'] for a in assets}):
        raise ValueError('Duplicate remote asset names')
    if set(files) != {a['name'] for a in assets}:
        raise ValueError('Remote asset inventory differs from verified bundle')
    for asset in assets:
        path = files[asset['name']]
        if asset['state'] != 'uploaded' or asset['size'] != path.stat().st_size:
            raise ValueError('Remote asset incomplete: ' + asset['name'])
        if asset.get('digest') != 'sha256:' + digest(path):
            raise ValueError('Remote SHA-256 differs or is unavailable: ' + asset['name'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory')
    parser.add_argument('release_json')
    args = parser.parse_args()
    verify(args.directory, json.loads(Path(args.release_json).read_text()))
    print('All uploaded asset sizes and GitHub SHA-256 digests match.')
