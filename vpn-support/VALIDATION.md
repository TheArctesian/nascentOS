# Validation record — 2026-10-22

Host: aarch64-darwin. Pinned nixpkgs:
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`.

| Gate | Result |
| --- | --- |
| Python unittest adapter suite | PASS: optional selection, platform filtering, invalid IDs, multiple selections, injected strings, unsupported host/IVPN architecture |
| nixfmt `--check` on all three Nix files | PASS |
| `nix eval --json ./vpn-support#validation` | PASS: nine supported provider/system profiles, zero failed NixOS assertions |
| Installed dependency derivation evaluation | PASS: 1,181 derivation references across the nine profiles (includes NixOS defaults, not unique package count); nothing realized |
| Catalog versus pinned package version assertions | PASS |
| Wrong-provider flags, invalid/multiple provider values, Proton plus Mullvad conflict, ARM IVPN | Rejected as expected |
| Shared keyring supplied by session | PASS |
| Direct composition with read-only foundation `51d8/nascentOS/modules` | PASS on aarch64-linux and x86_64-linux with desktop + Proton: no failed assertions; keyring, greetd PAM unlock and Waybar tray all enabled |
| `git diff --cached --check` | PASS |

Exact scoped commands are in README. Foundation composition used an impure Nix
expression importing its modules directly, avoiding the baseline's active VM
socket. No baseline/software-picker files were edited. The base commit in this
worktree has only the original project README/license, so there is no root
bootstrap or `scripts/check` to run here. The scoped gates above are the
changed-path checks; the final assembled repository must still run its own full
foundation checks.

Not performed: Linux package realization, graphical launch, VM boot, provider
login, public IP/DNS/IPv6 tests, kill-switch traffic checks, autoconnect/reboot,
split routing, or live account connectivity. No claim of verified leak protection
is made. See README's runtime acceptance procedure.
