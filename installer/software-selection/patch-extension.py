"""Patch the already nascentOS-patched pinned Calamares extension, fail closed."""
import ast
from pathlib import Path
import sys


def patch(text, manifest):
    if "from nascent_software import" in text or "install_software(" in text:
        raise ValueError("Calamares software handoff was already patched")
    before = "from nascent_install import prepare\n"
    after = before + "from nascent_software import install as install_software\n"
    call = "        prepare(root_mount_point, config)\n"
    replacement = call + f"        install_software(root_mount_point, config, {str(manifest)!r})\n"
    for old, new in ((before, after), (call, replacement)):
        if text.count(old) != 1:
            raise ValueError("Calamares software handoff anchor changed or was already patched")
        text = text.replace(old, new)
    ast.parse(text)
    return text


if __name__ == "__main__":
    source, manifest_path = Path(sys.argv[1]), Path(sys.argv[2])
    main = source / "modules/nixos/main.py"
    main.write_text(patch(main.read_text(), manifest_path))
