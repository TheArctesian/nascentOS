# Apple Silicon disposable installation test

This procedure builds Linux products in a dedicated Docker container and runs
the ARM64 ISO using native QEMU/HVF. It changes no host Nix configuration and
attaches only task-local image files. It requires Docker Desktop already running,
Nix, and sufficient free disk space for the builder store, ISO and installed disk.

## Native QEMU

```sh
nix --extra-experimental-features 'nix-command flakes' build \
  github:NixOS/nixpkgs/cd4ea8d57de16f4810bc5f14207bac45fbf19f67#qemu \
  --out-link .vm/qemu
```

Build the `nixosConfigurations.installer-aarch64.config.system.build.isoImage`
output inside an ARM64 Linux Nix container with a frozen source snapshot mounted
read-only. Use the repository lock file. Copy the resulting ISO out of the
container with `docker cp -L`; the result symlink itself is not portable.
For iteration, `packages.aarch64-linux.installer-dev` uses zstd level 3 instead
of the production ISO's level 19. This changes compression, not installed defaults.

## Boot and control

```sh
scripts/run-installer-vm .vm/nascentos-arm64.iso
```

The launcher creates `.vm/install-test/target.qcow2` (48 GiB sparse virtual
capacity) and persistent EFI variables. Subsequent runs reuse both files. The
Cocoa display shows the guest; these commands provide QMP input and screenshots:

```sh
python3 tools/vm-control.py status
python3 tools/vm-control.py screenshot live.png
python3 tools/vm-control.py key ctrl-alt-f2
python3 tools/vm-control.py type 'whoami
'
python3 tools/vm-control.py click 500 400
```

The keyboard helper assumes a US guest keyboard layout. Screenshots, QMP socket,
serial socket/log and PID file stay under `.vm/install-test/`. Localhost port
22222 forwards to guest SSH, which the ISO disables by default; a forwarding rule
alone does not enable access.

The launcher now gives the target disk first priority. A blank disk falls back
to the ISO; a completed disk should boot its installed system on restart. The
earlier CD-first launcher returned to the live installer after installation.
That does not require reinstalling or reformatting the existing disk.
For deliberate testing of a newer live image against an existing test disk,
`scripts/run-installer-vm --live ISO` explicitly prioritizes the CD. Use
`--installed` afterward; this development override keeps the ISO first until
the VM is stopped.

Complete Calamares against the sole virtual target disk. After a clean guest
shutdown, omit the ISO entirely to test the installed boot path:

```sh
scripts/run-installer-vm --installed
```

Use `NASCENT_VM_INSTANCE=install-verify` with the launcher and QMP helper to run a
separate headless verification guest (6 GiB RAM, port 22223, independent
`.vm/install-verify/` disk/EFI variables/sockets). The default visible session uses
8 GiB and port 22222. Never direct verification input to a session handed to the
user. `tools/vm-serial.py 'COMMAND'` is deliberately restricted to the verification
guest and returns its command exit status. Keep enough disk space for the new
ISO and installed store, in addition to the existing live session.

Follow the acceptance checks in [testing.md](testing.md). Record actual observed
results separately from source evaluation, including any runtime failures and
fixes. A launcher or successful image build does not establish an installation
pass.
