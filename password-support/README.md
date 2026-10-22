# Password support

Proton Pass is the preferred personal vault. GNOME Keyring supplies the session's
`org.freedesktop.secrets` service for application credentials. These have different
jobs: the vault holds website passwords/passkeys; the keyring holds credentials
that individual desktop applications explicitly store through Secret Service.
PAM can unlock the login keyring using the local login password. It does not unlock
the Proton account or merge these stores.

No supported Proton Secret Service **provider** interface was verified. Its CLI
can be a **client** of Secret Service, storing its local database encryption key
there. No vault mirroring, plaintext exports, general vault access for agents,
or automatic injection into arbitrary applications is implemented.

## Import and interface

Import `password-support/module.nix` once in the assembled NixOS configuration:

```nix
{
  imports = [ ./password-support/module.nix ];
  nascent.passwords = {
    enable = true;
    manager = "proton-pass";
    firefox.enable = true;
    # Optional, separate CLI authentication and paid-plan requirements apply:
    # protonCli.enable = true;
    # protonCli.persistentKeyring = true;
  };
}
```

| Option under `nascent.passwords` | Default | Behavior |
| --- | --- | --- |
| `enable` | `false` | Installs/configures support only when selected |
| `manager` | `"proton-pass"` | `proton-pass`, `keepassxc`, `bitwarden`, `none` |
| `desktop.enable` | Package available | Native app; fails if explicitly requested on an unsupported platform |
| `desktop.autostart` | `false` | User service tied to `graphical-session.target` |
| `firefox.enable` | `false` | Installs the selected official extension using `normal_installed`; user can disable it |
| `keyring` | `"gnome"` | `gnome`, `external`, `none` |
| `pamServices` | `greetd`, `login`, `hyprlock`, `passwd` | GNOME Keyring PAM unlock and password-change handling |
| `protonCli.enable` | `false` | Installs pinned `pass-cli`, with no authentication action |
| `protonCli.persistentKeyring` | `false` | Sets only public backend-selection variables to `keyring` and `dbus` |

`manager = "none"` keeps the session keyring for other apps. Mail Bridge and VPN
modules should depend on this service, not install their own keyring provider.
They can assert `services.gnome.gnome-keyring.enable` when they require the managed
provider, or permit an explicitly configured external Secret Service. They must
not read Proton's vault or manufacture keyring entries from its contents.

The default CLI backend is unchanged (kernel keyring). Optional D-Bus storage is
verified in upstream **2.0.2** documentation: it persists the CLI session key across
reboots and fails if Secret Service is locked/unavailable; it does not fall back
to plaintext. It does not remove Proton's session lock or account authentication.

## Session assembly requirements

The active foundation is read-only and this folder does not change it. Before
enabling support in a real session, its owner must resolve these integration steps:

1. Use one session D-Bus shared by PAM, Hyprland, user services, and applications.
   The reviewed foundation wraps `start-hyprland` in `dbus-run-session`; check and
   remove that nested private bus when the normal systemd user bus already exists.
   Merely importing this module does not prove PAM's daemon and GUI share a bus.
2. Complete GNOME Keyring startup in that same bus. NixOS registers D-Bus activation
   and PAM starts/unlocks the daemon. If the compositor does not process XDG
   autostart, invoke `gnome-keyring-daemon --start --components=secrets` during
   session startup (discard its environment-assignment output; never use a second
   `--replace` daemon). Verify the service owner in the guest before signing in.
3. Export the compositor display environment to D-Bus/systemd. The foundation
   already invokes `dbus-update-activation-environment --systemd` for display vars.
   Optional vault autostart additionally requires a correctly started/stopped
   `graphical-session.target`; the current foundation does not visibly manage it.
4. Use a password-authenticated greetd login and an equally protected login
   keyring. Autologin, fingerprint-only login, and mismatched keyring/login
   passwords cannot be assumed to supply the password needed by PAM. The live
   installer autologin therefore does not demonstrate automatic keyring unlock.
