# Validation record — 2026-10-22

Host: aarch64-darwin. Evaluator: Nix 2.35.2, flakes enabled per command.
Nixpkgs: `cd4ea8d57de16f4810bc5f14207bac45fbf19f67`, copied prototype
`flake.lock` with original nar hash. No Garuda, Nyx or CachyOS input is evaluated
or trusted by the tests.

Passed:

- `./gaming-support/tests/check`: full NixOS toplevel derivation evaluation for
  disabled x86 import, free ARM64 and x86 profiles, x86 Steam/session/tuning,
  independent GameMode/gamescope/Steam-only selections, ARM Hyprland/greetd/portal
  coexistence. Checks native enable overrides, a host mapping-limit override,
  Steam 32-bit graphics integration and closed default Steam firewall options.
- Assertion checks: ARM Steam, a session without Steam, and child enablement with
  the master disabled are rejected. These inspect assertions without forcing an
  invalid Steam package on ARM.
- License checks: no unfree allowance from the free profile, only two permitted
  Steam names when selected, and an existing software-picker-style
  `allowUnfreePredicate` remains intact.
- `nixfmt --check gaming-support/default.nix gaming-support/tests/eval.nix`
  using the prototype pin's nixfmt 1.5.0.
- `shellcheck gaming-support/tests/check` and `bash -n gaming-support/tests/check`.

No Linux build, VM boot, installation, hardware/driver test, GameMode runtime
activation, power-policy restoration, controller capture, Steam login or game
benchmark was performed. An evaluated `.drvPath` confirms configuration and
package graph evaluation only. No claims about FPS or reduced latency follow.
The runtime checklist is in the parent README.

The isolated checkout has no root `scripts/check`, root flake or documented
bootstrap beyond the original two-line README. Nix is already installed; the
changed-directory gate handles its non-PATH installation and required features.
The assembled repository's existing root gate, installer handoff tests and Linux
boot/manual hardware gates remain the coordinator's responsibility.
