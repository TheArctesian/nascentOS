# Develop here, validate in a VM, then install elsewhere

## 1. Local source gate

```sh
./scripts/check
```

This enables the required Nix features for that process, checks formatting and
runs `nix flake check --no-build --all-systems .`. All exported VM/installer
and Linux test derivations are evaluated, including NixOS assertions. The native CLI check also executes ownership, theme persistence, argument-forwarding,
input-validation and installer/hardware fixture tests with ShellCheck. No Linux boot or GPU behavior is verified
by these local checks.

## 2. Automated Linux boot gate

On a matching-architecture Linux builder with Nix and accessible `/dev/kvm`:

```sh
./scripts/test-vm
```

This first runs the local gate, then builds the native `checks.<system>.boot`
NixOS test. The test starts a separate disposable guest, waits for multi-user,
greetd and NetworkManager, verifies desktop entry points/configuration, and
checks that SSH is not running. It intentionally does not assert that a graphical
Hyprland session works. Keep the following interactive desktop gate separate.

## 3. Interactive desktop VM

```sh
nix build .#vm
mkdir -p .vm
cd .vm
../result/bin/run-nascent-vm-vm
```

`packages.<host-system>.vm` chooses ARM Linux for an ARM host and x86 Linux for an
x86 host. VM CPU/RAM/disk defaults are in `hosts/vm/default.nix`. QEMU is supplied
by Nix. The launcher creates only a local guest disk in the current directory;
run it inside `.vm/`. No host disks are attached and no inbound ports are forwarded.
Log in as `nascent` / `nascent`; sudo uses that same password. This VM is disposable
and its public password must never be carried to a physical host.

Check these before treating the desktop as usable:

- Log in through greetd; confirm there are no config errors (`hyprctl configerrors`).
- Open two terminals, tile/focus/move them and switch workspaces.
- Open fuzzel and Firefox; confirm Waybar, notifications and network access.
- Play audio, check file chooser/screen sharing portals, lock and unlock.
- Add an override to `~/.config/nascentos/hyprland.lua`, reload and confirm it applies.
- Exit and log in again; check that session processes clean up.

The VM uses software rendering. Physical GPU behavior, suspend/resume, multiple
monitors and NVIDIA drivers require a later hardware gate. VM success cannot
establish those properties. Keep `.vm/` between runs for guest home persistence;
move it aside to start a fresh guest without deleting prior state.

## Current Mac path

The development host inspected on 2026-10-22 is **aarch64-darwin (Apple Silicon)**.
Nix 2.35.2 is at `/nix/var/nix/profiles/default/bin/nix`; it was absent from PATH.
No standalone QEMU, Lima or Tart command was found on PATH.

The ARM Mac `vm` output uses NixOS's standard `virtualisation.host.pkgs` support:
QEMU/launcher run on Darwin and the guest is aarch64-linux. Nix still needs Linux
build products. Binary cache hits can supply some of these, but local/custom
Linux derivations require a configured **aarch64-linux builder**. This output is
not a cross compiler and does not silently provision another virtualization stack.
A Linux machine/VM with Nix is the simplest place to build and run the first
complete guest; a configured remote builder is another option. The automated
NixOS boot test also executes on Linux, not macOS.

Docker Desktop was subsequently found running an ARM64 Linux engine. A dedicated
task container now supplies Linux builds without changing host-wide Nix builder
settings. Native pinned QEMU was fetched and HVF initialization succeeded. The
ISO build and installation validation remain separate from that accelerator check.
The historical baseline ARM ISO completed a separate disposable Calamares
installation followed by installed-disk boot/login. The consolidated image has
its own verified installation/login/logout pass, recorded below; keep each
observation associated with its exact image identity.
See [vm-install-test.md](vm-install-test.md) for the task-local launcher and QMP
controls. x86 outputs remain available for later compatibility testing.
Build/evaluation status is recorded in [validation.md](validation.md).

## 4. Graphical installer VM gate

Build the matching `installer-aarch64` or `installer-x86_64` ISO described in
[install.md](install.md). Unlike the regular development VM, this gate must boot
the ISO with a **new disposable virtual target disk**, so installation cannot
modify the development guest or any host disk. Attaching disks and confirming
partition changes require deliberate review.

- Confirm the live session is nascentOS Hyprland, with no GNOME login requirement.
- Open **Install nascentOS**; inspect the hardware report, change the selected
  profile, and cancel once to verify that Calamares has not started.
