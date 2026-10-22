#!/usr/bin/env python3
"""Merge reviewed mail entries into an assembly copy of the picker catalog."""
import json
from pathlib import Path
import sys


def merge(base, mail):
    if base['schemaVersion'] != mail['schemaVersion'] or base['nixpkgsRevision'] != mail['nixpkgsRevision']:
        raise ValueError('Catalog schema/pin mismatch; review package metadata first')
    ids = [app['id'] for app in base['apps'] + mail['apps']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate software IDs; catalog already merged or needs review')
    return {**base, 'apps': base['apps'] + mail['apps']}


if __name__ == '__main__':
    target = Path(sys.argv[1])
    mail = json.loads(Path(__file__).with_name('catalog.json').read_text())
    result = merge(json.loads(target.read_text()), mail)
    target.write_text(json.dumps(result, indent=2) + '\n')
