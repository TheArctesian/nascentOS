"""Root-owned software state and Calamares target configuration handoff."""
import argparse
import json
import os
from pathlib import Path
import platform
import stat
import sys
import tempfile

from nascent_software_model import digest, load_manifest, validate
from nascent_optional_profiles import gaming_defaults, render_gaming, render_vpn

STATE = Path("/run/nascent-installer/software.json")


def host_system():
    return {"x86_64": "x86_64-linux", "aarch64": "aarch64-linux"}.get(platform.machine())


def check_directory(directory):
    metadata = directory.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != 0
            or metadata.st_mode & 0o022):
        raise ValueError("Unsafe installer state directory")


def atomic_write(path, text):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as out:
            temporary = Path(out.name)
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def record(manifest, value, state=STATE):
    if os.geteuid() != 0:
        raise ValueError("Software choices must be recorded by the installer privilege helper")
    if manifest["system"] != host_system():
        raise ValueError("Software catalog does not match the live system")
    value = validate(manifest, value)
    state.parent.mkdir(mode=0o700, exist_ok=True)
    check_directory(state.parent)
    value.update({"manifestDigest": digest(manifest), "system": manifest["system"]})
    atomic_write(state, json.dumps(value, indent=2) + "\n")


def load_record(manifest, state=STATE):
    check_directory(state.parent)
    metadata = state.lstat()
    if (not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0
            or metadata.st_mode & 0o077):
        raise ValueError("Unsafe software selection; restart Install nascentOS")
    value = json.loads(state.read_text())
    if (value.pop("manifestDigest", None) != digest(manifest)
            or value.pop("system", None) != manifest["system"]):
        raise ValueError("Software catalog changed; restart Install nascentOS")
    return validate(manifest, value)


def install(root, config, manifest_path, state=STATE):
    """Call after nascent_install.prepare(), before nixos-install runs."""
    manifest = load_manifest(Path(manifest_path))
    value = load_record(manifest, state)
    target, config = Path(root) / "etc/nixos", Path(config)
    module = target / "nascent-software.nix"
    receipt = target / "nascent-software.json"
    vpn_module = target / "nascent-vpn.nix"
    gaming_module = target / "nascent-gaming.nix"
    if any(p.exists() or p.is_symlink() for p in (module, receipt, vpn_module, gaming_module)):
        raise ValueError("Software configuration already exists; refusing to overwrite")
    source_catalog = target / "nascentos/installer/software-selection/catalog.json"
    source_lock = target / "nascentos/flake.lock"
    if (json.loads(source_catalog.read_text())["nixpkgsRevision"] != manifest["nixpkgsRevision"]
            or json.loads(source_lock.read_text())["nodes"]["nixpkgs"]["locked"]["rev"]
            != manifest["nixpkgsRevision"]):
        raise ValueError("Installed source and software catalog revisions differ")
    text = config.read_text()
    anchor = "./nascent-desktop.nix"
    if text.count(anchor) != 1:
        raise ValueError("Unexpected target configuration import list")
    # Validate/render every optional choice before creating any target files.
    vpn_text = render_vpn(value.get("vpn"), manifest["system"])
    gaming_text = render_gaming(value.get("gaming", gaming_defaults()), manifest["system"])
    names = " ".join(json.dumps(name) for name in value["selected"])
    module.write_text("{ ... }: {\n"
                      "  imports = [ ./nascentos/installer/software-selection/integration.nix ];\n"
                      "  nascent.software.enable = true;\n"
                      f"  nascent.software.selected = [ {names} ];\n"
                      "}\n")
    vpn_module.write_text(vpn_text)
    gaming_module.write_text(gaming_text)
    receipt.write_text(json.dumps({**value, "system": manifest["system"],
                                  "manifestDigest": digest(manifest)}, indent=2) + "\n")
    atomic_write(config, text.replace(anchor, anchor + "\n      ./nascent-software.nix\n      ./nascent-vpn.nix\n      ./nascent-gaming.nix"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["record"])
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        raw = sys.stdin.read(16385)
        if len(raw) > 16384:
            raise ValueError("Software selection is too large")
        record(load_manifest(args.manifest), json.loads(raw))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
