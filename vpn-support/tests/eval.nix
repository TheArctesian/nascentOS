{ nixpkgs }:
let
  lib = nixpkgs.lib;
  catalog = builtins.fromJSON (builtins.readFile ../catalog.json);
  mk =
    system: settings:
    lib.nixosSystem {
      inherit system;
      modules = [
        ../module.nix
        {
          system.stateVersion = "26.05";
          boot.loader.grub.enable = false;
          fileSystems."/" = {
            device = "/dev/test";
            fsType = "ext4";
          };
        }
        settings
      ];
    };
  failed = cfg: map (a: a.message) (lib.filter (a: !a.assertion) cfg.assertions);
  summary =
    system: provider:
    let
      cfg = (mk system { nascent.vpn.provider = provider; }).config;
      pkg =
        if provider == null then
          null
        else
          (import nixpkgs { inherit system; })
          .${(lib.findFirst (p: p.id == provider) null catalog.providers).package};
    in
    {
      inherit provider system;
      failures = failed cfg;
      daemon =
        if cfg.services.mullvad-vpn.enable then
          "mullvad"
        else if cfg.services.ivpn.enable then
          "ivpn"
        else
          null;
      keyring = cfg.services.gnome.gnome-keyring.enable;
      earlyBlocking = cfg.services.mullvad-vpn.enableEarlyBootBlocking;
      excludeWrapper = cfg.services.mullvad-vpn.enableExcludeWrapper && cfg.services.mullvad-vpn.enable;
      package = if pkg == null then null else pkg.drvPath;
      catalogVersionMatches =
        provider == null
        || !(lib.findFirst (p: p.id == provider) null catalog.providers ? version)
        || pkg.version == (lib.findFirst (p: p.id == provider) null catalog.providers).version;
      installedDerivations = map (p: p.drvPath) cfg.environment.systemPackages;
      launcher =
        if provider == null then false else builtins.hasAttr "nascentos/vpn.json" cfg.environment.etc;
    };
  valid =
    lib.concatMap
      (
        system:
        map (p: summary system p) (
          [
            null
            "mullvad"
            "proton"
            "networkmanager"
          ]
          ++ lib.optional (system == "x86_64-linux") "ivpn"
        )
      )
      [
        "x86_64-linux"
        "aarch64-linux"
      ];
  conflict =
    failed
      (mk "x86_64-linux" {
        nascent.vpn.provider = "proton";
        services.mullvad-vpn.enable = true;
      }).config;
  armIVPN = failed (mk "aarch64-linux" { nascent.vpn.provider = "ivpn"; }).config;
  wrongOptions =
    failed
      (mk "aarch64-linux" {
        nascent.vpn.provider = "proton";
        nascent.vpn.mullvad.earlyBootBlocking = true;
      }).config;
  invalid =
    builtins.tryEval
      (mk "x86_64-linux" { nascent.vpn.provider = "invalid"; }).config.nascent.vpn.provider;
  multiple =
    builtins.tryEval
      (mk "x86_64-linux" {
        nascent.vpn.provider = [
          "mullvad"
          "proton"
        ];
      }).config.nascent.vpn.provider;
  keyringOwnedBySession =
    (mk "aarch64-linux" {
      nascent.vpn = {
        provider = "proton";
        configureKeyring = false;
      };
      services.gnome.gnome-keyring.enable = true;
      security.pam.services.greetd.enableGnomeKeyring = true;
    }).config;
in
assert builtins.all (r: r.failures == [ ]) valid;
assert builtins.all (r: r.catalogVersionMatches) valid;
assert builtins.length conflict > 0;
assert builtins.length armIVPN > 0;
assert builtins.length wrongOptions > 0;
assert !invalid.success && !multiple.success;
assert keyringOwnedBySession.services.gnome.gnome-keyring.enable;
assert builtins.all (r: !r.earlyBlocking && !r.excludeWrapper) valid;
assert builtins.all (r: r.keyring == (r.provider == "proton")) valid;
{
  inherit
    valid
    conflict
    armIVPN
    wrongOptions
    ;
  invalidRejected = !invalid.success;
  multipleRejected = !multiple.success;
}
