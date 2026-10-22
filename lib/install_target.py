"""Calamares handoff: preserve generated users/storage, add the pinned nascentOS configuration."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import re
import tempfile
from hardware import PROFILES, profile_text, scan, write_profile

SELECTION = Path('/run/nascent-installer/profile.json')
SOURCE = Path('/etc/nascentos-source')


def record(profile):
    if os.geteuid() != 0:
        raise ValueError('Hardware selection must be recorded through the live installer privilege helper')
    if profile not in PROFILES:
        raise ValueError('Unknown hardware profile')
    SELECTION.parent.mkdir(mode=0o700, exist_ok=True)
    directory = SELECTION.parent.lstat()
    if not stat.S_ISDIR(directory.st_mode) or directory.st_uid != 0 or directory.st_mode & 0o022:
        raise ValueError('Unsafe installer state directory')
    report = scan()
    if not report['system'] or report['family'] != 'generic':
        raise ValueError('This platform needs a separate supported boot/kernel configuration')
    # A previous selection is intentionally replaced by another explicit GUI choice.
    with tempfile.NamedTemporaryFile(mode='w', dir=SELECTION.parent, delete=False) as output:
        temporary = Path(output.name)
        json.dump({'profile': profile, 'report': report}, output)
    os.replace(temporary, SELECTION)


def load_selection(path=SELECTION):
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != 0 or metadata.st_mode & 0o022:
        raise ValueError('Unsafe hardware selection record; launch Install nascentOS again')
    value = json.loads(path.read_text())
    if value.get('profile') not in PROFILES:
        raise ValueError('Invalid selected hardware profile')
    return value


def prepare(root, config, source=SOURCE, selection=None):
    """Called only inside Calamares's approved installation job, after config generation."""
    root, config = Path(root), Path(config)
    choice = selection if selection is not None else load_selection()
    report = choice['report']
    system = report['system']
    if system not in ('aarch64-linux', 'x86_64-linux') or report['family'] != 'generic':
        raise ValueError('Unsupported platform for this installer image')
    profile_text(choice['profile'])
    lock = json.loads((source / 'flake.lock').read_text())
    revision = lock['nodes']['nixpkgs']['locked']['rev']
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Invalid pinned nixpkgs revision')
    configuration = config.read_text()
    anchor = './hardware-configuration.nix'
    if configuration.count(anchor) != 1:
        raise ValueError('Unexpected generated configuration; refusing to change imports')
    target = root / 'etc/nixos'
    owned = [target / name for name in ('nascentos', 'nascent-desktop.nix', 'nascent-hardware.nix',
                                        'nascent-hardware.json', 'flake.nix', 'flake.lock')]
    if any(path.exists() or path.is_symlink() for path in owned):
        raise ValueError('nascentOS target files already exist; refusing to overwrite them')
    shutil.copytree(source, target / 'nascentos')
    (target / 'nascentos').chmod((target / 'nascentos').stat().st_mode | stat.S_IWUSR)
    for path in (target / 'nascentos').rglob('*'):
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | stat.S_IWUSR)
    write_profile(target, report, choice['profile'])
    desktop = '''{ pkgs, ... }: {
  nascent.desktop.enable = true;
  nascent.localAI.enable = true;
  services.greetd.enable = true;
  services.greetd.settings.default_session.command = "${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session";
}
'''
    (target / 'nascent-desktop.nix').write_text(desktop)
    config.write_text(configuration.replace(anchor, anchor + '\n      ./nascentos/modules\n      ./nascent-desktop.nix\n      ./nascent-hardware.nix'))
    # The generated entry consumes Calamares's users/boot/locale config, not the live ISO's module.
    (target / 'flake.nix').write_text('''{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/REVISION";
  outputs = { nixpkgs, ... }: {
    nixosConfigurations.nascent = nixpkgs.lib.nixosSystem {
      system = "SYSTEM";
      modules = [ ./configuration.nix ];
    };
  };
}
'''.replace('REVISION', revision).replace('SYSTEM', system))
    shutil.copyfile(source / 'flake.lock', target / 'flake.lock')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['record'])
    parser.add_argument('--profile', choices=PROFILES, required=True)
    args = parser.parse_args()
    try:
        record(args.profile)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
