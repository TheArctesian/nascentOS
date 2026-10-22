# GitHub builds and release candidates

These files integrate with the NixOS flake prototype. The release worktree initially
contains only README/LICENSE; integrate this directory and `.github/workflows/`
alongside the baseline **before enabling Actions**. Do not copy the baseline from
an active VM checkout just to make this worktree evaluate.

## What runs

- `check.yml`: PRs and main commits run `scripts/check` on native Ubuntu x86_64
  and ARM64 plus the release-support tests and actionlint. `scripts/check` checks
  formatting, evaluates all systems with `nix flake check --no-build --all-systems`,
  and builds the native CLI check. This does not build Linux images or boot them.
- `release.yml`: pushing an existing `vMAJOR.MINOR.PATCH` tag (optional prerelease
  suffix) or manually dispatching with that tag resolves it to a commit SHA.
  Both architectures then run source/CLI checks, build installer/profile assertion
  checks, `packages.<system>.vm`, and the production `packages.<system>.installer`.
  `scripts/test-vm` executes `checks.<system>.boot` through Nix's Linux test driver.
  Only successful jobs package and upload candidates, retained for seven days.
- A manual dispatch with `create_draft=true` waits for **both** build/boot jobs,
  downloads their artifacts, verifies all checksums and source/lock identities,
  then creates a **draft** GitHub Release with ISO assets, lock files, manifests,
  checksums and generated notes. It never edits an existing release. A tag push
  alone never creates a release. No workflow publishes a release.

The NixOS boot test checks service startup/configuration in a test guest. It is
not a boot of the release ISO, graphical session test, or Calamares installation.
All manifests retain `release_ready=false` and pending graphical, installation/
reboot and physical-hardware gates. Before manually publishing a draft, run the
baseline's `docs/testing.md` graphical/installer gates on **both candidate ISO
hashes**, record the results with that source SHA and image identity, and review
known hardware limitations. The current ARM live desktop observation does not
satisfy disk installation/reboot; x86 graphical/installation evidence is also
required. This workflow does not invent or silently pass an automated GUI test.

## Required runners and repository setup

Source CI uses `ubuntu-24.04` and `ubuntu-24.04-arm`. Release jobs deliberately use
matching dedicated Linux runners labeled:

- `[self-hosted, Linux, X64, nascent-release]`
- `[self-hosted, Linux, ARM64, nascent-release]`

Provision Nix with flakes/nix-command enabled, Python 3.11+, Git, Bash, coreutils,
and actionlint (or allow its installation from the locked nixpkgs).
`/dev/kvm` must be usable by the job user **and Nix build users**; configure Nix
`system-features` to include `kvm`. Preflight checks native architecture, KVM,
and at least 80 GiB free on workspace and store volumes. This is a conservative
minimum, not a measured peak: full desktop closures may require more, depending
on cache hits and parallel builds. Give each builder adequate RAM (start with
16 GiB), swap and a six-hour job budget. No remote CI/runtime measurement is
claimed. Jobs wait until suitable runners exist; do not replace a native runner
with an emulated architecture and call the boot gate equivalent.

Use disposable isolated runners restricted to this repository and trusted release
refs; never route arbitrary PR jobs to them. Restrict version-tag creation using
repository rulesets. Protect workflow changes through normal review. The only
write token is in the optional hosted `draft` job; checkout does not persist
credentials. No third-party accounts, cache secrets or PATs are required. Actions
are pinned by commit; update pins through reviewed dependency updates.

GitHub currently documents native Linux ARM64 and x64 hosted labels and 14 GB
standard-runner storage. That is insufficient headroom for this unmeasured full
OS build. Linux hardware acceleration is documented for Android tools, not a
blanket guarantee that every ARM/x64 image exposes KVM to Nix's sandbox. Probe
KVM and require successful test execution; don't infer it from a runner label.
macOS ARM hosted runners do not support nested virtualization. Dedicated Linux
builders avoid assuming that a Mac HVF desktop observation transfers to CI.
See [hosted runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners).

## Artifacts, reproducibility and caching

The manifest records the exact Git revision, locked input hash, Nix installer
output/store path, whole ISO SHA-256 and ordered part SHA-256/size. The original
lock is attached for each architecture. Use a clean checkout of that commit and
`nix build --no-update-lock-file .#packages.<system>.installer` to rebuild. A pinned
source/input graph supports reproduction; no byte-for-byte independent rebuild
has been demonstrated. Runtime/toolchain changes and upstream availability still
need consideration. Never update `flake.lock` inside a release run.

[GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
requires each asset to be under 2 GiB. Images over 1 GiB are split into ordered
1 GiB parts; notes provide the exact reconstruction and checksum commands. The
manifest contains the SHA-256 of the reconstructed ISO. Actions artifact ZIPs
are temporary transfer storage, not the long-term download location. Uploads use
no compression (ISOs are compressed already), unique architecture names and
seven-day retention. Storage/minute budgets and artifact upload/download limits
still apply; see [artifact behavior and limits](https://github.com/actions/upload-artifact)
and [Actions billing](https://docs.github.com/en/billing/managing-billing-for-your-products/managing-billing-for-github-actions/about-billing-for-github-actions).

Nix uses its standard signed `cache.nixos.org` substituter. No custom binary
cache is configured. A properly managed retained Nix store can save rebuild time
on trusted builders, but persistent machines require cleanup/isolation policy.
For disposable runners, optionally add a real signed Nix binary cache later:
self-hosted `nix-serve`, an HTTP/S3 binary cache, or a separately approved service
such as Cachix/Attic, with signing/trust and credentials configured deliberately.
Do not archive the entire `/nix/store` in Actions artifacts.
[GitHub Packages supports language/container registries](https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages),
not the NAR/narinfo substituter protocol; it is not a drop-in Nix binary cache.
See [Nix's binary cache documentation](https://github.com/NixOS/nix/blob/master/doc/manual/source/package-management/binary-cache-substituter.md).
This system release pipeline is separate from application update watchdogs.

## Local verification and integration

Run `./release-support/verify`. It exercises release-tag validation, split and
unsplit image metadata, reconstruction integrity, corruption rejection, empty
image and overwrite rejection, and lints both workflows with actionlint. Missing
actionlint/Nix is an environment failure, never a skipped passing gate.

After integrating the baseline, also run its documented `./scripts/check`.
Run `./scripts/test-vm` on each matching Linux/KVM builder, and execute a manual
candidate workflow without draft creation to establish capacity and timing.
No remote workflow, full image build, graphical gate, installer test, release,
repository settings or runner provisioning is performed by preparing these files.
