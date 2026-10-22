# Installer software selection

This directory is an independently reviewable addition to the nascentOS
installer. It does not alter the separate baseline VM build. The graphical
step runs **before** Calamares, in the existing hardware-review launcher; it
is not an embedded Calamares ViewStep. The existing desktop chooser remains
unchanged. Cancelling this step does not start Calamares or change disks.

`catalog.json` holds stable IDs, categories, package attributes, source backend,
license labels, platform limits and defaults. `availability.nix` evaluates the
catalog against the image's actual package set. The GUI and root helper use
that same evaluated manifest. No optional application is downloaded to display
its icon: `package.nix` uses the pinned Papirus theme. Missing theme marks use
an ordinary computer symbol rather than an invented logo. See `SOURCES.md` for
package, architecture, font and icon evidence.

Defaults are Neovim, Firefox, Fira Code and Font Awesome. LazyVim remains the
baseline's writable user configuration. Large creative apps are optional.
OpenDyslexic changes the fontconfig interface sans-serif preference only; code
retains Fira Code. Applications with their own font setting may need a separate
writable setting. A selected proprietary app requires an explicit inclusion
confirmation; this does not accept its upstream contract or activate a license.
Manual entries show setup information and cannot be selected for installation.

## Integrate after the baseline VM gate

Copy this directory into the source snapshot that the installed system receives.
Keep these source files tracked in Git when building a flake from a Git checkout.
No changes to the root flake or README are required by this directory alone.

1. In `modules/installer/default.nix`, rename the current patched `extensions`
   binding to `baseExtensions`. Add these bindings in the existing `let` block:

   ```nix
   software = import ../../installer/software-selection/package.nix { inherit pkgs; };
   extensions = import ../../installer/software-selection/extension.nix {
     inherit pkgs;
     extensions = baseExtensions;
   };
   ```

   Continue passing `extensions` to `pkgs.calamares-nixos.override`. The added
   override runs **after** the existing nascentOS patch. It copies the software
   handoff beside `nascent_install` and inserts `install_software(...)` inside
   the existing checked install job, after `prepare(...)` and before
   `nixos-install`. Changed/missing patch anchors abort the package build.

2. Add `software` to the launcher's `runtimeInputs`. After hardware recording
   and before `exec pkexec .../bin/calamares`, add:

   ```bash
   choices=$(nascent-software-picker) || exit 0
   if ! printf '%s' "$choices" | pkexec ${software}/bin/nascent-software-record; then
     zenity --error --text='Software choices could not be saved. Restart Install nascentOS.'
     exit 1
   fi
   ```

   `writeShellApplication` supplies `pipefail`; do not remove it. Use the
   absolute store path in `pkexec`, as shown. The GUI runs as the live user;
   only the validated record helper and Calamares run with privilege.

3. Import `../installer/software-selection/integration.nix` from `modules/default.nix` (path
   relative to that file). The target handoff
   also imports it through `nascent-software.nix`; Nix deduplicates identical
   module paths. The options exist in both live and installed configurations,
   but `nascent.software.enable` is enabled only for the installed selection.

4. Reconcile baseline packages and launchers. The current desktop installs and
   wraps Firefox unconditionally, and `nascent-browser` invokes Firefox. Make
   those honor the selected browser (or `xdg-open` with a selected browser's
   desktop association), retaining Firefox on the live image. Neovim is a
   baseline tool; either mark it required in product copy or remove its
   unconditional package when the software profile owns editor installation.
   An explicit empty profile adds no packages here; it cannot remove packages
   supplied by other modules. The broad `nascent.apps.desktop` profile should
   stay off for picker installs, so optional applications remain optional.

5. The baseline's NVIDIA and broad unfree-app modules currently set global
   `nixpkgs.config.allowUnfree = true`. Narrow those to their explicitly enabled
   packages before claiming a selected-only unfree policy. This module supplies
   a predicate restricted to selected proprietary package names; a global true
   from another module still permits everything. Compose predicates for the
   chosen NVIDIA driver and selected app names when needed.

6. Replace the baseline's JetBrains Mono Kitty/theme font setting with Fira Code
   in its writable template. Fontconfig defaults cannot override an explicit
   Kitty `font_family`. Font Awesome is an icon font, not a text-font choice.
   Keep OpenDyslexic out of terminal/code font settings.

