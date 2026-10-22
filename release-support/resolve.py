#!/usr/bin/env python3
"""Resolve an existing immutable source tag without shell interpolation."""
import re
import subprocess
import sys


def resolve(tag):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9][A-Za-z0-9.-]*)?", tag):
        raise ValueError("Expected vMAJOR.MINOR.PATCH, optionally with a prerelease suffix")
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], text=True
    ).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected a Git SHA-1 revision")
    return revision


if __name__ == "__main__":
    print(f"revision={resolve(sys.argv[1])}\ntag={sys.argv[1]}")
