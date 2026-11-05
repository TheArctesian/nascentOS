#!/usr/bin/env python3
"""Derive the build version from the first-parent commit count of a main revision.

The count is read as MAJOR, MINOR, PATCH with two decimal digits each for
MINOR and PATCH: 6 -> v0.0.6, 100 -> v0.1.0, 3222222 -> v322.22.22.
"""
import re
import subprocess
import sys


def format_version(count):
    return f'v{count // 10000}.{count // 100 % 100}.{count % 100}'


def version_number(tag):
    match = re.fullmatch(r'v([0-9]+)\.([0-9]{1,2})\.([0-9]{1,2})', tag)
    if not match:
        raise ValueError(f'Not a build version: {tag}')
    major, minor, patch = map(int, match.groups())
    return major * 10000 + minor * 100 + patch


def version(revision='HEAD'):
    sha = subprocess.check_output(
        ['git', 'rev-parse', '--verify', f'{revision}^{{commit}}'], text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Expected a Git SHA-1 revision')
    count = subprocess.check_output(
        ['git', 'rev-list', '--count', '--first-parent', sha], text=True).strip()
    if not count.isdigit() or int(count) < 1:
        raise ValueError('Expected a positive commit count; fetch full history')
    return format_version(int(count)), sha


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--number':
        print(version_number(sys.argv[2]))
        sys.exit()
    tag, sha = version(sys.argv[1] if len(sys.argv) > 1 else 'HEAD')
    print(f'revision={sha}\ntag={tag}')
