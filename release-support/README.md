# Build and publish installer ISOs

`.github/workflows/release.yml` builds the normal `packages.<system>.installer`
output on GitHub's hosted native runners for **every push to `main`** and uploads
the whole ISOs to the Cloudflare R2 bucket `nascentos-iso`, served at
<https://iso.stephenokita.com>. No tags are needed. ARM64 (`ubuntu-24.04-arm`) and
x86_64 (`ubuntu-24.04`) build in parallel; either may fail, and only verified
architectures are published. `installer-dev` is reserved for local iteration.

## Downloads

| URL | Contents |
| --- | --- |
| `/latest/nascentos-x86_64-linux.iso` | Newest x86_64 ISO (stable link) |
| `/latest/nascentos-aarch64-linux.iso` | Newest ARM64 ISO (stable link) |
| `/latest/nascentos-<system>.iso.sha256` | Checksum for that `latest/` ISO |
| `/latest.json` | Per architecture: version, source commit, URLs, size and SHA-256 |
| `/vX.Y.Z/` | One immutable build: ISO, flake.lock, manifest, SHA256SUMS, NOTES.md |

```sh
curl -LO https://iso.stephenokita.com/latest/nascentos-x86_64-linux.iso
curl -LO https://iso.stephenokita.com/latest/nascentos-x86_64-linux.iso.sha256
sha256sum -c nascentos-x86_64-linux.iso.sha256
```

Use `shasum -a 256 -c` on macOS. Only the newest version is retained
(`R2_KEEP` in `publish-r2`, default 1), plus any version `latest/` still
serves; older version directories are deleted, so a versioned link stops
working once a newer version is published. If one architecture fails to build, its
`latest/` image stays at the previous version rather than disappearing, so
`latest.json` can list different versions per architecture.

## Versioning

The version comes from the first-parent commit count of `main`
(`release-support/version.py`), so each merged PR or direct push moves it
forward without stored state. PATCH and MINOR each hold two decimal digits:

| Count | Version |
| --- | --- |
| 6 | `v0.0.6` |
| 99 | `v0.0.99` |
| 100 | `v0.1.0` |
| 10000 | `v1.0.0` |
| 3222222 | `v322.22.22` |

The checkout uses full history; a shallow clone would count 1. Rewriting `main`'s
history would reuse numbers, so don't force-push it.

## Credentials and permissions

The publisher job reads the repository secrets `R2_ENDPOINT`
(`https://<account>.r2.cloudflarestorage.com`), `R2_ACCESS_KEY_ID` and
`R2_SECRET_ACCESS_KEY`: an R2 API token with Object Read & Write on the bucket.
Build jobs have only `contents: read` and never see these secrets. Actions are
pinned to commit SHAs, and checkout does not persist credentials.

## Gates and resources

Each native build runs release unit tests and workflow lint, `scripts/check`,
and installer/profile derivation checks, then builds the production ISO without
updating `flake.lock`. Hosted runners document 14 GB storage, so the job removes
unused toolchains **on that disposable runner only**, requires 30 GiB free, and
adds a 24 GiB swap file for all-system evaluation. If `/dev/kvm` is present the
native NixOS boot derivation runs; otherwise the manifest records
`nixos_boot: not-run`. This service boot test is not a graphical installation.

Builds are serialised in one concurrency group. A newer push replaces a queued
build, and pushes touching only Markdown, `docs/` or installer preview images
are skipped, so not every version number gets an ISO. Only `main` publishes: a
manual run on another branch builds but skips the publish job.

## Assets and integrity

`package.py` writes the ISO, source lock, manifest (commit, lock hash, Nix store
path, whole-image bytes/SHA-256) and SHA256SUMS. `verify-candidate.py` re-checks
the bundle before upload. `publish-r2` then:

1. refuses to continue if the version already exists with a different ISO
   hash (re-runs may only complete a partial upload of identical bytes);
2. uploads the bundle, including NOTES.md, and runs `rclone check`;
3. downloads each ISO back through the public URL and checks its SHA-256, since
   rclone's multipart check relies on client-written MD5 metadata;
4. when the version is newer than `latest.json`, server-side copies each ISO to
   `latest/` immediately followed by its `.sha256`, then rewrites `latest.json`.
   An R2 read error aborts rather than being treated as "no latest yet";
5. prunes old versions.

Versioned objects are served `immutable`; `latest/` objects and `latest.json` use
`no-cache` so Cloudflare's edge revalidates them after each publish.

The x86_64 build is reproducible: a local build of commit `84122b6` and the
hosted build of the same commit gave the same ISO SHA-256 (`14167e53…`).

## Validation boundaries

These are experimental previews, not stable hardware installers;
`release_ready` remains false. See `docs/validation.md` for what the ARM
development image has passed. No x86 installation, physical NVIDIA validation,
games/VPN connections, provider sign-ins, model inference or audio/suspend
checks are claimed by this pipeline.

Run `./release-support/verify` for packaging, integrity and workflow checks;
`./scripts/check` remains the repository's source/CLI gate.
