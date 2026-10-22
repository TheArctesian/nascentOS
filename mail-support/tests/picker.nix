# pickerRoot must be an assembly copy with merge-catalog.py already applied.
{
  nixpkgs,
  system,
  pickerRoot,
}:
let
  lib = import (nixpkgs + "/lib");
  pkgs = import nixpkgs { inherit system; };
  manifest = import (pickerRoot + "/availability.nix") { inherit pkgs; };
  defaults = map (app: app.id) (
    lib.filter (a: a.default && a.available && !a.proprietary) manifest.apps
  );
  evaluate =
    selected:
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [
        (pickerRoot + "/default.nix")
        ../installer-adapter.nix
        {
          nascent.software = {
            enable = true;
            inherit selected;
          };
          system.stateVersion = "26.05";
        }
      ];
    }).config;
  normal = evaluate defaults;
  alternate = evaluate [
    "thunderbird"
    "protonmail-bridge"
  ];
  bridgeOnly = evaluate [ "protonmail-bridge" ];
  failures =
    cfg:
    lib.filter (
      a:
      !a.assertion && (lib.hasPrefix "nascent.mail" a.message || lib.hasPrefix "Cannot select " a.message)
    ) cfg.assertions;
in
assert failures normal == [ ];
assert failures alternate == [ ];
assert failures bridgeOnly == [ ];
assert
  normal.nascent.mail.clients == (lib.optional (system == "x86_64-linux") "protonmail-desktop");
assert alternate.nascent.mail.defaultClient == "thunderbird";
assert alternate.nascent.mail.bridge.enable;
assert bridgeOnly.nascent.mail.defaultClient == null;
assert !(bridgeOnly.xdg.mime.defaultApplications ? "x-scheme-handler/mailto");
{
  inherit system defaults;
  alternate = alternate.nascent.mail;
}
