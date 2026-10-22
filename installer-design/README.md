# Calamares spacing adapter

Presentation-only changes for the parent checkout's pinned Calamares **3.4.2**
(nixpkgs `cd4ea8d57de16f4810bc5f14207bac45fbf19f67`). No installer jobs,
partition options, navigation signals, confirmation policy, live theme, launcher,
or approved raster assets change.

The wizard stays a conventional Qt Widgets sidebar, page, and bottom navigation.
The existing Hyprland launcher still controls maximization. No QML dependency or
replacement installer is introduced.

## Layout

- Content inset: 40 logical pixels at window widths >=1100, 28 at >=900,
  otherwise 20. Top inset is 32, reducing to 20 below 660 high.
- Centered content column and aligned footer cap at 1080 logical pixels.
- Sidebar: 224 wide, or 196 below 1000 wide; 16 horizontal inset. Smaller,
  left-aligned step text and an inset rounded current-step highlight. The
  existing scrollable step list remains usable at short heights.
- Approved logo: unchanged file, 56-pixel sidebar viewport. The main artwork
  preserves its complete aspect ratio inside a maximum 640×360 viewport,
  shrinking with available space. Its intrinsic raster size no longer forces
  the install page to expand. No cropping or image edits.
- Install page: clear heading; artwork and status separated by 24 pixels;
  progress, percentage, and log control share one row. Status wraps.
- Footer: 12-pixel button spacing, 20 top / 24 bottom inset (12 / 16 when
  compact). Buttons have 8×16 padding and visible keyboard focus.
- Form controls receive consistent internal padding. The outer inset replaces
  module-dependent page margins. Internal specialized module layouts remain
  upstream. Application-scoped QSS also reaches unparented installer dialogs;
  their sizing and behavior remain upstream.

`NascentLayout.h` owns responsive window insets and the bounded artwork widget.
`apply.py` connects these to the pinned upstream widget hierarchy. All anchors
are validated before source writes, so source drift fails visibly. The adapter
changes only six presentation `.cpp` files and adds one header.

## Integration after the independent installation gate is stable

Copy this directory into the integration checkout, excluding `__pycache__`.
Review and apply [integration.patch](integration.patch) there. It has only three
changes to `modules/installer/default.nix`:

1. Import `../../installer-design/integration.nix` with `pkgs`.
2. Append `installerDesign.extensionPostPatch` after the existing branding copy.
3. Merge `installerDesign.installerAttrs old` into the existing installer
   override, preserving its wrapper arguments and desktop launcher changes.

The adapter passes its header as a separate Nix store path: it does not assume
that sibling files accompany an interpolated script path.

Run the parent repository's documented bootstrap/gates after integration:

```sh
./scripts/check
nix build .#installer
```

The Linux build and live wizard checks are still required. In a **separate**
disposable VM, inspect Welcome, Users, Desktop, Partitions, Summary, Install,
Finish, and confirmation/error dialogs at 1280×800, 1024×768, and 800×600. Check
keyboard focus, longer translated labels, and changing the display size while
open. Review partition dialogs for overflow before shipping. The existing
installer session must finish independently; do not replace/restart its VM.

## Validation completed in this isolated checkout

- `python3 installer-design/verify.py /path/to/pinned/calamares/source`: passes
  on the cached Nix source. Checks the exact changed paths, source anchors,
  repeat-application rejection, and no writes on anchor mismatch.
- Python syntax compilation passes for the adapter, verifier, and preview.
- `nix-instantiate --parse installer-design/integration.nix`: passes.
- `nixfmt --check installer-design/integration.nix`: passes.
- The proposed integrated parent module parses. Parent checkout was read only.
- Production QSS loads into real Qt Widgets without stylesheet parser warnings.
- Qt preview geometry checks pass at 1280×800, 1024×768, 800×600, and 800×520;
  footer controls remain in bounds with >=36-pixel height.

This isolated checkout has no flake or root test runner. The parent full gate
was not run against an unintegrated proposal. C++ compilation and full Linux
Calamares runtime behavior have **not** been validated here.

## Preview provenance and regeneration

The PNGs under `previews/` are **representative Qt Widgets renders**, using the
production stylesheet and a focused mirror of the actual Calamares install-page
widget hierarchy, plus the unchanged parent artwork. They are **not screenshots
of the running installer**. Qt 6.12/Fusion on macOS approximates the parent's
Qt 6.11/Kvantum metrics; verify those metrics in Linux before shipping.
The Users image is an illustrative form sample, not a port of Calamares Users.
No screenshot generation touched a VM.

```sh
python3 -m venv /tmp/nascent-installer-layout-venv
/tmp/nascent-installer-layout-venv/bin/pip install PySide6-Essentials
QT_QPA_PLATFORM=offscreen /tmp/nascent-installer-layout-venv/bin/python \
  installer-design/preview.py \
  --asset /path/to/nascentOS/assets/branding/main-logo.png
```

Offscreen Qt may print `This plugin does not support propagateSizeHints()`;
geometry assertions still run and pass. PySide is a preview-only dependency,
not part of the installer package.
