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

Preview ISOs are published from every push to `main`:
[x86_64](https://iso.stephenokita.com/latest/nascentos-x86_64-linux.iso),
[ARM64](https://iso.stephenokita.com/latest/nascentos-aarch64-linux.iso),
[version info and checksums](https://iso.stephenokita.com/latest.json).

For graphical installation, download one of those or build the native Linux ISO with `nix build .#installer`,
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

Keybindings follow the owner's bspwm/sxhkd layout.

| Shortcut | Action |
| --- | --- |
| Super + Shift + Enter (or Enter) | Terminal |
| Super + P (or D) | App launcher |
| Super + Shift + Space | Desktop menu (apps, screenshot, clipboard, do not disturb, themes, agent, power) |
| Super + A | Selected agent |
| Super + B / O / Z / G / M / Y | Browser / Obsidian / Zotero / Signal / Slack / Yazi (focus or launch) |
| Super + I | Open or focus Install nascentOS (live ISO) |
| Super + C (or Q) / Shift + C | Close / kill window |
| Super + T / Shift + T / S / F | Tiled / pseudo-tiled / floating / fullscreen |
| Super + Space | Monocle (maximise) toggle |
| Super + h j k l | Focus window |
| Super + Shift + h j k l | Swap window |
| Super + Alt + h j k l | Resize window |
| Super + Ctrl + h j k l | Preselect split direction |
| Super + 1…0 / Shift + 1…0 | Workspace / move window to workspace |
| Super + Left / Right (or < >) | Previous / next workspace |
| Super + V | Clipboard history |
| Super + N / Shift + N | Show the last notification again / toggle do not disturb (also the bar bell) |
| Print / Super + Shift + S / Ctrl + Print | Screenshot: full / area / delayed (copied, saved to ~/Pictures/Screenshots) |
| Super + Shift + E (or Pause) | Power menu (lock, suspend, log out, reboot, shut down) |
| Super + Escape / Shift + R | Reload compositor config |
| Super + Shift + Q | Exit session |
| Super + mouse drag | Move (left button) / resize (right button) |

Volume, microphone, brightness and media keys work, including on the lock screen, and show a
brief on-screen level.
The display scale is picked from the panel's pixel density (for example 2× on a
Framework 13); set your own with `hl.monitor` in `~/.config/nascentos/hyprland.lua`.

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
physical hardware behavior need runtime validation. After 5 idle minutes the screen
dims, at 10 it locks and then blanks; the live installer never locks. There is no agent orchestrator or remote access default. Model services are opt-in.
