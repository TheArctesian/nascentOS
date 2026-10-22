# Software catalog evidence

Reviewed 22 October 2026. Native packages are selected from nixpkgs revision
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`, matching the prototype system flake.
The catalog records the pinned package version and source file for every native
entry. These versions deliberately need not equal the latest upstream release.

## Verification and limits

The package licenses, `meta.platforms` and `meta.broken` were evaluated from the
pinned package set, with `allowUnfree = true` solely for metadata inspection.
Every included native package had `meta.broken = false`. Each native package’s
`drvPath` was forced for both `x86_64-linux` and `aarch64-linux` where offered;
these evaluations succeeded. This checks expression/platform compatibility,
not a successful package build, binary cache presence or runtime operation.
No optional application or engine was built or downloaded for this research.

Slack, Discord and ONLYOFFICE are offered only on x86_64 Linux: their pinned
`meta.platforms` excludes aarch64 Linux. Unity Hub is also x86_64 Linux only.
Session declares `lib.platforms.all`; the catalog deliberately exposes only the
two Linux architectures evaluated here. Other broadly declared packages are
similarly narrowed to nascentOS’s two target architectures. Native ARM builds
may be maintained by nixpkgs even where vendor binary downloads are narrower.

`license` describes package metadata, not service availability or price. For
Signal, upstream nixpkgs metadata lists AGPL-3.0-only plus an unspecified free
license; Neovim lists Apache-2.0 and Vim. Cursor, Obsidian, Slack and Discord are
optional proprietary packages. Account-based online services can have paid
features even where the client is open source. Selection must never stand in
for agreeing to upstream terms or activating a license.

## Upstream primary sources

| Entries | Official evidence and catalog decision |
| --- | --- |
| Neovim | [Neovim](https://neovim.io/) describes a terminal editor with user configuration in `init.lua`. Neovim is the default; the baseline supplies LazyVim separately. |
| Zed | [Linux installation](https://zed.dev/docs/linux) and [installation](https://zed.dev/docs/installation) document x86_64 and aarch64 Linux. |
| VSCodium | [Project website](https://vscodium.com/) identifies MIT-licensed binaries, disabled telemetry, Linux support and the NixOS `vscodium` package. |
| OpenCode | [Official documentation](https://opencode.ai/docs/) documents its open source terminal coding agent and provider credentials. This catalog installs the pinned `opencode` CLI, not a desktop edition or a newer major version. |
| Codex | [Official Codex CLI documentation](https://learn.chatgpt.com/docs/codex/cli) distinguishes the terminal agent. The pinned Apache-2.0 CLI is a native option; authentication is completed after installation. |
| Cursor | [Official downloads](https://cursor.com/download) provides Linux downloads; pinned `code-cursor` has both Linux architectures and an unfree license. |
| ChatGPT | [Official Linux app documentation](https://learn.chatgpt.com/docs/linux/linux-app) now describes Linux desktop support. A native ChatGPT package and NixOS compatibility were not verified in the pinned set. An informational card explains this; no browser shortcut or package is installed. It does **not** claim that no official Linux app exists. |
| Firefox | [Mozilla’s Firefox site](https://www.firefox.com/) is the upstream project. The architecture/license decision is established by pinned package metadata; browser is the open source default. |
| Chromium | [Chromium project](https://www.chromium.org/Home/) identifies the open source browser. Google Chrome is deliberately absent. |
| Joplin | [Installation](https://joplinapp.org/help/install/) lists a Linux desktop application. |
| Notion | [Desktop downloads](https://www.notion.com/desktop) and [web service](https://www.notion.so/) establish the official service. An informational card explains that the picker offers no verified official native package; no unofficial Electron wrapper or browser shortcut is installed. |
| Obsidian | [Downloads](https://obsidian.md/download) lists Linux and ARM64 AppImages; [end user agreement](https://obsidian.md/eula) is the pinned package license. |
| Zotero | [Downloads](https://www.zotero.org/download/) lists Linux 64-bit and ARM64. |
| Blender | [Blender](https://www.blender.org/) is the upstream project; pinned package metadata declares GPL-2.0-or-later and both Linux architectures. Heavy optional application, unchecked by default. |
| Godot | [Linux downloads](https://godotengine.org/download/linux/) lists Linux x86_64 and arm64 and distinguishes .NET versions. This catalog uses standard `godot_4`, without .NET. |
| Unity | [Unity Hub documentation](https://docs.unity.com/en-us/hub) describes Hub managing editors and licenses. Pinned `unityhub` exists, but Unity is deliberately a manual setup card: account/license activation and editor choice/download belong after installation. |
| Unreal Engine | [Epic’s Linux development quickstart](https://dev.epicgames.com/documentation/en-us/unreal-engine/linux-development-quickstart-for-unreal-engine) documents installed/source builds, account download and Intel/AMD recommendations. Manual setup only; no engine or license acceptance is automated. ARM editor support is unverified and is not offered. |
| Signal | [Official download page](https://signal.org/download/) documents Linux desktop support and linking to a phone. Pinned nixpkgs builds both architectures. |
| WhatsApp | [Official downloads](https://www.whatsapp.com/download) directs unsupported devices to its [web application](https://web.whatsapp.com/). Informational card only: no verified official native package or browser shortcut is installed. |
| Session | [Official downloads](https://getsession.org/download) lists the Linux desktop application. |
| Slack | [Official Linux download page](https://slack.com/downloads/linux) establishes the vendor Linux client; pinned platform metadata restricts this catalog to x86_64 Linux. |
| Teams | [Microsoft downloads](https://www.microsoft.com/en-us/microsoft-teams/download-app) recommends the Teams progressive web app for Linux. Informational card only: no verified official native package or browser shortcut is installed. |
| Discord | [Official downloads](https://discord.com/download) provides Linux; pinned platform metadata restricts this catalog to x86_64 Linux. |

## Added office, graphics and video applications

| Entry | Evidence and pinned decision |
| --- | --- |
| ONLYOFFICE | [Vendor product page](https://www.onlyoffice.com/desktop) describes its open source office editors. [Vendor ARM announcement](https://www.onlyoffice.com/blog/2026/01/onlyoffice-desktop-editors-available-for-linux-arm) documents newer ARM support, but pinned `onlyoffice-desktopeditors` 9.1.0 declares **only x86_64 Linux**; ARM is disabled here. AGPL-3.0-or-later. |
| LibreOffice | [The Document Foundation](https://www.libreoffice.org/) describes its open source office suite. Pinned `libreoffice` supports both target architectures. |
| Inkscape | [Upstream](https://inkscape.org/) is the SVG editor’s official site (HTTP 403 from the research browser, so package metadata supplies verification). Pinned `inkscape` supports both targets, GPL-3.0-or-later. |
| GIMP | [Official GIMP site](https://www.gimp.org/) describes the GNU/Linux image editor. Pinned `gimp` supports both targets, GPL-3.0-or-later. |
| Kdenlive | [Official KDE project](https://kdenlive.org/) describes the Linux nonlinear video editor. Pinned `kdePackages.kdenlive` supports both targets; full aggregated metadata licenses are recorded in the catalog. |
| Shotcut | [Official site](https://shotcut.org/) describes a free Linux video editor. Pinned `shotcut` supports both targets, GPL-3.0-or-later. |
| DaVinci Resolve | [Blackmagic product page](https://www.blackmagicdesign.com/products/davinciresolve) distinguishes Resolve and Studio. Pinned `davinci-resolve` and `davinci-resolve-studio` 20.3.2 exist for x86_64 Linux only and are unfree. Source [package.nix](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/da/davinci-resolve/package.nix) implements a POST to the vendor registration endpoint with synthetic registration fields, then a large download. **Manual informational card only**, with no package installed or registration submitted. GPU drivers/OpenCL or CUDA and codec/edition limitations need review; Studio requires its purchased license. |
| Olive | Excluded. `olive` is absent. `olive-editor` is a throwing alias in pinned [aliases.nix](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/top-level/aliases.nix), explicitly removed as unmaintained and broken (2026-05-22). |
| ArtCraft suite | Excluded, including as a default. `artcraft` is absent; case-insensitive searches for ArtCraft, PhotoCraft, WordCraft, GridCraft and DeckCraft found no pinned package definitions. [Upstream source](https://github.com/storytold/artcraft) establishes project identity, but an external download does not meet the user’s nixpkgs-only constraint. No third-party similarly named download sites are trusted for installation. |

The final catalog offers only `kind = package` entries for installation. Manual
cards are disabled information, including ChatGPT, Notion, WhatsApp and Teams.
There are no `web` entries and no generated browser shortcuts. The user subsequently broadened acceptable sources. This implementation still
enables only verified pinned nixpkgs installations: `backend = nixpkgs` for
package entries and `backend = manual` for informational entries. The user’s source order is native nixpkgs first, then a verified Nix-wrapped
AppImage when no native package exists. External release mapping and updater
infrastructure are coordinator-owned and not enabled by this catalog. Flatpak
was not selected and is not an enabled provider.

## Icon provenance

The picker uses the installed `pkgs.papirus-icon-theme` from the same pinned
nixpkgs, rather than copying logos from search results or generating vendor
logos. [Papirus upstream](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme)
licenses its artwork under GPL-3.0 and explains that application marks remain
the property of their trademark holders; inclusion does not imply endorsement.
See its [license](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme/blob/master/LICENSE)
and [authors](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme/blob/master/AUTHORS).
The pinned Papirus version is 20250501. Its upstream 64x64/apps Git tree was inspected: all initial catalog icon hints exist except `opencode`, `openai`, `cursor`, `chatgpt`, and `unreal-engine`. Theme icon names are hints: if an application mark is absent from the pinned
theme, the UI must show its explicit generic fallback, never invent a logo.
No external icon request is made at runtime.

## Updating

When advancing the system nixpkgs pin, reevaluate `meta.platforms`,
`meta.broken`, licenses and native `drvPath` for both architectures. Verify
upstream URLs and manual/web decisions again. Do not widen architectures
merely because a web search mentions ARM support, and do not infer a
successful build from successful evaluation.

## Fonts and accessibility

Font entries have `role = font` and belong in `fonts.packages`, not just
`environment.systemPackages`. All three pinned font derivations evaluate on
x86_64 Linux and aarch64 Linux, have `meta.broken = false`, and use OFL-1.1.

- [Fira Code upstream](https://github.com/tonsky/FiraCode): pinned `fira-code`
  6.2, selected by default for coding and terminal monospace. The package
  installs its variable TTF by default (`useVariableFont = true`).
- [Font Awesome upstream](https://github.com/FortAwesome/Font-Awesome): pinned
  `font-awesome` 7.2.0, selected by default as an icon font only. This package
  installs OTF font files, not web CSS or SVG assets. It must never become a
  general text family or replace UI/coding fonts.
- [OpenDyslexic upstream](https://opendyslexic.org/) and the [archived source
  used by the pin](https://github.com/antijingoist/opendyslexic/tree/v0.91.12):
  pinned `open-dyslexic` 0.91.12, optional and initially unchecked. Offer it as
  a writable UI font preference only; retain the coding monospace family.
  Describe it as a personal reading preference without promising a treatment
  or guaranteed accessibility outcome.

The generic `preferences-desktop-font` theme icon identifies these font
controls. It is not a fabricated font brand mark.

Font family names were verified by reading SFNT `name` tables (family ID 1
and typographic family ID 16) directly from the pinned upstream artifacts:
Fira Code’s 6.2 release ZIP variable TTF; Font Awesome 7.2.0 `otfs/` files;
and OpenDyslexic v0.91.12 `compiled/` OTF files. No font package was built.
The resolved coding family is **Fira Code** (the variable font also has a
legacy family name `Fira Code Light`; it is not `Fira Code VF`). Icon families
are **Font Awesome 7 Free**, **Font Awesome 7 Free Solid**, and **Font Awesome
7 Brands**. The optional UI family is **OpenDyslexic**. These names are
recorded in each font entry’s `fontFamilies` list.