5. When enabling KeePassXC browser native messaging, use
   `config.programs.firefox.finalPackage` consistently. Remove the foundation's
   separate plain `pkgs.firefox` system-package entry to avoid duplicate wrappers.
   The software picker must likewise avoid adding a second Firefox wrapper.

No custom unlock/password forwarding daemon is introduced. GNOME's supported PAM
module handles authentication; a first-run keyring prompt may still be required.
Hyprlock PAM unlock does not imply that screen lock locks the entire keyring or
Proton vault; configure/test each vault's lock timeout independently.

## Verified capabilities and gaps (2026-10-22)

| Component | Pinned availability / supported boundary |
| --- | --- |
| Proton desktop 1.36.1 | Native nixpkgs package repackages official DEB; x86_64 Linux only |
| Proton CLI 2.0.2 | Native nixpkgs package, x86_64/aarch64 Linux; separate login, optional Secret Service client |
| Proton Firefox extension | Official Mozilla add-on; website autofill and website passkeys; works without desktop app |
| Proton desktop SSH | Upstream changelog introduces agent in **1.39.0**; absent from this desktop pin; no socket/SSH config installed |
| Proton CLI SSH | Separate upstream CLI command exists; not enabled, no agent socket/environment is changed |
| Proton desktop autotype | Upstream documents paid feature and Linux remote-interaction permission; 1.33.5 changelog initially feature-gated it; Hyprland support unverified |
| Proton Linux biometrics | 1.36.0 changelog explicitly hides Linux biometrics; no PAM-to-vault unlock promised |
| KeePassXC 2.7.12 | Native x86_64/aarch64 Linux, browser native messaging included; local DB and pairing require user setup |
| Bitwarden 2026.8.0 | Native x86_64/aarch64 Linux; browser extension configured; system-authentication/native-messaging pairing untested |

The browser extension is the achievable low-friction path for routine website
logins/passkeys. Proton account sign-in and vault lock prompts remain under its
control. Current product documentation can describe features newer than the pin.
Desktop autotype requires compositor remote-input support and user consent; the
foundation's Hyprland/GTK portals have not been shown to supply it. No `uinput`
permissions, synthetic typing fallback, or silent permission grants are added.

KeePassXC is the supported alternative if a single application must also serve
Secret Service. Set `keyring = "external"`, disable other providers, then explicitly
enable KeePassXC Secret Service and expose a **dedicated application-credentials
group** with confirmation as appropriate. This module does not expose a database,
write its configuration, or register KeePassXC as an activation service. Until the
user configures it, `external` supplies no provider. Keep GNOME Keyring as the
default even when choosing KeePassXC for the personal vault unless this tradeoff
is intentional. Bitwarden offers a synced alternative; no verified Secret Service
provider interface is claimed for it.

App settings, vault lock choices and pairing stay writable in each user's normal
configuration; no Home Manager. Firefox policy can be disabled in the writable
system configuration; Firefox labels policy use as managed. No browser profile is
edited by this work. Other browsers can use their official store extensions
manually; no Chromium/Brave policy or native-messaging wiring is claimed.
Firefox's built-in save-login prompt defaults to off when extension support is
enabled; the user can change it. Existing browser-saved passwords are not migrated.

## Catalog handoff

`catalog.json` contains additive software-picker rows, pinned versions and platform
limits. Merge its `apps` into the picker's catalog, then import
`catalog-adapter.nix` **alongside** the picker module. The adapter knows the picker
option schema but never imports its source, avoiding ownership/import cycles.
It rejects multiple password-manager selections, maps one selection to the
manager, and maps no selection to `none` while retaining the session keyring.

Rows have `default = false` to avoid the current picker's architecture-independent
default list selecting an unavailable Proton desktop on ARM. `preferredManager`
records Proton as the product preference; a picker implementing platform-aware
defaults can preselect it on x86_64. ARM users can enable the module's Proton
browser-only configuration above. Firefox integration remains explicit; the
adapter does not install or mutate browsers just from selecting a desktop app.
Native Nix packages are available; no Flatpak or unverified AppImage fallback.

