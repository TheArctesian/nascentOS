# Validation — 2026-10-22

Host: aarch64-darwin. Nix invoked explicitly from
`/nix/var/nix/profiles/default/bin/nix`, with `nix-command flakes` enabled.
Package source: baseline flake.lock revision
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`, resolved to
`/nix/store/x605rbj3d9bjxd3zdnqy0iphq7g6ly50-source`.

Passed:

- Four Python catalog merge tests.
- Pinned nixfmt check on all five mail Nix files.
- `tests/eval.nix` on x86_64-linux and aarch64-linux: module assertions,
  service dependencies, no Bridge autostart, mapping, MIME defaults and real
  selected client/Bridge/handler derivation evaluation.
- `tests/picker.nix` against an assembly copy of the real merged picker on
  both architectures: architecture availability, x86 Proton default, no ARM
  substitute, Thunderbird + Bridge selection and Bridge-only selection.
- All 34 Python tests from the picker in that assembly copy.
- Baseline `./scripts/check` in the temporary assembly: formatting,
  `nix flake check --no-build --all-systems` and the host CLI check build.

The assembly copy imported the picker and mail adapter from modules/default.nix
and merged the mail catalog before evaluation. Its location was
`/var/folders/pv/p2kd10rn273718pvbvzd1vjc0000gn/T/nascent-mail-assembly-g4byde84`.
No files in the running baseline or picker worktrees were edited. The assembly
was a source snapshot, not a merge into the final baseline. Later changes in
those separate chats require integration checks again.

An initial attempt to snapshot the baseline with `nix flake metadata path:...`
failed because that active checkout contains a QMP socket. The package pin was
instead resolved directly from the lock's GitHub revision. The first temporary
assembly gate failed because the copy omitted `agents/skills`; adding the
required `agents/` and `lib/` source directories fixed the copy and the gate
then passed. Neither failure was hidden or counted as a pass.

Not performed: Linux client builds or launches, graphical installer interaction,
Nord/Wayland/notification verification, Secret Service/PAM unlock, account login,
mail sync/send/receive or a boot test build. No account data, credentials or
secret environment files were read. Package metadata support does not certify
upstream NixOS/ARM support. The README lists the remaining runtime checks.
