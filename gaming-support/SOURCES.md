# Provenance and adaptation record

Adapted on 2026-10-22 from Garuda Nix Subsystem commit
[`026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d`](https://github.com/garuda-linux/garuda-nix-subsystem/tree/026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d).
The upstream authors are the Garuda Nix Subsystem contributors. Its root
[LICENSE](https://github.com/garuda-linux/garuda-nix-subsystem/blob/026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d/LICENSE)
is GPL version 3; the two adapted files have no individual copyright/SPDX notices.
The unmodified license text is preserved in `licenses/Garuda-GPL-3.0.txt`.

`default.nix` retains GPL-3.0-only provenance. Modifications: replace `garuda-lib`
and the Garuda namespace with an independent NixOS module; split bundled choices;
keep Steam opt-in; add architecture/dependency assertions; omit blanket tuning;
expose only mapping compatibility as a separate option. Original tests/docs are
under the repository's AGPL-3.0 license. The root license is unchanged. GPLv3
section 13 addresses combination with AGPLv3; upstream notices must remain when
this adaptation is integrated or redistributed.

## Exact Garuda behavior and disposition

| Pinned source | Upstream behavior | nascentOS disposition |
| --- | --- | --- |
| [gaming.nix](https://github.com/garuda-linux/garuda-nix-subsystem/blob/026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d/internal/modules/base/gaming.nix) | GameMode, Steam, Steam gamescope session, CachyOS settings + gaming together | Retain GameMode; add independently usable nested gamescope. Steam and its additional session become separate opt-ins. No CachyOS import. |
| [performance.nix](https://github.com/garuda-linux/garuda-nix-subsystem/blob/026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d/internal/modules/base/performance.nix) | `vm.max_map_count=16777216` | Exact value retained behind a separate false-by-default compatibility option. |
| performance.nix | ananicy-cpp/Cachy rules and semaphore cleanup, irqbalance, permanent performance governor, AMD ppfeaturemask, EPP/PCIe/GPU performance writes | Omitted: unrelated global scheduling/power/driver policies need per-host measurement. |
| performance.nix | SATA power and drive sleep settings, storage schedulers, zram zstd/90%, swappiness180/page-cluster0, watchdog/scheduler/network sysctls | Omitted: memory/storage/power tradeoffs and broad kernel behavior are outside a game launcher profile. |
| performance.nix | hdparm package, systemd-oomd slices/20s pressure, bpftune enabled even outside performance toggle | Omitted: importing the entire file would change unrelated systems even when tuning is off. |

Garuda uses `gDefault = mkOverride 950`; component enables use conventional
`mkDefault` (priority 1000). The mapping setting retains priority 950 to override
NixOS's own priority-1000 default; ordinary host definitions still take precedence. It does
not reuse the Garuda module framework, Plasma, Home Manager, cache trust, Nyx
package overlays or an unstable channel input.

## Inspected transitive sources (not incorporated)

Garuda's pinned [flake.lock](https://github.com/garuda-linux/garuda-nix-subsystem/blob/026ee24cc48ce1eb58eadfa098e3a8fa2b4e663d/flake.lock)
resolves:

- [ksv-cachyos-settings-nixos `efd9d8e44e107c806070185d5d9ee2d0f02b8cb5`](https://github.com/vivekanandan-ks/ksv-cachyos-settings-nixos/tree/efd9d8e44e107c806070185d5d9ee2d0f02b8cb5),
  translating the CachyOS settings into NixOS. No root license or per-module
  notice was found in the inspected tree; no code from this project is copied.
- [CachyOS-settings `4bcb3e3bf8a0c6763dbd935d14430c60d7ff5a37`](https://github.com/CachyOS/CachyOS-settings/tree/4bcb3e3bf8a0c6763dbd935d14430c60d7ff5a37),
  GPLv3 (`LICENSE.md`). Inspected for the translated tuning/tools' behavior.
- [Chaotic Nyx `52e7e4e599f1366a95960b1bd65e0bb8df270834`](https://github.com/chaotic-cx/nyx/tree/52e7e4e599f1366a95960b1bd65e0bb8df270834),
  MIT, Copyright (c) 2023 Pedro Henrique Lara Campos. Inspected for Garuda's
  package/module context; no Nyx source is incorporated. Garuda imports Nyx
  globally; its default module enables the Nyx overlay and binary cache, and
  Garuda follows Nyx's unstable Nixpkgs. None is imported by this module.

In ksv's `fpModules/nixos/cachyos-settings.nix`, `enableAll` defaults to `enable`.
Consequently Garuda's gaming switch enables all eight submodules under
[`fpModules/nixos/`](https://github.com/vivekanandan-ks/ksv-cachyos-settings-nixos/tree/efd9d8e44e107c806070185d5d9ee2d0f02b8cb5/fpModules/nixos):
`sysctl.nix`, `zram.nix`, `systemd.nix`, `tmpfiles.nix`, `modprobe.nix`,
`udev.nix`, `audio-pam-limits.nix`, `tools.nix`.

This entails memory/dirty-page/network/file limits, zram100% and zswap disablement,
shorter shutdown timeouts, NOFILE/cgroup/journal settings, transparent huge-page
and coredump policies, driver/watchdog options, PCI latency and storage power/
scheduler writes, and audio-group real-time limits with normal-user membership.
The NVIDIA system-memory allocation setting carries an upstream security warning;
it is not suitable as an assumed RTX 3080 optimization. None is adopted here.

The gaming-specific additions load `ntsync` and install `game-performance`,
`dlss-swapper`, `dlss-swapper-dll`, `zink-run` (tools also add `topmem`/`kerver`).
`game-performance` takes a power-profiles performance lease and optionally inhibits
sleep; the DLSS helpers replace/force DLSS choices (one enables the NGX updater);
`zink-run` forces Mesa/EGL selection. They are omitted: they add driver, kernel,
proprietary-library and power-policy assumptions beyond native GameMode. `ntsync`
can be considered later with kernel/Proton testing rather than loaded on every
ARM/x86 target. The optional max-map value above comes directly from Garuda's
licensed performance module, not from copying the ksv translation.

## Runtime package licenses

At the prototype's Nixpkgs pin, GameMode is BSD-3-Clause and gamescope BSD-2-Clause;
Steam is `unfreeRedistributable`. Those packages retain their own notices through
Nixpkgs. This configuration does not grant rights to Steam, DLSS, games or other
third-party content and adds no acceptance flags.
