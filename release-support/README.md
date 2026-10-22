# Build and publish installer previews

`.github/workflows/release.yml` builds the normal
`packages.<system>.installer` output on GitHub's hosted native runners and
publishes a **prerelease** on GitHub Releases. ARM64 uses `ubuntu-24.04-arm`
and is required. x86 uses `ubuntu-24.04` as a best-effort parallel build: if it
fails, only the successful ARM bundle is published. Only verified complete
architecture bundles appear in release notes. No self-hosted runner is needed.
The normal ISO uses the production compression setting; `installer-dev` is
reserved for local iteration and is not the release artifact.

## Trigger

Push a new immutable version tag from the reviewed source commit:

```sh
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

Use a new version for each build. Existing releases are never overwritten.
The tag workflow runs from the tagged commit, including when this workflow has
not yet been merged into the repository's default branch. A manual Run workflow
with an existing version tag is also defined, but GitHub only enables dispatch
once the workflow exists on the default branch. No merge or default-branch
change is needed for tag pushes.

Only trusted version tags trigger publication. PR/main checks in `check.yml`
have read-only repository permission. The release build job also has only
`contents: read`; only the separate publisher receives `contents: write`.
Actions are pinned to commit SHAs, and checkout does not persist credentials.
No personal access token or new repository secret is needed.

## Gates and resources

Each native build verifies the tag's commit, runs release unit tests and
workflow lint, `scripts/check`, and installer/profile derivation checks. It then
builds the production ISO without updating `flake.lock`.

Standard hosted runners document 14 GB storage, so the job first removes unused
Android, .NET, GHC and CodeQL toolchains **on that disposable runner only**.
Preflight logs actual free space and requires 30 GiB for the ISO-only build.
This is a measured-at-run gate, not a promise of unlimited hosted capacity.
The build uses two Nix jobs/four cores, a 180-minute timeout, and garbage-collects
unreferenced build dependencies before copying release parts. Failure stops
publication; there is no silently queued self-hosted job.

If `/dev/kvm` is present, the job grants the ephemeral Nix build users access and
executes the native NixOS boot derivation. If absent, the manifest explicitly
records `nixos_boot: not-run`. KVM availability is not inferred from a runner
label, and this service boot test is not a graphical ISO installation.

The build/publisher transport artifact is retained for one day. GitHub Actions
artifact quotas still apply. Published Release assets are the durable download.

## Assets and integrity

Each architecture has named ISO parts, a source lock, manifest and SHA256SUMS.
Images over 1 GiB are split into ordered 1 GiB parts to stay strictly under
GitHub's 2 GiB per-asset limit. The manifest records the source commit, lock hash,
Nix output/store path, whole-image bytes/SHA-256 and ordered part hashes/sizes.

The publisher verifies the whole reconstructed identity, exact inventory and
lock before upload. It creates a draft, uploads every asset, then checks GitHub's
server-computed asset SHA-256 digests and sizes against local files. Only after
that succeeds does it make the prerelease public. An upload failure leaves a
draft for diagnosis; it does not expose a partial public release.

The generated release notes contain reconstruction and verification commands.
Download all matching parts plus the lock, manifest and SHA256SUMS first:

```sh
sha256sum -c nascentos-TAG-aarch64-linux.SHA256SUMS
cat nascentos-TAG-aarch64-linux.iso.part* > nascentos-TAG-aarch64-linux.iso
```

Use `shasum -a 256 -c` for checksum-file verification on macOS. Compare the final
ISO hash with the whole-image hash in the manifest/release notes as well.
A tag plus `flake.lock` pins the source inputs; an independent byte-for-byte
rebuild has not been demonstrated.

## Validation boundaries

These are experimental previews, not stable hardware installers.
`release_ready` remains false. The consolidated local ARM development image
passed graphical installation, installed-disk boot, password login, selected
app/font/keyring checks and logout; its exact hash is in `docs/validation.md`.
That does not certify a newly built production ISO's bytes. New release hashes
still need the appropriate graphical and physical hardware gates.
No x86 installation or physical NVIDIA validation, actual games/VPN connections, provider
sign-ins, vault data, model inference or microphone/audio/suspend checks are
claimed by this pipeline.

Run `./release-support/verify` for packaging, integrity and workflow checks;
`./scripts/check` remains the repository's source/CLI gate.

References: [hosted runner resources](https://docs.github.com/en/actions/reference/runners/github-hosted-runners),
[release asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
[release asset digest metadata](https://docs.github.com/en/rest/releases/assets).
