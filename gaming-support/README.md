# Optional gaming support

Import `gaming-support/default.nix` into the **installed target**, then select the
profile explicitly. Merely importing it changes no gaming services or packages.
This directory is independent of the installer and uses the target's pinned
Nixpkgs; it adds no flake inputs, overlays, cache keys or Home Manager dependency.

```nix
{
  imports = [ ./gaming-support ]; # Adjust relative to the target configuration.
  nascent.gaming.enable = true;
}
```

This selects the free GameMode and gamescope components. GameMode is Feral's
on-demand daemon, not a Windows Game Mode UI or an automatic per-game detector.
Launch a game with `gamemoderun /path/to/game`, or use Steam's per-game launch
option `gamemoderun %command%`. GameMode's upstream defaults can temporarily
request CPU governor/power changes; this module adds no GPU overclock settings,
custom scripts or permanent performance governor. The NixOS module supplies
polkit integration and its default `CAP_SYS_NICE` wrapper. Host policy can use
`programs.gamemode.enableRenice = false` or configure `programs.gamemode.settings`.

Use `gamescope -- /path/to/game` for an optional nested compositor. No blanket
wrapping, GPU environment variables, real-time gamescope capability, HDR flags,
portal replacement, display-manager change or input remapping is applied.
Actual gamescope/Wayland/driver compatibility needs hardware testing.

Steam is proprietary and **off by default**, including on x86. Explicit selection:

```nix
nascent.gaming = {
  enable = true;
  steam.enable = true;
  # Optional extra session entry; leave off for the existing Hyprland workflow.
  steam.gamescopeSession.enable = true;
};
```

Steam selection permits only `steam` and `steam-unwrapped` through Nixpkgs'
additive `allowUnfreePackages` list. It does not enable `allowUnfree`, alter other
license predicates, accept Valve agreements, log in, download games or enable
remote-play/LAN-transfer firewall ports. Installing Steam includes its bootstrap;
launching it may download/update its client and present Valve terms. The target
Nixpkgs must support `allowUnfreePackages` (the tested pin does). If a caller
supplies `nixpkgs.pkgs`, the caller must apply this license allowance there.

The Steam module handles 32-bit graphics/audio and Steam controller udev rules.
It remains x86_64 Linux only: native ARM GameMode/gamescope support does not make
x86 Steam, Proton, Windows games or NVIDIA CUDA work on ARM. Package metadata is
checked for GameMode/gamescope; Steam needs an explicit x86_64 restriction because
its pinned package metadata does not declare a useful platform list. Metadata
availability is not proof that every dependency builds or every device works.

For a game that demonstrably needs more memory mappings, opt in separately:

```nix
nascent.gaming.tuning.maxMapCount.enable = true;
```

This adopts Garuda's `vm.max_map_count = 16777216`, system-wide. It can prevent
mapping-limit failures, does not preallocate that many mappings, and is not a
performance benchmark. All other Garuda/CachyOS tuning is omitted; see
[SOURCES.md](SOURCES.md). Native NixOS options remain available for host-specific
choices; the component enables use `mkDefault`, while the max-map value uses Garuda's
priority 950 to override NixOS's existing priority-1000 default (1048576).

## Installer integration contract

No picker files or root flake have been changed. The coordinator should import
this module in generated **target** configurations only and emit the following
options from independent selection state:

| Selection | Target option | Default | Availability |
| --- | --- | --- | --- |
| Gaming support | `nascent.gaming.enable` | false | Linux; tested ARM64/x86_64 eval |
| GameMode | `nascent.gaming.gamemode.enable` | follows profile | Nixpkgs metadata |
| gamescope | `nascent.gaming.gamescope.enable` | follows profile | Nixpkgs metadata |
| Steam (proprietary) | `nascent.gaming.steam.enable` | false | x86_64-linux only |
| Steam gamescope session | `nascent.gaming.steam.gamescopeSession.enable` | false | Requires Steam + gamescope |
| Mapping compatibility tuning | `nascent.gaming.tuning.maxMapCount.enable` | false | Requires profile |

The master profile must be selected before any component. Clearing it must clear
all child selections (or emit none). Reject unsupported Steam and invalid session
combinations before installation; the module also asserts them. The picker should
label Steam proprietary and keep it unchecked. Emit module options, not duplicate
packages: installing `pkgs.steam` alone loses NixOS's device/runtime integration.
Do not add these components to live ISO contents or silently select them based on
GPU detection. No model, GPU brand, desktop theme or NVIDIA driver is chosen here.
The existing category catalog can route its gaming choice to this contract without
making it depend on the module's implementation.

## Validation

Run `./gaming-support/tests/check` from any directory. It uses the copied
prototype lock (Nixpkgs `cd4ea8d57de16f4810bc5f14207bac45fbf19f67`) without
reading or copying a live worktree. No new system packages need bootstrapping
beyond Nix with flakes; the script enables the required features. It evaluates
complete NixOS toplevel derivations, not builds or boots. The existing root gate
is absent from this isolated branch; the coordinator must run its final assembled
`scripts/check` and Linux/installer gates after integration.

Evaluation covers disabled import, free profile on ARM64/x86_64, x86 Steam with
session and mapping tuning, narrow license policy coexistence, native overrides,
ARM Steam rejection, orphan child/session rejection and Hyprland/greetd/portal
configuration coexistence. See [tests/VALIDATION.md](tests/VALIDATION.md).

Before claiming working gaming support, boot a Linux target and check:

1. Log into the existing Hyprland session; test file chooser/screen sharing,
   audio, keyboard, mouse, controller, lock/unlock and suspend/resume.
2. Run `gamemoded -t`, then launch a real game with `gamemoderun`; inspect
   `gamemoded -s` while it runs and after it exits. Check policy changes restore.
3. Test a native game in nested gamescope, including pointer capture, resolution,
   fullscreen transitions and returning to the desktop.
4. On a selected x86 Steam target, accept any required terms yourself; test the
   client, a native game, a chosen Proton title and 32-bit graphics/controller
   input. Test the extra Steam session only if deliberately selected and the
   actual greeter exposes session entries (greetd needs its own chooser).
5. Test the actual GPU/driver, multi-monitor and VRR/HDR choices separately.
   An RTX 3080 is a possible future target, not a verified or hardcoded device.

A software-rendered VM cannot establish GPU, frame pacing, thermal or power
behavior. No benchmarks or hardware-runtime success are claimed here.