- Reopen, select the appropriate profile and complete the Calamares flow using
  only the disposable disk. Verify locale, users, boot choice and the disk summary.
- Inspect the generated `/etc/nixos` files before rebooting: nascentOS source,
  desktop and hardware imports, selected profile, pinned flake and generated users
  must all be present. The target must not import the installer or VM modules.
- Eject the ISO, boot the installed virtual disk, log in with the account created
  in Calamares and repeat the interactive desktop checks above. Check that a new
  personal desktop configuration is writable and that live credentials were not
  inherited.

The historical baseline ARM64 ISO is identified by SHA-256
`cf016922176306ef515a02dd5c8bf51e21f20a1af03fe0bea9df99eeafb45c40`.
`scripts/check` and 34 Python tests passed. A separate disposable VM reached
Calamares **All done**, completing EFI/ext4 partitioning and `nixos-install`.
**Installed-disk boot and login passed in that separate test VM.** It started
with `--installed` and no ISO in the process arguments. Its root was `/dev/vda2`
(ext4), `/dev/vda1` mounted at `/boot` (vfat), no `sr0` existed, and EFI booted
generation 1. The fixture `vmtest` password worked at serial and graphical greetd
login. These are manual runtime observations, not an automated end-to-end GUI test.

Installed Hyprland ran without config errors, preserved `English (UK)` / `gb`,
and displayed Nord with the dithered home wallpaper. The screenshot is
`.vm/install-verify/installed-desktop.png`. No installer bar/button/command,
live marker or `nixos` account remained. `sudo -n` rejected passwordless access;
`vmtest` owned its writable Neovim `init.lua` (mode 644). Shared graphical,
nascent and wallpaper units were active with no failed system units. The
inference endpoint listened only on `127.0.0.1:11434`; no model behavior was tested.
The `--installed` launcher uses a nonempty `-boot menu=on` baseline to avoid the
Mac's Bash 3.2 empty-array failure.

The user-visible VM rebooted CD-first into the attached live ISO. Read-only disk
inspection confirmed `/etc/NIXOS`, the AArch64 systemd-boot and fallback EFI
binaries, and a generation-1 loader entry. Those files do not establish an
installed-system boot by themselves. A separate project task subsequently
recovered the user VM by booting its existing disk with `--installed` and verified
greetd's Username prompt. The user reported Hyprland started after login. Keep
that report distinct from the separate fixture VM's direct checks; this task
supplied no user credentials. See [validation.md](validation.md).

Live corrections include a bounded `xhost` root grant with cleanup around the
installer, shared session-bus/lifecycle handling, a modal-dialog maximize
restriction and the Nord-dithered home-photo wallpaper. Remaining nonfatal logs
include **No schemas installed**, sleep-inhibitor unavailability and unsupported
`chcon`; retain those in further test reports. Audio, lock-screen PAM unlock and
NVIDIA behavior still lack runtime proof; the consolidated fixture separately
verified password-login keyring unlock below. Repeat the graphical installation gate
on x86 before claiming equivalent coverage there.

## Consolidated image gate — ARM fixture passed

Current ISO4: `.vm/nascentos-arm64-integrated-fixed.iso`, SHA-256
`0a5e6839f1d8cd71a1e50a6daa86598deace69e1c60e55374b1fc17c7fd6cdfe`.
Its exact store/source identities are in [validation.md](validation.md). The
image includes the actual picker, AppImage infrastructure with no enabled
AppImage entries, mail/password/VPN/gaming integration, design resources and
Zsh/Oh My Zsh Boxfish. Release/CI files are present locally; remote execution is
not implied.

Consolidated validation passed 39 root, 43 picker, 16 AppImage, four mail, two VPN
and three release Python tests; native CLI and expanded ARM/x86 profiles; 12 Qt
widget tests per architecture; and eight native shell tests. The previous final
`scripts/check` stopped at a source-hash guard when documentation changed during
evaluation, an environment/source-stability interruption rather than a product
failure. The subsequent frozen-source rerun passed formatting, all-system
evaluation and the built native CLI tests; its log is `.vm/frozen-source-check.log`.
This documentation-only result update followed completion of that gate.

The real picker passed search, optional native selection, explicit Cursor
proprietary confirmation/removal and disabled ARM Slack checks. The installation
receipt selects `codex`, `fira-code`, `firefox`, `font-awesome`, `keepassxc`,
`neovim`, `open-dyslexic`; VPN `networkmanager`; gaming/GameMode/gamescope enabled,
with Steam, its extra session and mapping tuning disabled. Generated target
software/VPN/gaming modules and receipt match. No VPN connection or credentials
were activated.

