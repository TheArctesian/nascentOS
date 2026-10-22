#!/usr/bin/env python3
"""Validate the adapter against an unpacked pinned source, without modifying it."""
import argparse
import hashlib
from pathlib import Path
import shutil
import tempfile
from apply import apply

parser = argparse.ArgumentParser(__doc__)
parser.add_argument('source', type=Path)
args = parser.parse_args()
with tempfile.TemporaryDirectory(prefix='nascent-layout-check-') as directory:
    source = Path(directory)
    shutil.copytree(args.source, source, dirs_exist_ok=True)
    # Nix store sources are read-only; make only the disposable copy writable.
    for path in source.rglob('*'):
        if path.is_file() or path.is_dir():
            path.chmod(path.stat().st_mode | 0o200)
    apply(source)
    changed = []
    for path in source.rglob('*'):
        if path.is_file():
            relative = path.relative_to(source)
            original = args.source / relative
            if not original.exists() or path.read_bytes() != original.read_bytes():
                changed.append(str(relative))
    expected = {
        'src/calamares/CalamaresWindow.cpp',
        'src/calamares/progresstree/ProgressTreeDelegate.cpp',
        'src/calamares/progresstree/ProgressTreeView.cpp',
        'src/libcalamaresui/ViewManager.cpp',
        'src/libcalamaresui/viewpages/ExecutionViewStep.cpp',
        'src/libcalamaresui/viewpages/Slideshow.cpp',
        'src/libcalamaresui/NascentLayout.h',
    }
    assert set(changed) == expected, changed
    snapshot = {str(p): hashlib.sha256(p.read_bytes()).digest() for p in source.rglob('*') if p.is_file()}
    try:
        apply(source)
    except ValueError:
        pass
    else:
        raise AssertionError('Already-patched source must fail closed')
    assert snapshot == {str(p): hashlib.sha256(p.read_bytes()).digest() for p in source.rglob('*') if p.is_file()}
    print('PASS: pinned source anchors, exact presentation-only changed paths, atomic drift rejection')
