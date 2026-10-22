# nascentOS VPN integration

This directory is self-contained for assembly into the foundation checkout. It
does not change the active baseline or software picker's separately owned files.
Native nixpkgs packages are used throughout. No Home Manager or AppImage is needed.
No provider is selected by default, no account is provisioned, and this module
never runs a login/connect command or writes credentials into Nix configuration.

## Assembly contract

Import `./vpn-support/module.nix` once from the final root module (or export it as
`nixosModules.vpn`). Preserve the foundation's `networkmanagerapplet`, polkit agent,
and Waybar `tray` module. No compositor-specific service is added here.

```nix
{ ... }: {
  imports = [ ./vpn-support/module.nix ];
  nascent.vpn.provider = "proton"; # null, "mullvad", "proton", "ivpn", "networkmanager"
}
```

The picker needs a **separate optional single-choice VPN field**; do not add these
as normal `nascent.software.selected` package IDs. Simply installing Mullvad or
IVPN's GUI without its system module leaves an unusable client. Use `catalog.json`
for labels/platform availability and `installer_adapter.render_selection(provider,
targetSystem)` for a validated, credential-free target module. `None` renders
`nascent.vpn.provider = null`. Reject multiple selections rather than silently
choosing the first. Write this generated module alongside, and import it with,
the picker's existing target software module. Do not configure a provider in the
live installer just because it was chosen for the target OS.

Changing provider requires a rebuild. Existing user client settings and
NetworkManager profiles survive a rebuild; review old autoconnect/kill switch
settings before switching. This module rejects conflicting Mullvad, IVPN and
ExpressVPN services. It cannot detect manually started clients or imported user
profiles; those must not be autoconnected alongside the selected provider.

## Desktop and session contract

`nascent-vpn` and the **VPN connection** desktop entry open the selected official
GUI, or NetworkManager's connection editor for manual import. Status/connect/
disconnect are provided by that GUI and its tray icon. Keep Waybar `tray` enabled;
an ordinary network/Wi-Fi icon is not a VPN status indicator. Nothing starts the
GUI automatically. `/etc/nascentos/vpn.json` supplies provider and launcher metadata
for future desktop/menu integration; it is not a live status endpoint.

Proton enables NetworkManager, its OpenVPN plugin, polkit, and GNOME Keyring Secret
Service with greetd PAM unlock by default. It installs `proton-vpn` (GTK GUI), not
the separate CLI, and does not provision the optional Proton split-tunnel daemon.
The password/session module should supply the same single GNOME Keyring provider;
set `nascent.vpn.configureKeyring = false` if that module owns service/PAM setup.
This is compatible with a separate Proton Pass vault, which is not assumed to
provide Secret Service. An authenticated login can unlock the keyring; autologin
has no password to unlock it, so test the manual unlock prompt. Never use a
plaintext keyring fallback to bypass that prompt.

Mullvad uses `services.mullvad-vpn` with `pkgs.mullvad-vpn` (GUI plus daemon), not
the default CLI-only package. Its exclusion wrapper and early-boot blocking are
explicit opt-ins under `nascent.vpn.mullvad`. IVPN uses `services.ivpn` plus
`ivpn-ui`; upstream's NixOS module changes reverse-path filtering to `loose` and
writes IP route tables. The pinned GUI is x86 only.

## Connection and privacy behavior

These are upstream feature descriptions, **not verified nascentOS guarantees**.
The installer only prepares the client. Connect and choose autoconnect/kill switch
in the client after login; installed client/daemon does not mean protected traffic.
Sources and version caveats are in [SOURCES.md](SOURCES.md).

| Choice | Kill switch, DNS and IPv6 | Autoconnect / split routing / limits |
| --- | --- | --- |
| Mullvad | Built-in disconnect protection; disconnected blocking requires the client's lockdown setting. DNS and IPv6 settings are owned by the client. Early boot blocking is off here unless explicitly enabled. | Choose autoconnect in the client. App exclusions need the opt-in privileged wrapper. Paid account, up to 5 devices, no port forwarding. |
| Proton | Client controls standard/advanced kill switch and DNS/IPv6 behavior. NixOS/Hyprland is outside the official supported distro/desktop list. No OS-wide kill switch is imposed here. | Configure startup/connection behavior in client and verify after reboot. Current upstream Linux split tunneling has distro restrictions, requires extra daemon integration absent here, and generally conflicts with kill switch. Do not promise it from this pin. Free plan has restricted server/feature choice; Plus offers 10 simultaneous devices. |
| IVPN | Client firewall has on-demand/always-on modes; Linux boot protection is best effort upstream. Client controls DNS and IPv6 handling. | Configure autoconnect and exclusions in app; validate DNS for excluded apps. Paid plan/device limits depend on plan. GUI offered only on x86 for this pin. |
| Manual NetworkManager | No automatic kill switch, DNS leak prevention or IPv6 policy. Imported configuration must explicitly route IPv4/IPv6 and DNS as intended. | Import WireGuard/OpenVPN privately after install; use client autoconnect only after checks. Provider-specific features and limits are not inherited from branded apps. |

## Gates and runtime acceptance

The repository base has no bootstrap script; this scoped flake reuses the exact
foundation lock. With the existing Nix installation:

```sh
python3 -m unittest discover -s vpn-support/tests -p 'test_*.py' -v
/nix/var/nix/profiles/default/bin/nix --extra-experimental-features 'nix-command flakes' run ./vpn-support#formatter.aarch64-darwin -- --check vpn-support/module.nix vpn-support/flake.nix vpn-support/tests/eval.nix
/nix/var/nix/profiles/default/bin/nix --extra-experimental-features 'nix-command flakes' eval --json ./vpn-support#validation
```

Use the matching formatter system on other hosts. Evaluation checks ARM/x86 valid
selections, package derivations, invalid IDs/multiple values, conflicting daemons,
unsupported ARM IVPN, defaults, and shared keyring ownership. It does not build
Linux clients, boot a guest, log in, or verify connectivity. After final assembly,
run the foundation's documented `scripts/check` and Linux VM gates as well.

Runtime release checks require a disposable VM and an account supplied privately
by the user: verify launch/tray/polkit and keyring unlock, login, connect,
disconnect and accurate client status; compare public IPv4/IPv6 and DNS before/
after connection; inspect routes/resolvers and packet capture outside the tunnel;
force tunnel loss, suspend/resume, network changes and reboot; test disconnected
and boot behavior for each chosen kill switch mode; verify autoconnect only when
enabled; test excluded apps and DNS separately; check switching providers leaves
no stale autoconnect profile or firewall rules. Record results per provider,
package version, architecture and network. The client status alone is insufficient
evidence of leak protection. No live connectivity has been tested in this task.
