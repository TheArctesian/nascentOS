# Software selection Nix gates

Use the repository's pinned nixpkgs source (revision
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`), with Nix and its `nix-command`
feature available. These gates evaluate configuration and derivations; they do
not build applications, download AppImages, or start the updater.

```sh
for system in x86_64-linux aarch64-linux; do
  for test in nix-eval appimage-eval; do
    nix --extra-experimental-features 'nix-command flakes' eval --impure --json \
      --file "installer/software-selection/tests/$test.nix" \
      --apply "test: test { nixpkgs = /absolute/path/to/pinned/nixpkgs; system = \"$system\"; }" || exit
  done
done
```

`nix-eval.nix` exercises the real NixOS software module: known IDs, duplicate and
manual selection rejection, architecture availability, empty selection, narrow
unfree permission, native package derivations, Qt picker packaging and font
roles. It checks that Fira Code stays the coding monospace family when optional
OpenDyslexic becomes the UI sans family. Synthetic package metadata exercises
the missing, broken, wrong-platform and incorrectly labeled license gates.

`appimage-eval.nix` exercises `appimage-validation.nix` and
`appimage-integration.nix` with synthetic metadata only. It checks reviewed
complete metadata, exact versioned GitHub asset URLs and SHA-256 pins, native
platforms, known licenses, metadata types and proprietary labels. A declared
resolver option fixture verifies the service configuration mapping; a missing
resolver verifies the actionable module assertion. No AppImage is offered by
the production catalog.

These evaluations do not validate a Linux GUI runtime, a Calamares installation,
or the separate updater's download and activation behavior.
