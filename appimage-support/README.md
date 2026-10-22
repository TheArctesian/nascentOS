# Nix-managed vendor AppImages

Import `appimage-support/module.nix` into the NixOS configuration. No Home Manager
is used. Prefer a nixpkgs package first; use this backend only for a reviewed
vendor Type 2 AppImage hosted in an official public GitHub release repository.
Nothing is selected by default, so importing/enabling the module alone downloads
no AppImages and creates no timer.

```nix
{
  imports = [ ./appimage-support/module.nix ];
  services.nascentAppImages = {
    enable = true;
    onCalendar = "daily"; # systemd calendar syntax; plus up to 1h jitter
    apps = { };          # explicit allowlist; fill only after vendor review
  };
}
```

Each `apps.<id>` entry has this interface. IDs must match `[a-z][a-z0-9-]*` and
must not collide with another installed executable. These are schematic values,
not a real package recommendation or a usable pin:

```nix
apps.vendor-editor = {
  displayName = "Vendor Editor";
  repository = "OFFICIAL-OWNER/OFFICIAL-REPOSITORY";
  assetName = "VendorEditor-{tag}-x86_64.AppImage";
  platform = "x86_64-linux"; # or aarch64-linux; must match this machine
  license = "unfree";       # verified key in nixpkgs lib.licenses
  pin = {
    version = "v1.2.3";
    url = "https://github.com/OFFICIAL-OWNER/OFFICIAL-REPOSITORY/releases/download/v1.2.3/VendorEditor-v1.2.3-x86_64.AppImage";
    hash = "sha256-REPLACE-WITH-THE-REVIEWED-SOURCE-HASH=";
  };
  autoActivate = true;      # default; false builds/stages only
  maxBytes = 1073741824;    # default metadata size ceiling: 1 GiB
};
```

The initial pin must be reviewed against the vendor's official distribution
page/repository, architecture and license before enabling the entry. Compute its
SRI SHA-256 using `nix store prefetch-file --json URL` and compare with upstream's
published digest (or stronger signature where provided). The selected asset name
must be exact; `{tag}` is the only substitution, using the complete upstream tag.
Unfree seeds also require the normal NixOS `nixpkgs.config.allowUnfreePredicate`
or `allowUnfree` permission. Do not use a fake hash as a shipping pin.

The software picker can represent this as `backend = "appimage"` with an ID and
the fields above. Keep fallback selection disabled until all pin and provenance
fields exist. This module supplies a launcher named `<id>` and desktop entry
`nascent-appimage-<id>.desktop`; no picker or app catalog is included here.

## Update and activation behavior

The systemd service runs as a dedicated `nascent-appimages` account. The timer
requires that account to be permitted by the Nix daemon's `allowed-users`
(the standard NixOS default permits local users; no trusted-user grant is needed).
It
queries GitHub's latest stable release for each allowlisted repository. It
requires exactly one matching asset, a versioned URL in that repository, a
supported tag and GitHub's SHA-256 asset digest. It refuses missing digests,
prereleases, oversized metadata/assets and replacements under the current tag.
The asset size ceiling checks metadata; Nix performs the actual download and
source-hash verification. GitHub API redirects/download CDN behavior is delegated
to HTTPS and the Nix fetcher, with the pinned digest checked on downloaded bytes.

The digest protects integrity relative to the GitHub release metadata; it is not
an independent vendor signature or protection from a compromised upstream account.
Discovery trusts GitHub's latest-release designation, not semantic version
ordering. Sources requiring custom APIs, authentication, update manifests,
non-GitHub hosting or signature policies need a separately reviewed adapter;
this implementation fails closed rather than guessing.

For each candidate, the updater writes a complete `pin.json`, then invokes
`nix-build` on the bundled packaging expression and **the system's captured
nixpkgs source path**. It uses `appimageTools.wrapType2` and `fetchurl` with the
explicit hash. It never updates a flake lock, rebuilds NixOS or invokes the GUI
binary as a service check. The automatic builder imports plain nixpkgs with the
selected package's unfree permission; it does not reproduce host overlays or
custom nixpkgs configuration. Apps needing custom libraries/overlays are outside
this generic backend until explicit support is added.