Fresh live Zsh has no wizard and uses writable user-owned mode-600 configuration.
This image fixes ISO3's wizard using early global zshenv seeding with a root
guard; fresh-HOME positive/negative regression tests pass. All Calamares stages
through Install and its compact confirmation were observed. Record the remaining
Desktop ZIP placeholder, cropped square Welcome artwork and Summary translucency
as presentation limits rather than calling the UI flawless.

ISO4 reached Calamares **All done** after EFI/ext4 installation; evidence:
`.vm/install-verify/consolidated-finish-check.png`. The default launcher then
booted the installed `/dev/vda2` ext4 root with the ISO still attached, proving
the boot-priority fix. No live marker existed and serial password login started
Zsh without a wizard; see `default-boot-priority-test.png` and
`default-priority-installed.serial.log` in `.vm/install-verify/`.

A subsequent powered-off-to-`--installed` launch had no ISO process arguments or
`sr0`. Password greetd login entered Hyprland with empty config errors, preserved
English (UK)/`gb`, Nord and the dithered home wallpaper. All three session units
were active and no system units failed. The exact seven selected app/font IDs,
VPN and gaming flags above persisted. No live user/marker/installer command or
button, passwordless sudo, or external Ollama listener remained.

The installed fixture also verified these bounded checks:

- Codex 0.146.0, KeePassXC 2.7.12, GameMode 1.8.2 and gamescope 3.16.23 version
  output. KeePassXC opened on the real display through the user manager. A first
  TTY version attempt lacked DISPLAY; the corrected display-context check passed.
- Kitty running Zsh 5.9.1/Boxfish without a wizard; font matching returned
  OpenDyslexic sans and Fira Code monospace. Screenshot: `kitty-boxfish-runtime.png`.
- Agent GUI showing available Codex with no default selection; explicit fixture
  selection and `run --version` passed, then selection was restored to none.
  Screenshot: `installed-agent-only.png`. No provider authentication/request ran.
- Writable user-owned adapter mode 700, shell/theme files 600, Neovim init 644.
- A single GNOME keyring process owning `org.freedesktop.secrets`, default alias
  resolving to the login collection, and `Locked=false` after password login.
  No secret item contents or vault data were accessed.
- Super+Shift+E returning to greetd, with all three session units inactive and
  Hyprland/Waybar/mako absent. Screenshot: `consolidated-logout.png`.

Those screenshots are under `.vm/install-verify/`. This is a manual ARM fixture
installation/login/logout pass, separate from the user VM recovery and the
historical baseline. VPN connectivity, gameplay, model inference, vault-data
operations, provider login, audio and lock-screen unlock remain untested. Repeat
appropriate checks against any newly built image and before claiming x86 or
physical hardware equivalence. The final frozen-source check passed.

## Profile evaluation matrix

`checks.<linux-system>.profiles` forces complete NixOS derivation evaluation for:

| Profile | Architectures | What the gate verifies |
| --- | --- | --- |
| Portable desktop | ARM64, x86_64 | Common desktop without a model service |
| CPU local AI | ARM64, x86_64 | Loopback endpoint, no firewall opening/model downloads; x86 also evaluates personal CLI packages |
| Personal desktop apps | x86_64 | Native and selected proprietary package attributes/license allowance |
| NVIDIA + CUDA local AI | x86_64 | Optional driver/module and CUDA runtime selection |
| Selected software and fonts | ARM64, x86_64 | Catalog defaults, native overrides and selected-only package/license behavior |
| Mail, passwords and VPN | ARM64, x86_64 | Combined target options, single password-manager ownership and provider separation |
| Gaming profiles | ARM64, x86_64 | Free components; Steam remains an explicit x86-only choice |

These are configuration tests, not simulated NVIDIA/Intel/AMD GPUs. Mesa/virtual
GPU behavior is exercised only by the later interactive VM gate. Microcode,
firmware, storage, graphics, suspend and model performance need actual hardware.

Hardware detector fixtures should exercise generic Intel/AMD/virtual graphics,
modern/older NVIDIA, hybrid GPUs and Apple/Qualcomm platform warnings. They verify
recommendations and refusal/ownership behavior using synthetic sysfs trees; they
do not emulate GPU drivers. Installer handoff fixtures verify generated target
imports and pin preservation independently of actual disk writes. Run the
physical gate only on a deliberately selected machine after the disposable VM
installation succeeds; device firmware, graphics and boot support remain per-host
concerns.
