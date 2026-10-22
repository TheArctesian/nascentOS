# Mail support

Scoped addition for final assembly, checked on 2026-10-22. This worktree does
not modify the baseline VM or the separately owned software picker. No Home
Manager, Flatpak, account login, account provisioning or mail inspection.

## Choices at the baseline lock

Pinned nixpkgs: `cd4ea8d57de16f4810bc5f14207bac45fbf19f67` (read from
the baseline's flake.lock). All choices use existing nixpkgs packages; no
AppImage fallback is necessary or claimed.

| Picker ID | Package/version | x86 Linux | ARM Linux | Role |
| --- | --- | --- | --- | --- |
| protonmail-desktop | protonmail-desktop 1.13.0 | yes | unavailable | Preferred/default Mail + Calendar client |
| protonmail-bridge | protonmail-bridge-gui 3.24.2 | yes | yes | Optional IMAP/SMTP adapter, not a reader |
| thunderbird | thunderbird 157.0.1 | yes | yes | Alternative reader; Proton needs Bridge |
| geary | geary 46.0 | yes | yes | Alternative reader; Proton needs Bridge, unofficial pairing |
| evolution | evolution 3.60.2 | yes | yes | Alternative reader; Proton needs Bridge, unofficial pairing |

These are metadata/evaluation results, not successful Linux application builds.
The Proton Desktop package repackages the official, hash-pinned DEB with Nix's
Electron runtime. Bridge is built from Proton's source (with nixpkgs GUI patches).
All five package licenses are free software licenses; a paid service requirement
does not make the package license proprietary. The catalog records exact source
paths, versions, descriptions and license labels for the installer.

Proton's [desktop documentation](https://proton.me/support/mail-desktop-app)
still calls Linux beta. It requires a paid or trial Mail plan, with a 14-day
trial for free accounts. Its [Linux setup page](https://proton.me/support/set-up-proton-mail-linux)
names Ubuntu/Fedora as supported systems; NixOS is community packaging, not an
officially supported Proton distribution. Those pages differ in which Ubuntu
release they name, so no precise upstream distro-version guarantee is inferred.

[Bridge](https://proton.me/support/bridge-for-linux) needs a paid plan including
Mail and a working Secret Service credential store or Pass. Proton's current
[tested clients list](https://proton.me/support/clients-supported-bridge) names
**Thunderbird only on Linux**. Geary/Evolution remain useful supported nascentOS
package choices for other providers; their Proton compatibility is not certified.
The ARM Bridge entry reflects nixpkgs source-build support, not an official
Proton ARM binary or a tested ARM login. Proton Desktop does not use Bridge.

## Assembly interface

Copy this directory as `mail-support/` at the repository root. In the final
assembly copy, once the picker directory is present, run:

```sh
python3 mail-support/merge-catalog.py installer/software-selection/catalog.json
```

This merges the five IDs exactly once, checks the revision/schema and rejects
duplicates. It edits the picker's single source catalog so GUI manifests, root
validation, target receipts and target package resolution all see identical
entries. Do not merge only the display manifest. Existing picker availability
checks disable Proton Desktop on ARM; its default selection logic includes only
available entries. ARM therefore has no implicit substitute mail reader: choose
Thunderbird + Bridge for Proton with a paid plan, or use Proton in the browser.
On x86, only Proton Desktop is preselected; Bridge and other readers stay opt-in.

Import `../mail-support/installer-adapter.nix` alongside the software module in
`modules/default.nix`. The adapter imports the standalone mail module and
consumes `nascent.software.enable` / `nascent.software.selected`; neither is
required when importing the standalone module. The installed system must copy
both source directories. `selection.nix` maps only mail IDs, with default priority
Proton, Thunderbird, Geary, Evolution, independent of click order. Multiple
readers remain permitted. Bridge alone installs its setup GUI without assigning
it the mailto handler. Empty mail selection installs no client here.

The software module and mail module may both list the same selected derivation;
Nix deduplicates it in the system environment. Geary/Evolution also activate
their upstream NixOS modules for required D-Bus/dconf/data-server integration.
They do not enable a GNOME desktop. No clients are downloaded merely to show
their catalog rows.

Standalone or later system configuration:

```nix
imports = [ ./mail-support/default.nix ];
nascent.mail = {
  enable = true;
  clients = [ "protonmail-desktop" ]; # x86 only; explicit ARM use fails clearly
  defaultClient = "protonmail-desktop";
  bridge.enable = false;
};
# For Proton with Thunderbird on either architecture:
# clients = [ "thunderbird" ]; defaultClient = "thunderbird";
# bridge.enable = true;
```

`nascent.mail.bridge.credentialStore = "gnome-keyring"` is the default. It sets
the shared `services.gnome.gnome-keyring.enable = true` option also used by the
password task; repeated assignments to that same service do not create competing
providers. The password/desktop assembly owns PAM unlock/session validation.
Use `"existing"` to leave Bridge's provider setup to an existing Secret Service
or Pass configuration. Proton Pass is the preferred personal vault but is not
assumed to implement Secret Service. Geary/Evolution upstream modules also need
GNOME Keyring regardless of Bridge's credentialStore setting.

Only selected clients receive small `nascent-mail-<id>.desktop` launchers, with
store-qualified executables and `%u` URI forwarding. The system mailto default
points to the selected launcher's exact desktop ID. These URI handlers use
`NoDisplay=true` so the upstream application has only one visible menu entry.
Per-user `mimeapps.list`
overrides continue to work; no user profiles, accounts, preferences or themes
are overwritten. Proton documents its [mailto support](https://proton.me/support/set-default-email-handler).
No `.eml` handler is assigned to Proton because file opening was not verified.

Bridge is installed, but no system/user autostart service is enabled here. After
login, open Bridge, sign in yourself, and follow the [official setup guide](https://proton.me/support/protonmail-bridge-install).
Use the IMAP/SMTP credentials shown by Bridge in the client, not your Proton
account password. Keep Bridge running during mail use. Nothing stores these
credentials in Nix or exports them to the installer. Session autostart can be
configured later in writable user settings after successful manual setup.

## Validation

No bootstrap exists in this minimal starting checkout beyond Nix itself. Use
`/nix/var/nix/profiles/default/bin/nix` if Nix is missing from PATH. Run
`python3 -m unittest discover -s mail-support/tests -v`, Nix formatting and:

```sh
nix eval --impure --json --expr 'import ./mail-support/tests/eval.nix { nixpkgs = /path/to/pinned-nixpkgs; system = "x86_64-linux"; }'
# Repeat for aarch64-linux.
nix eval --impure --json --expr 'import ./mail-support/tests/picker.nix { nixpkgs = /path/to/pinned-nixpkgs; system = "x86_64-linux"; pickerRoot = /path/to/assembly/installer/software-selection; }'
# The picker test requires the merged assembly catalog; repeat for ARM too.
```

Tests cover empty/disabled selections, invalid defaults, duplicates, ARM
rejection, shared keyring, no Bridge autostart, Geary/Evolution service setup,
picker mapping and real package derivation evaluation. After assembly also run
the baseline's `scripts/check`, picker tests, and its documented graphical VM
gate. On both Linux architectures verify selected launchers, `xdg-mime query
default x-scheme-handler/mailto`, `xdg-open 'mailto:example@example.invalid'`
(do not send), user MIME overrides, Nord readability, notifications and
shared keyring unlock after a fresh login. Runtime login/sync/send behavior
requires the user's later account setup and is not tested here.