A successful build must contain the expected executable. The updater atomically
switches that app's `current` symlink. New launches resolve the new store package;
existing processes are not signaled or restarted. This is packaging validation,
not proof that the GUI works. A running application can still resolve its own
resources or upgrade writable user data, so app-specific compatibility testing
and backups remain relevant. Package rollback does not roll back user data.
Disable vendor in-app self-updaters where the app provides a setting.

The system build supplies the reviewed initial package as a fallback. The first
watchdog run registers it as a GC-rooted seed generation, so the first automatic
upgrade also has a rollback target. Every subsequent generation keeps its own
stable `nix-build --out-link` GC root; these links must not be moved. The current
generation survives a service timeout or discovery/build failure. The journal
and per-app status record report failures and the service exits nonzero if any
app fails; other selected apps can still update.

## Operations and reproducibility

Run these on the delivered NixOS machine, after applying its configuration:

```sh
nascent-appimages status
sudo systemctl start nascent-appimages.service
journalctl -u nascent-appimages.service
sudo -u nascent-appimages nascent-appimages rollback vendor-editor
sudo -u nascent-appimages nascent-appimages resume vendor-editor
```

Mutating CLI commands should run as the service account, not root, to preserve
state ownership. A file lock serializes manual commands and timer runs. Rollback
selects the preceding activated generation and creates an update hold; the timer
will leave that app alone until `resume`. Rollback is manual after a behavioral
problem: automatic runtime health detection is not claimed. `autoActivate = false`
leaves successful builds staged; set it back to true and run the service to
build/activate the current upstream candidate after review.

State lives in `/var/lib/nascent-appimages/<id>/`: `current`, `generations/*/pin.json`,
`build-context.json`, GC-rooted `package`, `nixpkgs` and `recipe` links in each
generation, activation `history.json`, `status.json`, and
optional `hold`. These are readable system manifests, contain no credentials,
and can be copied to version control for audit/reproduction. Each pin records
version, source URL, source hash, repository, platform and license. Runtime
updates intentionally do not edit the shared Git checkout. To rebuild a saved
pin against the same captured nixpkgs source:

```sh
nix-build ./appimage-support/build.nix \
  --argstr nixpkgsPath /nix/store/RECORDED-SYSTEM-NIXPKGS-source \
  --argstr pinPath /absolute/path/to/pin.json --out-link ./reproduced-app
```

The generation's `build-context.json` records the exact nixpkgs and recipe store
paths; their GC roots preserve those inputs after old system generations expire.
For an archived generation, use its `recipe/build.nix`, `nixpkgs` and `pin.json`
paths directly with the same command. Keep the system's nixpkgs lock alongside
exported manifests. Existing active
generations remain active when the system configuration's seed pin changes;
the seed is a fallback, not an imperative reset of app state. Reverting a system
generation does not revert this separately managed app state. App rollback uses
the command above. Removing an app from the allowlist removes its launcher and
future updates. Retained generations are deliberately not pruned automatically;
plan disk usage and remove obsolete GC roots only after identifying which
generations must remain available for rollback. With no pruning, long-running
desktops can accumulate substantial storage.

No watchdog is installed or enabled on the development Mac by this directory.

## Verification

There is no repository bootstrap requirement in the minimal baseline. Required
changed-path checks for this directory are:

```sh
python3 -m unittest discover -s appimage-support/tests -v
nix-instantiate --eval --strict appimage-support/tests/module-eval.nix \
  --arg nixpkgs /absolute/path/to/the-pinned-nixpkgs-source
git diff --check
```

The Python suite uses temporary directories and a fake Nix runner; it does not
download or execute an AppImage. The Nix check evaluates disabled/empty/selected
module cases, platform assertions and a Linux package derivation. On this Mac,
16 tests and evaluation against nixpkgs `cd4ea8d57de16f4810bc5f14207bac45fbf19f67`
pass. Actual Linux AppImage builds, Nix daemon GC-root registration under the
hardened systemd unit, GUI launches, and reboot/process survival need Linux
integration validation with a real selected vendor package before rollout.

Primary references:

- [Nixpkgs AppImage helpers](https://nixos.org/manual/nixpkgs/stable/#sec-pkgs-appimageTools)
- [GitHub release asset API and digest field](https://docs.github.com/en/rest/releases/assets)
- [GitHub latest release API](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)
- [nix-build output links and GC-root lifetime](https://nix.dev/manual/nix/stable/command-ref/nix-build.html)
