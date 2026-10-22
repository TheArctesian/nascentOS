{ nixpkgs, system }:
let
  lib = import (nixpkgs + "/lib");
  pkgs = import nixpkgs { inherit system; };
  evaluate =
    settings:
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [
        ../default.nix
        {
          nascent.mail = settings;
          system.stateVersion = "26.05";
        }
      ];
    }).config;
  failures =
    config: lib.filter (a: !a.assertion && lib.hasPrefix "nascent.mail" a.message) config.assertions;
  valid = settings: failures (evaluate ({ enable = true; } // settings)) == [ ];
  disabled = evaluate { enable = false; };
  proton = evaluate { enable = true; };
  thunderbird = evaluate {
    enable = true;
    clients = [ "thunderbird" ];
    bridge.enable = true;
  };
  geary = evaluate {
    enable = true;
    clients = [ "geary" ];
  };
  evolution = evaluate {
    enable = true;
    clients = [ "evolution" ];
  };
  empty = evaluate {
    enable = true;
    clients = [ ];
  };
  mapSelection = selected: import ../selection.nix { inherit lib selected; };
  adapter =
    selected:
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [
        ../installer-adapter.nix
        {
          options.nascent.software = {
            enable = lib.mkOption {
              type = lib.types.bool;
              default = true;
            };
            selected = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = selected;
            };
          };
          config.system.stateVersion = "26.05";
        }
      ];
    }).config;
  adapted = adapter [
    "thunderbird"
    "protonmail-bridge"
    "firefox"
  ];
  noPicker =
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [ ../installer-adapter.nix ];
    }).config;
  catalog = builtins.fromJSON (builtins.readFile ../catalog.json);
in
assert !(disabled.nascent.mail.bridge.enable);
assert !(disabled.services.gnome.gnome-keyring.enable);
assert !(noPicker.nascent.mail.enable);
assert valid { clients = [ "thunderbird" ]; };
assert valid {
  clients = [
    "geary"
    "evolution"
  ];
};
assert valid { clients = [ ]; };
assert
  !(valid {
    clients = [
      "thunderbird"
      "thunderbird"
    ];
  });
assert
  !(valid {
    clients = [ "thunderbird" ];
    defaultClient = "geary";
  });
assert (valid { }) == (system == "x86_64-linux");
assert thunderbird.services.gnome.gnome-keyring.enable;
assert !(thunderbird.services.protonmail-bridge.enable);
assert !(thunderbird.systemd.user.services ? protonmail-bridge);
assert
  thunderbird.xdg.mime.defaultApplications."x-scheme-handler/mailto"
  == "nascent-mail-thunderbird.desktop";
assert !(empty.xdg.mime.defaultApplications ? "x-scheme-handler/mailto");
assert geary.programs.geary.enable && geary.programs.dconf.enable;
assert evolution.programs.evolution.enable && evolution.services.gnome.evolution-data-server.enable;
assert adapted.nascent.mail.clients == [ "thunderbird" ] && adapted.nascent.mail.bridge.enable;
assert
  (mapSelection [
    "geary"
    "protonmail-desktop"
  ]).defaultClient == "protonmail-desktop";
assert !(mapSelection [ "firefox" ]).enable;
assert (mapSelection [ "protonmail-bridge" ]).defaultClient == null;
assert builtins.all (a: a.backend == "nixpkgs" && !a.proprietary) catalog.apps;
{
  inherit system;
  protonSupported = failures proton == [ ];
  selected = adapted.nascent.mail;
  packages =
    map
      (id: {
        inherit id;
        version = pkgs.${id}.version;
        supported = lib.meta.availableOn pkgs.stdenv.hostPlatform pkgs.${id};
      })
      [
        "protonmail-desktop"
        "protonmail-bridge-gui"
        "thunderbird"
        "geary"
        "evolution"
      ];
  # Force selected package/desktop derivations, without claiming Linux builds.
  derivations = map (p: p.drvPath) (lib.take 3 thunderbird.environment.systemPackages);
  clientDerivations = map (id: pkgs.${id}.drvPath) (
    lib.filter (id: lib.meta.availableOn pkgs.stdenv.hostPlatform pkgs.${id}) [
      "protonmail-desktop"
      "thunderbird"
      "geary"
      "evolution"
    ]
  );
}
