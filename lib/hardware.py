"""Read-only Linux hardware summary and small, reviewable profile generation."""
import argparse
import json
from pathlib import Path
import platform

PROFILES = ("generic", "nvidia-open")


def read(path):
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return ""


def scan(sysroot=Path('/sys'), machine=None):
    machine = machine or platform.machine()
    system = {"x86_64": "x86_64-linux", "aarch64": "aarch64-linux", "arm64": "aarch64-linux"}.get(machine)
    gpu = []
    for device in sorted((sysroot / 'bus/pci/devices').glob('*')):
        try:
            kind = int(read(device / 'class'), 16)
            vendor = int(read(device / 'vendor'), 16)
            ident = int(read(device / 'device'), 16)
        except ValueError:
            continue
        if kind >> 16 == 3:
            gpu.append({"slot": device.name, "vendor": f'{vendor:04x}', "device": f'{ident:04x}'})
    dmi = sysroot / 'class/dmi/id'
    compatible = read(sysroot / 'firmware/devicetree/base/compatible').split('\0')
    families = set()
    for prefix, name in (("apple,", "apple-silicon"), ("qcom,", "qualcomm")):
        if any(token.startswith(prefix) for token in compatible):
            families.add(name)
    family = next(iter(families)) if len(families) == 1 else ('conflicting' if families else 'generic')
    warnings = []
    if family != 'generic':
        warnings.append(f'{family} needs platform-specific boot/kernel/firmware support not supplied by this installer.')
    manufacturer = read(dmi / 'sys_vendor')
    model = read(dmi / 'product_name')
    if any(word in (manufacturer + ' ' + model).lower() for word in ('framework', 'surface', 'rog')):
        warnings.append('Device-specific audio/input/firmware quirks are not automatically ported from Omarchy.')
    nvidia = [item for item in gpu if item['vendor'] == '10de']
    # Adapted from Omarchy's GSP-generation recommendation; a heuristic, not a support guarantee.
    modern_nvidia = bool(nvidia) and all(int(item['device'], 16) >= 0x1e00 for item in nvidia)
    recommended = 'nvidia-open' if modern_nvidia and system == 'x86_64-linux' else 'generic'
    if nvidia:
        warnings.append('Verify NVIDIA generation/driver support before accepting a proprietary driver profile.')
        if len(gpu) > len(nvidia):
            warnings.append('Hybrid graphics detected: PRIME routing/bus IDs require a separate reviewed setup.')
        if not modern_nvidia:
            warnings.append('Older/unknown NVIDIA card: no automatic legacy driver choice; generic may not provide a usable session.')
    if not gpu:
        warnings.append('No PCI display device found; platform/virtual GPUs may need separate review.')
    return {'system': system, 'family': family, 'manufacturer': manufacturer, 'model': model,
            'firmware': 'uefi' if (sysroot / 'firmware/efi').exists() else 'bios-or-platform',
            'gpus': gpu, 'recommended': recommended, 'warnings': warnings}


def profile_text(profile):
    if profile not in PROFILES:
        raise ValueError('Unknown hardware profile')
    body = '  hardware.graphics.enable = true;\n'
    if profile == 'nvidia-open':
        body += ('  nixpkgs.config.allowUnfreePackages = [ "nvidia-x11" "nvidia-settings" "nvidia-persistenced" ];\n'
                 '  services.xserver.videoDrivers = [ "nvidia" ];\n'
                 '  hardware.nvidia.modesetting.enable = true;\n'
                 '  hardware.nvidia.open = true;\n')
    return '# Generated selection; review/edit this file. Storage/boot remain in hardware-configuration.nix.\n{ ... }: {\n' + body + '}\n'


def write_profile(directory, report, profile):
    if profile == 'auto':
        profile = report['recommended']
    contents = profile_text(profile)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / 'nascent-hardware.nix', directory / 'nascent-hardware.json']
    if any(path.exists() or path.is_symlink() for path in paths):
        raise ValueError('Hardware files already exist; refusing to overwrite personal configuration')
    # Exclusive creation also protects against a concurrent writer.
    with paths[0].open('x') as output:
        output.write(contents)
    with paths[1].open('x') as output:
        json.dump({**report, 'selected': profile}, output, indent=2)
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['scan', 'generate'])
    parser.add_argument('directory', nargs='?')
    parser.add_argument('--profile', choices=('auto',) + PROFILES, default='auto')
    args = parser.parse_args()
    if platform.system() != 'Linux':
        parser.exit(2, 'Hardware probing requires the booted Linux target, not the development Mac.\n')
    report = scan()
    try:
        if args.action == 'scan':
            print(json.dumps(report, indent=2))
        elif not args.directory:
            parser.error('generate requires an output directory')
        else:
            selected = write_profile(Path(args.directory), report, args.profile)
            print(f'Wrote {selected} profile and review summary to {args.directory}; no drivers or disks changed.')
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
