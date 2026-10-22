# Reference audit

Reviewed 2026-10-22. The personal repositories and Omarchy are design references, not build dependencies.
The only flake dependency is nixpkgs, pinned by revision and NAR hash in flake.lock.

| Source | Exact revision | What informs this prototype | Reuse and license |
| --- | --- | --- | --- |
| [TheArctesian/etcnixos](https://github.com/TheArctesian/etcnixos/tree/96b0c7c32b583ea4884573a2fbfccf2033df6cdf) (`master`) | `96b0c7c32b583ea4884573a2fbfccf2033df6cdf` | Separate desktop/audio/appearance/service modules; JetBrains Mono and Nord palette | No source files copied. No license file was present at this revision; do not vendor code without resolving permission. |
| [omacom/omarchy](https://github.com/omacom/omarchy/tree/a17a001b72799ccad1b1c9e859d4a5760a57e820) (`quattro`) | `a17a001b72799ccad1b1c9e859d4a5760a57e820` | Keyboard-first tiling, command structure, personal overrides and hardware detection/setup patterns | Independently authored Nix/Lua configuration. No upstream scripts, shell, wallpaper, branding or application assets copied. MIT notice retained in `third-party/omarchy.LICENSE` as reference attribution. |
| [NixOS/nixpkgs](https://github.com/NixOS/nixpkgs/tree/cd4ea8d57de16f4810bc5f14207bac45fbf19f67) (`nixos-26.05`) | `cd4ea8d57de16f4810bc5f14207bac45fbf19f67` | NixOS modules, packages, QEMU VM, installer ISO and test driver | Consumed as a flake input. Upstream licenses remain with their packages. |

The old config selects X11/bspwm and includes installer disk UUIDs, LUKS keyfile
paths, a specific user, NVIDIA/CUDA services, exposed ports and automatic updates.
Those machine assumptions are excluded. PipeWire, fonts and modularity carry over
as ideas; a compositor choice remains replaceable.

Omarchy's manual at this revision describes Arch + Hyprland + Quickshell. Its
`config/hypr/hyprland.lua` and `manual/31-dotfiles.md` explain the defaults/overrides
split. `default/hypr/looknfeel.lua` and `default/hypr/bindings/tiling.lua` informed
the scope of the desktop experiment. This prototype uses a small Waybar/fuzzel
setup; the small CLI adapts selected structural patterns, while substantial Omarchy
parity and Quickshell remain future work.
Arch installation, pacman, migration and update scripts are not applicable to NixOS.

Hyprland Lua calls were checked against the pinned package's
[v0.55.4 example](https://github.com/hyprwm/Hyprland/blob/v0.55.4/example/hyprland.lua).
The configurations here are new project code under this repository's AGPL-3.0 license.
Any future copied Omarchy code must preserve its MIT copyright and permission notice
and be recorded here with source paths and modifications.

Additional supplied sources:

- Dotfiles upstream/local clean revision `602357c47db57de7c9d956788508842be1449e15`:
  `assets/nvim` is an unchanged copy of `.config/nvim`; its Apache-2.0 license is
  preserved inside that directory, and the repository-level GPL-3.0 notice is
  retained as `third-party/dotfiles.LICENSE`. `docs/Brewfile.source` is the source
  inventory; package mappings are newly authored. No other personal configs copied.
- Wallpapers revision `2105e063afd839fdd06b47eaf426716fcffa21b4`: the user-selected
  original `raw/home1.JPG` is included at `assets/wallpapers/home1.JPG` with explicit
  user authorization; its Git blob is `ce854da0d30d58f1d6b64c521e62c26bc40f722a`.
  The requested Nord default is the unchanged `screens/2560x1440/home1.png`,
  bundled as `assets/wallpapers/home1-nord.png`, Git blob
  `6366ec73eff21f4b20ffee1f9eaddc7ba5450585`.
  No general wallpaper redistribution license was found; this authorization does
  not extend to the rest of the repository. See `docs/personalization.md`.
- DotFiles' `legacy/config/polybar/config.ini` informed compact height and rounded
  corners; `legacy/config/xmobar/nord-xmobarrc.hs` informed the Nord palette and
  restrained workspace underline. The new Waybar configuration is independently
  authored. Outer 10–12px margins implement the user's current request; they were
  not measured from wallpaper renders. The Polybar source is Dracula, while the
  xmobar source is Nord. The wallpaper repository's `screens/` are wallpapers,
  not desktop screenshots.
- The pinned nixpkgs `nordic` package supplies GTK/Kvantum application themes under
  its GPL-3.0-only license. [Hyprland 0.55 window rules](https://wiki.hypr.land/0.55.0/Configuring/Basics/Window-Rules/)
  provide the Calamares maximization rule.
- Omarchy `bin/omarchy`, `bin/omarchy-theme-set`, `bin/omarchy-agent`,
  `bin/omarchy-default-agent` and `agents/skills/command-metadata.md` informed
  command routing, writable theme selection and optional provider adapters. The
  new implementation intentionally keeps only those structural patterns; it does
  not copy the large command registry, account migration or provider-specific
  permission flags.

## Hardware setup audit

The hardware audit uses Omarchy revision
[`a17a001b72799ccad1b1c9e859d4a5760a57e820`](https://github.com/omacom/omarchy/tree/a17a001b72799ccad1b1c9e859d4a5760a57e820):

- [`install/hardware/all.sh`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/install/hardware/all.sh)
  dispatches hardware setup scripts, including device-specific workarounds.
- [`install/hardware/nvidia.sh`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/install/hardware/nvidia.sh)
  selects supported NVIDIA package families and configures modesetting/initramfs.
  [`vulkan.sh`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/install/hardware/vulkan.sh)
  selects graphics packages by vendor/platform.
- [`bin/omarchy-hw-nvidia-gsp`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/bin/omarchy-hw-nvidia-gsp)
  and [`omarchy-hw-nvidia-without-gsp`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/bin/omarchy-hw-nvidia-without-gsp)
  inspect cached sysfs vendor/class/device IDs instead of probing PCI config space.
  They use generation thresholds to distinguish modern and older GPU families.
- [`bin/omarchy-hw-platform`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/bin/omarchy-hw-platform)
  distinguishes architecture/platform families, including device-tree Apple and
  Qualcomm identities; its image-target handling avoids mistaking build hardware
  for the eventual target.
- [`bin/omarchy-apply-hardware`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/bin/omarchy-apply-hardware)
  runs setup on installed hardware or defers image setup;
  [`bin/omarchy-provision-hardware`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/bin/omarchy-provision-hardware)
  resumes queued first-boot work. [`install/hardware/platform-setup.sh`](https://github.com/omacom/omarchy/blob/a17a001b72799ccad1b1c9e859d4a5760a57e820/install/hardware/platform-setup.sh)
  invokes platform lifecycle hooks.

nascentOS independently adapts the cached-ID inspection and platform separation
into `lib/hardware.py`, with DMI identity/warnings and a reviewable JSON report.
A modern-NVIDIA heuristic recommends the selectable `nvidia-open` profile;
`generic` keeps standard kernel/Mesa defaults. It does not port Omarchy's full
workaround inventory, legacy driver families, deferred queue or Arch package and
initramfs commands. Detected special ARM platforms require a separate supported
boot/kernel configuration. Generated NixOS storage/boot configuration remains
separate from graphics policy, and the user reviews the selection before install.
The Omarchy MIT attribution above applies to these referenced patterns.

## Graphical installer sources

The [NixOS manual's installation and live ISO guidance](https://nixos.org/manual/nixos/stable/#sec-installation)
and the [Calamares user guide](https://calamares.io/docs/users-guide/) informed the
graphical flow: distribution-configured locale, keyboard, partition, users,
summary and installation stages. The integration consumes the existing NixOS
Calamares extension rather than implementing a new partitioner.

At pinned nixpkgs revision `cd4ea8d57de16f4810bc5f14207bac45fbf19f67`, the relevant
upstream sources are:

- [`nixos/modules/installer/cd-dvd/installation-cd-graphical-base.nix`](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/installer/cd-dvd/installation-cd-graphical-base.nix):
  graphical installer base, composed with nascentOS Hyprland instead of GNOME.
- [`pkgs/by-name/ca/calamares-nixos/package.nix`](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/ca/calamares-nixos/package.nix)
  and [`calamares-nixos-extensions/package.nix`](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/ca/calamares-nixos-extensions/package.nix):
  NixOS wrapper and extension 0.3.23 packaging. The underlying
  [`calamares/package.nix`](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/ca/calamares/package.nix)
  pins Calamares 3.4.2.

`modules/installer` overrides these packages with a checked patch against the
extension's `modules/nixos/main.py` and configuration. It fixes the desktop choice
to nascentOS, routes installer launch through graphical hardware review, translates
autologin to greetd and adds a target configuration handoff before `nixos-install
--flake`. `lib/install_target.py` preserves generated users/storage/boot settings
while adding source, modules, graphics policy and the pinned flake.

Upstream installer packages are built through nixpkgs with their existing license
metadata and notices; their complete source trees are not vendored here. Local
patch/handoff code is project code. Build/evaluation and fixture tests are distinct
from a live boot or end-to-end installation, which remains untested.
