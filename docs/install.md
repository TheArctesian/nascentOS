# Graphical live installation

The installation prototype boots the nascentOS **Hyprland** desktop and launches
Calamares after a graphical hardware review. It uses NixOS's graphical installer
base without adding a GNOME session. The intended installed system retains
nascentOS modules, Nord desktop defaults, writable personal configuration, LazyVim
and local inference support. No models are downloaded automatically.

The consolidated ARM image completed software selection, a disposable graphical
installation, disk-only boot and password login to Hyprland. Selected apps,
fonts, the writable Zsh/Boxfish setup and session keyring were checked. See
[validation.md](validation.md) for exact image identities and observed results;
source tests do not establish runtime behavior of a newer image.

## Build and preview

Use a matching Linux builder for the image you want to test:

```sh
# Generic ARM64 Linux image, for supported virtual/firmware environments:
nix build '.#nixosConfigurations.installer-aarch64.config.system.build.isoImage'
# Generic x86_64 Linux image:
nix build '.#nixosConfigurations.installer-x86_64.config.system.build.isoImage'
```

`nix build .#installer` selects the native Linux architecture. The development Mac
needs Linux build products; see the ARM development route in [testing.md](testing.md).
An ARM ISO is not an Apple Silicon bare-metal installer: platform-specific boot,
kernel and firmware support is separate.

First boot the image in a disposable VM with a fresh virtual target disk. Inspect
the Hyprland desktop, launcher, terminal, network and Nord defaults. Open **Install
nascentOS** from the application launcher, or run `nascent-install` in a terminal.
Writing the ISO to removable media and installing on a physical disk are later,
explicitly reviewed actions; this repository performs neither automatically.

## Hardware review, then Calamares

1. The hardware dialog shows architecture, firmware, DMI identity, PCI display
   devices, warnings and a recommended profile. Select `generic` or `nvidia-open`.
   Canceling exits before Calamares starts. This step changes no disks or drivers.
2. `generic` enables standard graphics support without vendor-specific overrides.
   `nvidia-open` enables modesetting and the unfree NVIDIA driver with its open
   kernel module; verify that the actual GPU is supported before selecting it.
   The recommendation uses a PCI-ID generation heuristic, not a compatibility
   database. Hybrid graphics still needs a reviewed PRIME/bus-ID configuration.
3. The software picker selects applications, fonts, one password manager and an
   optional VPN or gaming profile. Architecture-specific choices are disabled
   when unavailable; proprietary components require explicit confirmation.
   Canceling leaves disks untouched. No account sign-in or VPN activation occurs.
4. Calamares handles locale, keyboard, user account, boot/storage choices and its
   installation summary. Select the intended disk explicitly, check its model
   and size, and review the partition changes before confirming installation.
   Disk changes begin only through the installer workflow; there is no guessed
   target disk or unattended partitioning recipe.
5. During the approved installation job, the NixOS extension generates the target
   hardware/users/boot configuration. The nascentOS handoff adds the common modules
   and selected graphics profile, then installs the `nascent` flake configuration.

The hardware selection is recorded in root-owned live-session state. Unsupported
architectures and detected Apple/Qualcomm device-tree platforms are refused by
this handoff because their boot/kernel configuration is not supplied. Older
NVIDIA cards, special laptops and other platform GPUs need further review; neither
Omarchy inspiration nor a successful scan implies universal device support.
Networking is normally needed to fetch pinned packages and build the target;
this is not a verified offline installer.

## Installed configuration and ownership

The resulting `/etc/nixos` contains:

- `configuration.nix` and `hardware-configuration.nix`: Calamares/NixOS-generated
  users, locale, boot and machine-specific storage/module configuration.
- `nascentos/`: a writable copy of the exact prototype source shipped on the ISO.
- `nascent-desktop.nix`: the installed desktop, greetd session and local AI option.
- `nascent-hardware.nix` and `nascent-hardware.json`: selected graphics policy and
  the detected hardware summary, both available for review and editing.
- `nascent-software.nix` and `nascent-software.json`: validated software choices
  and their receipt; `nascent-vpn.nix` and `nascent-gaming.nix` hold optional profiles.
- `flake.nix` and `flake.lock`: the installed `nascent` entry and pinned nixpkgs
  revision inherited from the ISO source.

The installed entry imports the generated target configuration, not the live ISO
module or VM host. Live credentials and live autologin are therefore separate;
Calamares's user choices remain authoritative. Its optional autologin choice is
translated to greetd. The handoff refuses to overwrite existing nascentOS target
files. Personal desktop files are bootstrapped without overwriting later edits;
theme changes need no NixOS or Home Manager rebuild.

After a test install, remove the ISO and verify the installed boot, login, graphics,
networking, audio, lock/unlock and suspend. Review `/etc/nixos` before future
system changes. Subsequent configuration builds use `/etc/nixos#nascent`; update
the flake intentionally and use NixOS generations for rollback. This prototype
does not configure automatic deployment or upgrades.

## Manual fallback

For recovery or a platform requiring a custom configuration, follow the
[NixOS installation manual](https://nixos.org/manual/nixos/stable/#sec-installation).
Generate hardware configuration on the actual target and import this project's
`modules` alongside it. `nascent hardware scan` reads the booted Linux target;
`nascent hardware generate DIR --profile generic` writes a separate reviewable
profile and JSON summary without applying it or overwriting an existing selection.
`hosts/physical-example` remains a UEFI template; adapt users, storage, boot and
architecture deliberately. Never use the disposable `hosts/vm` on physical hardware.