## Checks and runtime validation

With Nix installed, from repository root run `password-support/check`.
The standalone flake uses an unchanged copy of the foundation lock. It evaluates
both Linux architectures, positive and negative module configurations, disabled
behavior, PAM text, CLI backend choice, Firefox policy/native messaging, catalog
mapping, and conflicts with passSecretService/KWallet PAM. It also runs flake
evaluation and Nix formatting. No additional bootstrap is needed beyond Nix;
the initial repository has no root flake/check script to run.

Completed on 2026-10-22: the above gate passed for both Linux architectures,
formatting passed, and ShellCheck/Bash syntax checks passed for `check`. An
additional read-only x86_64 evaluation alongside the foundation's `modules`
directory (desktop and Firefox support enabled) returned no failed assertions,
with GNOME Keyring and greetd PAM enabled. This was configuration evaluation,
not a build or session test.

Before claiming session integration complete, run an isolated NixOS VM using a
throwaway user/keyring: password login; check one `org.freedesktop.secrets` owner;
store/retrieve/delete only a synthetic test item; log out/in and reboot; test
autologin's expected locked state and keyring password changes; verify independent
vault lock. Check Firefox `about:policies`, extension installation and KeePassXC
pairing with a disposable browser profile. Validate portal/autotype on Hyprland
and any future SSH-agent upgrade separately with synthetic credentials.

These are pending runtime checks, **not executed tests**. Package builds, VM boot,
real account login, vault operations, live keyring changes, and baseline edits
were not performed. Assertions detect known declarative conflicts; a manually
installed user-level provider can still compete, so inspect the guest's D-Bus
owner. D-Bus Secret Service is not a per-application sandbox or vault-wide ACL.

## Primary sources

- [Freedesktop Secret Service specification](https://specifications.freedesktop.org/secret-service/latest/)
- [GNOME Keyring PAM integration](https://wiki.gnome.org/Projects/GnomeKeyring/Pam)
- [Proton Linux setup](https://proton.me/support/set-up-proton-pass-linux)
- [Proton browser extension](https://proton.me/support/pass-browser-extension)
- [Proton website passkeys](https://proton.me/support/pass-use-passkeys)
- [Proton autotype and Linux permissions](https://proton.me/support/pass-autotype)
- [Proton desktop SSH setup](https://proton.me/support/ssh-agent)
- [Proton desktop changelog](https://github.com/ProtonMail/WebClients/blob/main/applications/pass-desktop/CHANGELOG.md)
- [CLI 2.0.2 backend configuration](https://github.com/protonpass/pass-cli/blob/2.0.2/docs/public/docs/get-started/configuration.md)
- [CLI 2.0.2 SSH command](https://github.com/protonpass/pass-cli/blob/2.0.2/docs/public/docs/commands/ssh-agent.md)
- [KeePassXC Secret Service and browser guide](https://keepassxc.org/docs/KeePassXC_UserGuide)
- [Bitwarden desktop setup](https://bitwarden.com/help/getting-started-desktop/)
- [Mozilla extension policy](https://firefox-admin-docs.mozilla.org/reference/policies/extensionsettings/)
- Official AMO IDs verified using Mozilla API: [Proton](https://addons.mozilla.org/api/v5/addons/addon/proton-pass/), [KeePassXC](https://addons.mozilla.org/api/v5/addons/addon/keepassxc-browser/), [Bitwarden](https://addons.mozilla.org/api/v5/addons/addon/bitwarden-password-manager/).
- Pinned nixpkgs package sources are linked in the catalog; module sources:
  [GNOME Keyring](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/services/desktops/gnome/gnome-keyring.nix),
  [PAM](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/security/pam.nix),
  [Firefox](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/programs/firefox.nix).
