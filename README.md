# nascentOS

An early experiment toward an agent-first NixOS desktop. “Agent-first” is still
being defined. This first slice is a portable Hyprland foundation, a disposable
VM and a Hyprland live graphical installer. No agent provider is chosen. Optional local inference/speech support is available.

The desktop includes kitty, Firefox, fuzzel, Waybar, mako, PipeWire, NetworkManager,
Fira Code, Font Awesome, the selected Nord-dithered home wallpaper, and Nord as the default
palette, with live theme selection. Hyprland is the initial tiling
experiment, not a permanent architecture decision. Defaults are inspired by the
[old personal NixOS config and Omarchy](docs/references.md), rather than an Omarchy port.

The installer offers application/font choices plus optional VPN and gaming
support. Interactive logins use Zsh, Oh My Zsh, suggestions/highlighting and a
writable Boxfish prompt; Bash remains available for scripts. The consolidated
ARM image has passed a disposable installation and installed-disk login; see
[the validation record](docs/validation.md) for its exact identity and limits.

## Start here

Install Nix using the [official instructions](https://nixos.org/download/).
An existing installation outside PATH can be exposed with:

```sh
export PATH="/nix/var/nix/profiles/default/bin:$PATH"
export NIX_CONFIG="extra-experimental-features = nix-command flakes"
./scripts/check
```

There was no pre-existing bootstrap or validation workflow. `scripts/check` is the
local gate: formatting and evaluation of all exported configurations/checks. It
does not build Linux or claim a desktop boots. New source files must be added to Git (intent-to-add is sufficient) before flake evaluation; ignored VM state stays outside the source snapshot.

For graphical installation, build the native Linux ISO with `nix build .#installer`,
boot it in a disposable VM first, and open **Install nascentOS** from the live
Hyprland launcher. A hardware review precedes Calamares; the installed system gets
nascentOS modules and a pinned flake. See [the installer workflow](docs/install.md).
The consolidated ARM image passed graphical installation, installed-disk boot
and password login on this Mac. See [the exact validation record](docs/validation.md)
for the image hash and remaining x86/physical-hardware gates.

On Linux with the matching CPU architecture:

```sh
nix build .#vm
mkdir -p .vm
cd .vm
../result/bin/run-nascent-vm-vm
```

Log in as **nascent**, password **nascent**, only in this disposable VM. This
account is defined only in `hosts/vm`. The Super key is usually Command on a Mac.

| Shortcut | Action |
| --- | --- |
| Super + Enter | Terminal |
| Super + Space | Desktop menu (apps, themes, agent, lock) |
| Super + D / A | App launcher / selected agent |
| Super + B | Browser |
| Super + I | Open or focus Install nascentOS (live ISO) |
| Super + arrows | Focus window |
| Super + 1…0 | Workspace 1…10 |
| Super + Shift + 1…0 | Move window to workspace |
| Super + Q / F / V | Close / fullscreen / float |
| Super + Shift + L / E | Lock / exit session |
| Super + mouse drag | Move (left button) / resize (right button) |

The session starts through `nascent-session`. Themes and the personal Nord LazyVim
config bootstrap into writable user files only when absent. `nascent theme set
nord` and `nascent theme set tokyo-night` switch themes without a system rebuild.
Personal compositor overrides live at `~/.config/nascentos/hyprland.lua` and load
last. See [personalization, wallpapers and the Brewfile migration](docs/personalization.md).
No Home Manager is used. `nascent logo` displays the approved Nord ASCII logo;
the unchanged main raster brands the graphical installer.

Reusable NixOS modules
are opt-in: import `nixosModules.default` and set `nascent.desktop.enable = true`.
Host/user packages and other NixOS modules can be added normally. No display
manager, disk layout, credentials, timezone or GPU is imposed by that module.

See [testing and Mac VM constraints](docs/testing.md),
[graphical installation and hardware review](docs/install.md), and
[pinned reference/attribution notes](docs/references.md),
[default agent toolchain](docs/toolchain.md), and
[local models, Whisper and agent adapters](docs/local-ai.md), and
[bounded voice desktop commands](docs/voice.md).

This is a prototype: login/lock, portal integration, rendering, audio, resume and
physical hardware behavior need runtime validation. No automatic idle lock is
configured yet. There is no agent orchestrator or remote access default. Model services are opt-in.
