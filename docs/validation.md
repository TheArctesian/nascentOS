# Validation record — 2026-10-22

Development checkout: isolated linked worktree on `codex/hyprland-foundation`,
from repository revision `6dc5075d02418af4fdaa337f83f6f34a0f73bf3d`.
Host: Apple Silicon macOS (`aarch64-darwin`). Nix 2.35.2 was found outside PATH.
No pre-existing repository bootstrap or gate existed; `scripts/check` is the new gate.

## Current consolidated image — installation, boot and logout passed

The consolidated ARM64 ISO4 is `.vm/nascentos-arm64-integrated-fixed.iso`:

- ISO SHA-256: `0a5e6839f1d8cd71a1e50a6daa86598deace69e1c60e55374b1fc17c7fd6cdfe`.
- ISO store path: `/nix/store/6ywbx3735ynp4cknah7j3jp7fng326bg-nixos-nascent-graphical-26.05.20261020.cd4ea8d-aarch64-linux.iso`.
- Source store path: `/nix/store/66vnnrihh54s9274qiv563hvw5db1wpf-source`.
- Source NAR hash: `sha256-fzQbclYdXTlwd0Oz/EtW8AgXKxkhjPDVIu4W/8DHJ5o=`.

The `.vm/source-integrated4` snapshot matches the production source files;
subsequent shell regression changes affect tests only. This image includes the
software picker, AppImage infrastructure (zero enabled AppImage catalog entries),
mail/password selection, VPN and gaming profiles, approved design resources,
Zsh with Oh My Zsh Boxfish, and local release/CI source files. Including workflow
files does not mean any remote workflow or release has run.

Passed consolidated checks: 39 root Python tests, 43 picker tests, 16 AppImage
tests, four mail tests, two VPN tests and three release Python tests; native root
CLI checks; expanded ARM/x86 profile evaluation; 12 offscreen Qt widget tests per
architecture; and eight native shell regression tests. The previous final
`scripts/check` attempt stopped at its source-hash guard because documentation
changed during evaluation. This was an environment/source-stability interruption,
not a product failure. The subsequent frozen-source `scripts/check` passed
formatting, all-system evaluation and the built native CLI test derivation.
Its complete log is `.vm/frozen-source-check.log`; this result update changes
documentation only after that gate completed.

The real live GUI picker passed search, optional native selection, Cursor's
explicit proprietary checkbox confirmation and removal, and disabled Slack on
ARM. The validated root-owned selection receipt contains:

- Software: `codex`, `fira-code`, `firefox`, `font-awesome`, `keepassxc`, `neovim`,
  `open-dyslexic`.
- VPN: `networkmanager`; no credentials, profile import or connection activated.
- Gaming: profile, GameMode and gamescope enabled; Steam, extra Steam session and
  mapping tuning disabled.

The fresh ISO4 live session starts Zsh without a first-login wizard and has
user-owned, mode-600 writable `.zshrc` and theme configuration. ISO3 (hash prefix
`44725…`) exposed a Zsh wizard; the production fix seeds configuration early via
global zshenv with a root guard. Eight fresh-HOME shell tests cover positive and
negative behavior. The older ISO3 result is not the current image.

The ISO4 Calamares run has shown Welcome, Location, Keyboard, Users, Desktop,
Partitions, Summary and Install, including its compact confirmation dialog.
Known presentation limits remain: Desktop still shows an upstream ZIP
placeholder, the Welcome banner crops square artwork, and Nordic translucency
is visible behind Summary. This is not a claim of flawless installer UI.

ISO4's Calamares run reached **All done**, completing EFI/ext4 partitioning and
installation; screenshot `.vm/install-verify/consolidated-finish-check.png`.
The task-local launcher's boot-priority correction passed a default-launch test
with the ISO still attached: root was `/dev/vda2` (ext4), no live marker existed,
and password serial login entered Zsh without a wizard. Evidence:
`.vm/install-verify/default-boot-priority-test.png` and
`.vm/install-verify/default-priority-installed.serial.log`.

After poweroff, a separate `--installed` launch had no ISO arguments and no `sr0`.
The fixture account `vmtest` authenticated through graphical greetd and entered
Hyprland (observed PID 1039). Config errors were empty, `gb` / English (UK)
persisted, and Nord with the dithered home wallpaper was visible. All three
shared session units were active and no system units failed. The installed
selection persisted exactly as the seven software IDs, NetworkManager VPN and
three enabled gaming options listed above; Steam/session/mapping remained off.
There was no live `nixos` account, marker, installer command/button or passwordless
sudo allowance. Ollama listened only on `127.0.0.1:11434`.

Installed commands reported Codex 0.146.0, KeePassXC 2.7.12, GameMode 1.8.2 and
gamescope 3.16.23. KeePassXC's real GUI opened through the user manager on the
active display. Its initial TTY version check lacked DISPLAY; repeating in the
actual display context succeeded, so the initial failure was a context issue.
Kitty ran actual Zsh 5.9.1 with Boxfish and no first-run wizard; screenshot
`.vm/install-verify/kitty-boxfish-runtime.png`. Font matching selected
OpenDyslexic for sans and Fira Code for monospace.