The root-owned `/run/nascent-installer/software.json` is private, atomically
replaced, architecture checked and bound to the evaluated manifest digest.
During installation, `handoff.install()` verifies the copied source's catalog
**and actual flake lock** revision, validates all IDs and proprietary inclusion
records again, then writes:

- `/etc/nixos/nascent-software.nix`, a real import and selected-ID list;
- `/etc/nixos/nascent-software.json`, an auditable receipt;
- the software module import in Calamares's generated `configuration.nix`.

Users can later edit `nascent.software.selected` in the target configuration and
rebuild the system flake. No Home Manager configuration or user dotfiles are
made immutable by this feature.

## Additional source backend contract

Prefer `backend = "nixpkgs"` whenever a native package exists. A Nix-wrapped
AppImage fallback belongs only to a reviewed catalog entry when no suitable
native package exists. The separate AppImage infrastructure task owns its
resolver, timer, pinned updates and rollback; this directory does not implement
a second updater. There are currently no enabled AppImage entries. ArtCraft
is excluded until an official Linux release and packaging can be verified.
Flatpak was not selected for this implementation.

Keep the final source layout as `installer/software-selection/` and
`appimage-support/` directly below the repository root. `integration.nix`
imports `../../appimage-support/module.nix` when that separately supplied
directory is present. It does not duplicate the resolver. Its absence permits
native-only operation, but selecting an AppImage then fails an assertion.
Both directories must be in the source copied into the installed system before
enabling an AppImage entry. The typed resolver contract is:

```nix
services.nascentAppImages = {
  enable = true;
  apps.example = {
    displayName = "Example";
    repository = "owner/repo";
    assetName = "Example-{tag}-x86_64.AppImage";
    platform = "x86_64-linux";
    license = "mit"; # key in lib.licenses
    pin = { version = "v1.0"; url = "https://github.com/owner/repo/releases/download/v1.0/Example-v1.0-x86_64.AppImage"; hash = "sha256-..."; };
    autoActivate = true;
    maxBytes = 1073741824;
  };
};
```

Catalog source URLs are evidence, not executable download commands. Do not
turn manual entries into installable choices merely by adding an upstream URL.

## Validation

The starting repository in this worktree contains only its root README and
license; the baseline's `scripts/check` is outside this worktree. It must run
again after integration. This directory's checks require Python 3, Nix with
`nix-command flakes`, the pinned nixpkgs source, and PySide6 for GUI checks.
Missing dependencies are environment failures. Do not treat skipped Qt/VM
checks as a runtime pass.

```bash
python3 -m unittest discover -s installer/software-selection/tests -v
nixfmt --check installer/software-selection/*.nix installer/software-selection/tests/nix-eval.nix
nix eval --impure --json --expr 'import ./installer/software-selection/tests/nix-eval.nix { nixpkgs = /path/to/pinned-nixpkgs; system = "x86_64-linux"; }'
nix eval --impure --json --expr 'import ./installer/software-selection/tests/appimage-eval.nix { nixpkgs = /path/to/pinned-nixpkgs; system = "x86_64-linux"; }'
# Repeat with system = "aarch64-linux".
nix eval --impure --json --expr 'import ./installer/software-selection/availability.nix { pkgs = import /path/to/pinned-nixpkgs { system = "aarch64-linux"; }; }' > /tmp/manifest.json
QT_QPA_PLATFORM=offscreen python installer/software-selection/tests/gui.py /tmp/manifest.json -v
```

For local UI inspection when a Linux Nix build is unavailable, create a temporary
Python venv and install `PySide6_Essentials`; this is a test-only dependency, not
the product packaging. The product uses pinned nixpkgs `python3Packages.pyside6`.
`picker.py --manifest /tmp/manifest.json --icon-path /path/to/Papirus/share/icons
--screenshot /tmp/picker.png` renders the actual widget tree and exits without
recording or installing choices. Set `QT_QPA_PLATFORM=offscreen` for headless QA.

Evaluation verifies metadata and expressions, not successful native package
builds, binary-cache availability or application operation. The remaining gate
is a Linux graphical install: select an optional native app, confirm a
proprietary one, verify disabled ARM entries, install to disk, reboot from that
disk, inspect `/etc/nixos/nascent-software.*`, and run the selected launchers.
