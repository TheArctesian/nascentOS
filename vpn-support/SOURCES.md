# VPN evidence — reviewed 2026-10-22

## Exact package baseline

The foundation's `flake.lock` was copied unchanged. Revision:
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`; narHash:
`sha256-vhe2jyvRCgufWPqDuDq1S3t3ypE+ka46IFutV02xKso=`.
Evaluation used `/nix/var/nix/profiles/default/bin/nix` on the Mac, resolving the
already available pinned source. No heavy Linux client was built/downloaded.

Primary pinned nixpkgs definitions:

- [Mullvad GUI 2026.3](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/mu/mullvad-vpn/package.nix): separately hashed amd64/arm64 releases; native Nix wrapper around upstream deb.
- [Mullvad NixOS service](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/services/networking/mullvad-vpn.nix): defaults to CLI package; explicit GUI override required; optional early blocker and setuid exclusion wrapper.
- [Proton GTK 4.15.3](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/pr/proton-vpn/linux.nix): `proton-vpn`, `protonvpn-app`, Linux platform metadata, Python keyring/API/local-agent dependencies.
- [Proton API core 5.0.1](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/development/python-modules/proton-vpn-api-core/default.nix): NetworkManager backend, WireGuard/OpenVPN kill-switch imports. Its [optional split tunnel daemon](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/development/python-modules/proton-vpn-daemon/default.nix) exists separately; this module does not wire its privileged service/policies.
- [IVPN GUI 3.15.6](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/iv/ivpn-ui/package.nix): x86_64-linux metadata only. Newer upstream ARM support must not be inferred for this pin.
- [IVPN NixOS service](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/services/networking/ivpn.nix): separate daemon/CLI, reverse-path filtering `loose`, iproute2 configuration.
- [GNOME Keyring module](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/services/desktops/gnome/gnome-keyring.nix): D-Bus service activation and login PAM hook. This module adds the corresponding greetd PAM hook.
- [NetworkManager module](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/nixos/modules/services/networking/networkmanager.nix): `networking.networkmanager.plugins` is the current plugin option.

## Provider behavior

- [Mullvad client guide](https://mullvad.net/en/help/using-mullvad-vpn-app) and [security design](https://github.com/mullvad/mullvadvpn-app/blob/main/docs/security.md): disconnect kill switch and optional persistent disconnected blocking; DNS/IPv6/settings behavior belongs to client. [Split tunneling design](https://github.com/mullvad/mullvadvpn-app/blob/main/docs/split-tunneling.md) describes Linux process exclusions. [Plan limits](https://mullvad.net/en/pricing): paid account, five devices, no port forwarding.
- [Proton Linux support](https://protonvpn.com/support/linux-vpn-setup): current official distro/desktop scope and manual WireGuard/OpenVPN option; no NixOS/Hyprland endorsement. [Pinned GTK source](https://github.com/ProtonVPN/proton-vpn-gtk-app/blob/v4.15.3/README.md) identifies client and writable per-user settings.
- [Proton advanced kill switch](https://protonvpn.com/support/advanced-kill-switch), [IPv6](https://protonvpn.com/support/prevent-ipv6-vpn-leaks), and [split tunneling](https://protonvpn.com/support/protonvpn-split-tunneling): upstream features are version/distribution dependent; Linux split mode requires app restart after connection and generally cannot combine with kill switch. Current documentation can describe newer releases than pinned 4.15.3. [Plans](https://protonvpn.com/pricing) and [bandwidth](https://protonvpn.com/support/does-protonvpn-have-bandwidth-limit): free/paid availability, unlimited data, Plus ten devices; no promises about current server counts/prices are hardcoded here.
- [IVPN Linux](https://www.ivpn.net/apps-linux/), [firewall](https://www.ivpn.net/knowledgebase/general/do-you-offer-a-kill-switch-or-vpn-firewall/), [split tunnel FAQ](https://www.ivpn.net/knowledgebase/general/split-tunnel-faq/): app firewall and exclusions, best-effort Linux boot blocking, DNS behavior of excluded applications. These claims still require runtime checks on nascentOS.
- [NetworkManager nmcli manual](https://networkmanager.dev/docs/api/latest/nmcli.html): profile import and connection control. Manual profiles do not implement branded-client kill switches automatically.

## Other useful provider/client investigations

| Client | Current official evidence and pin | Decision |
| --- | --- | --- |
| NordVPN | [Official Linux GUI guide](https://support.nordvpn.com/hc/en-us/articles/35078364516625-How-to-use-NordVPN-Linux-GUI), [official source](https://github.com/NordSecurity/nordvpn-linux). Neither `nordvpn` nor `nordvpn-gui` exists in the pinned package set, and no Nord NixOS module was found. | Defer branded client pending a separately reviewed Nix package/service. A portable GUI alone does not supply the privileged daemon, routing or firewall. Manual provider-exported profiles may use the generic import option after individual review. |
| ExpressVPN | [Official current Linux GUI guide](https://www.expressvpn.com/support/vpn-setup/app-for-linux/) excludes unlisted distros from fixes. Pinned [expressvpn 3.52.0.2](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/ex/expressvpn/package.nix) is an older x86-only CLI/FHS package with a DNS file watcher, not the current GUI. | Defer; do not mislabel CLI as GUI or infer current upstream features for an older pin. |
| AirVPN / Eddie | [Official source](https://github.com/AirVPN/Eddie), pinned [eddie 2.24.6](https://github.com/NixOS/nixpkgs/blob/cd4ea8d57de16f4810bc5f14207bac45fbf19f67/pkgs/by-name/ed/eddie/package.nix) provides CLI/Mono GUI and polkit files; broad Linux metadata. The provider Linux page was JS-blocked during research. | Promising native follow-up, but elevated helper/polkit discovery, GUI/tray and ARM runtime need focused validation before a selectable entry. |

No AppImage fallback was added: required clients already have native Nix packages;
no reviewed, pinned provider AppImage plus system-service contract was established
for the deferred clients. An opaque portable app cannot replace VPN integration.

## Validation scope

`tests/eval.nix` forces installed package derivation paths but does not realize the
clients. See README for exact gates and runtime acceptance. Initial validation
passed nine supported combinations; invalid/multiple choices, ARM IVPN, conflicting
Mullvad with Proton and wrong-provider Mullvad flags were rejected. The separate
installer adapter's architecture and injection/conflict tests passed.

The foundation has active VM state containing a Unix socket. A whole-directory
`path:` metadata query rejected that socket. Research therefore used the explicit
locked nixpkgs revision and direct module imports, without copying or modifying
the baseline's VM files. This is unrelated to VPN package validity.