The installed Agent GUI offered the executable Codex adapter while the default
selection remained none; screenshot `.vm/install-verify/installed-agent-only.png`.
An explicit fixture selection followed by `run --version` worked without provider
authentication or a provider/network request. The newly created selection file
was then removed to restore none. User ownership/writability checks passed for
the adapter (mode 700), `.zshrc` and theme (600), and Neovim `init.lua` (644).

One GNOME keyring process (observed PID 1003) owned `org.freedesktop.secrets`.
After password GUI login, `ReadAlias(default)` resolved to the login collection
and its `Locked` property was false. No item contents were read; no vault or
provider login was performed. Super+Shift+E then returned to greetd; screenshot
`.vm/install-verify/consolidated-logout.png`. All three session units became
inactive and Hyprland, Waybar and mako were absent.

This proves the consolidated ARM fixture installation, installed login and
logout path. No VPN connection, game, model/inference, vault-data operation or
provider authentication was tested. Gaming version checks do not establish
working gameplay. The final frozen-source gate passed as recorded above.

## Historical baseline — full installation and boot passed

The historical baseline ARM64 ISO has SHA-256
`cf016922176306ef515a02dd5c8bf51e21f20a1af03fe0bea9df99eeafb45c40`.
`scripts/check` and 34 Python tests passed. This baseline superseded the first
live-preview ISO recorded below; runtime observations must stay associated with
the image actually tested.

A separate disposable ARM VM completed the full graphical Calamares workflow
and reached **All done**. EFI/ext4 partitioning and `nixos-install` completed.
The separate test VM then passed installed-disk boot and login. It launched with
`--installed`; process arguments contained no ISO. The running root was
`/dev/vda2` (ext4), `/dev/vda1` was mounted at `/boot` (vfat), and no `sr0`
optical device was present. EFI boot selected generation 1.

The fixture account `vmtest` authenticated with its password both on serial and
through graphical greetd. Hyprland was running and `configerrors` was empty.
The selected keyboard remained `English (UK)` / layout `gb`. Nord was the default
theme and the dithered home wallpaper was visible; screenshot:
`.vm/install-verify/installed-desktop.png`.

The installed desktop had no installer bar/button/command, no live `nixos` user
and no live marker. `sudo -n` rejected passwordless access. The account owned a
writable `~/.config/nvim/init.lua` with mode 644. Shared graphical, nascent and
wallpaper session units were active, and `systemctl --failed` was empty. The
inference listener bound only to `127.0.0.1:11434`; this verifies endpoint exposure,
not loaded models or inference.

The task-local `--installed` launcher also received a Bash 3.2 compatibility fix:
its boot-option array now retains the nonempty `-boot menu=on` baseline, avoiding
an empty-array failure.

The user-visible VM rebooted into the attached, CD-first live ISO. Read-only
inspection of its installed disk confirmed `/etc/NIXOS`,
`EFI/systemd/systemd-bootaa64.efi`, `EFI/BOOT/BOOTAA64.EFI` and a generation-1
loader entry. These establish installed files and boot artifacts, not a completed
installed-disk boot by themselves. Recovery was subsequently completed by a
separate project task: it launched the existing disk with `--installed` and
verified greetd's Username prompt. The user then reported that Hyprland started
after login. That user report is distinct from the separate fixture VM's direct
runtime checks; no user credentials were supplied by this task.

The ready live integration includes a bounded `xhost` root grant to the X display for
privileged graphical installation, with cleanup after the installer exits;
shared session-bus/lifecycle handling; a restriction against modal dialogs
maximizing; and the existing Nord-dithered home-photo wallpaper. The original
photo remains available separately. These corrections replace the earlier
privilege-launch/startup concerns described by the initial preview.

The historical baseline did not include the later integrated components. Its
full pass must not be transferred to the consolidated image without repeating
installation and installed-disk boot there.

## Passed source and earlier preview checks

- `scripts/check`: Nix formatting, `nix flake check --no-build --all-systems .`,
  then a built/executed native Darwin `checks.aarch64-darwin.cli` derivation.
- Complete ARM/x86 NixOS VM and graphical installer ISO derivation evaluation;
  Darwin-host QEMU launcher evaluation for ARM/x86. Installer assertions verify
  Hyprland enabled, no GNOME, SSH disabled, the live greetd user and valid ISO labels.
- Profile matrix: portable desktop and CPU local AI on ARM/x86, plus personal
  CLI/desktop/proprietary app and NVIDIA/CUDA profiles on x86. Assertions verify
  loopback-only Ollama, no firewall opening or automatic model loading, and no
  model runtime enabled in the generic desktop.
