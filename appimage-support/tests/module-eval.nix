{ nixpkgs }:
let
  evaluate =
    settings:
    import (nixpkgs + "/nixos/lib/eval-config.nix") {
      system = "x86_64-linux";
      modules = [
        ../module.nix
        {
          system.stateVersion = "26.05";
          services.nascentAppImages = settings;
        }
      ];
    };
  app = {
    repository = "vendor/example";
    assetName = "example-{tag}.AppImage";
    platform = "x86_64-linux";
    license = "mit";
    pin = {
      version = "v1.0.0";
      url = "https://github.com/vendor/example/releases/download/v1.0.0/example-v1.0.0.AppImage";
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
  };
  empty = (evaluate { enable = true; }).config;
  selected =
    (evaluate {
      enable = true;
      apps.example = app;
    }).config;
  disabled = (evaluate { enable = false; }).config;
  wrongPlatform =
    (evaluate {
      enable = true;
      apps.example = app // {
        platform = "aarch64-linux";
      };
    }).config;
  appAssertions =
    cfg:
    (import ../module.nix {
      config = cfg;
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      lib = import (nixpkgs + "/lib");
    }).config.content.assertions;
  pin = {
    id = "example";
    inherit (app) repository platform license;
  }
  // app.pin;
  package = import ../package.nix {
    pkgs = import nixpkgs { system = "x86_64-linux"; };
    inherit pin;
  };
in
assert !(disabled.systemd.services ? nascent-appimages);
assert !(empty.systemd.timers ? nascent-appimages);
assert selected.systemd.timers.nascent-appimages.timerConfig.OnCalendar == "daily";
assert selected.systemd.services.nascent-appimages.serviceConfig.User == "nascent-appimages";
assert builtins.all (a: a.assertion) (appAssertions selected);
assert !(builtins.head (appAssertions wrongPlatform)).assertion;
assert package.meta.mainProgram == "example";
assert builtins.isString package.drvPath;
# Force service command/config and launcher derivations to evaluate without downloads.
assert builtins.isString selected.systemd.services.nascent-appimages.serviceConfig.ExecStart;
assert builtins.all (p: builtins.isString p.drvPath) selected.environment.systemPackages;
true