- ShellCheck for every `bin/` and `scripts/` command. CLI tests execute theme
  bootstrap/persistence, writable dereferenced copies of store-like symlinks,
  preservation of personal theme/editor edits, strict agent selection/argument
  forwarding and invalid input handling.
- Eight voice intent tests with mocked compositor/local-model calls: phrase
  routing, schema, fixed launch, targeted normal close, ambiguity, foreign/injected
  address rejection, explicit selection and model response rejection.
- Installer tests using synthetic sysfs and temporary directories: PCI
  filtering, GPU/platform recommendations, hybrid warnings, selection/profile
  validation, no-overwrite behavior, generated config preservation, pin/flake/source
  propagation and the actual pinned Calamares extension patch/AST/install command.
- Generated two temporary installed configurations through the real handoff helper:
  ARM generic and x86 NVIDIA-open, with synthetic UEFI filesystems and a fixture
  user. Both full NixOS system derivations evaluate. Assertions verified desktop
  and greetd enabled, selected `gb` keyboard preserved, GNOME disabled and the live
  `nixos` account absent. This evaluated configuration files only; it installed
  nothing and accessed no target disks.
- Approved main raster SHA-256 matches the branding task's original:
  `421812bf8c068ffc8999289d5ea0d6be1e4b85199140b71101adb2cc79ed872c`.
  `nascent logo` wraps the unchanged renderer; its intentional empty POSIX CDPATH
  assignment is the only excluded ShellCheck style warning (SC1007).
- The preserved original wallpaper matches `raw/home1.JPG` byte-for-byte:
  Git blob `ce854da0d30d58f1d6b64c521e62c26bc40f722a`.
- `git diff --check`.
- Built the full ARM64 graphical ISO in the dedicated Docker container
  `nascentos-arm-builder-51d8` (Nix 2.35.3); Calamares 3.4.2 compiled successfully.
  Output: `.vm/nascentos-arm64.iso`, SHA-256
  `e41a872247a3fb8e17937ff9e18c50f01ead3bb0160797823aa0c169db9951c3`.
- Booted that ISO using native QEMU 10.2.4/HVF on this Mac, with a disposable
  48 GiB qcow2 target, 8 GiB RAM, four vCPUs and virtio graphics. Observed live
  Hyprland, the original home-photo wallpaper, Waybar, themed terminal and menu.
  `hyprctl -i 0 configerrors` returned no errors; greetd is active. The monitor
  reports 1280×800 and software rendering. A startup warning recommends using
  `start-hyprland` rather than invoking Hyprland directly; subsequent session
  corrections are included in the ready image above.
  This is historical preview evidence; the ready ISO above contains subsequent
  session/installer corrections. Screenshots and serial/QEMU logs are under
  `.vm/install-test/`.

At validation time, source files were marked intent-to-add so Git flakes included
them before committing. Ignored VM state/bytecode/build results are excluded.

## Not executed / environment limits

`scripts/test-vm` was invoked and correctly refused macOS with a Linux/KVM
requirement. Nix's builders setting references `/etc/nix/machines`, but that file
is absent. A dedicated Docker ARM64 Linux builder was subsequently provisioned
without changing those host settings; the graphical ISO build and interactive
live boot passed as recorded above. The automated Linux/KVM boot check still has
not run. No Intel/nearby builder setup or host-wide Mac virtualization changes
were made.

The ready ARM64 image has passed live graphical use and a separate disposable
Calamares installation and installed-system boot/login, as recorded above. The
user-visible VM recovery was handled separately, with the user reporting Hyprland
after login. Consolidated ISO4 separately passed installation, disk boot,
graphical login and logout as recorded above.
The x86 image and graphical installation path have not received equivalent
runtime validation.

Remaining nonfatal logs include **No schemas installed**, an unavailable sleep
inhibitor and unsupported `chcon` operations. They remain observations to review,
not proof of complete session or security integration. NVIDIA/firmware,
suspend/resume, physical GPU behavior, audio integration and lock-screen
PAM unlock have no runtime proof. Password-login keyring unlock and session
logout were verified above; portal and lock-screen behavior still need checks. No models were downloaded, and no
Whisper/microphone/model inference or real browser actions were performed.
LazyVim's first plugin-install startup and optional apps beyond the specific
installed command/GUI checks above need runtime checks.
Special Apple/Qualcomm boot/kernel support, legacy NVIDIA drivers and device-specific
Omarchy quirks are not implemented by the generic profile.

The installer emits an upstream ZFS `forceImportRoot` default warning, and
nixpkgs warns that 26.05 is the last x86_64-darwin release. Neither is a validation
failure; the prototype chooses no ZFS target layout and the current Mac is ARM.
Partitioning and installation occurred only on disposable VM disks. No physical
installation, deployment or external messages occurred during validation.
Source publication is separate from these runtime checks. Follow `docs/testing.md`
and `docs/install.md` for the next gates.
