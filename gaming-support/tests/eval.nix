# SPDX-License-Identifier: AGPL-3.0-only
{ nixpkgs }:
let
  lib = import (nixpkgs + "/lib");
  mk =
    system: settings: extra:
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [
        ../default.nix
        {
          system.stateVersion = "26.05";
          boot.loader.grub.enable = false;
          fileSystems."/" = {
            device = "/dev/test-root";
            fsType = "ext4";
          };
          nascent.gaming = settings;
        }
        extra
      ];
    }).config;
  valid = cfg: builtins.all (a: a.assertion) cfg.assertions;
  force = cfg: builtins.seq cfg.system.build.toplevel.drvPath true;
  off = mk "x86_64-linux" { } { };
  free = system: mk system { enable = true; } { };
  steam =
    mk "x86_64-linux"
      {
        enable = true;
        steam.enable = true;
        steam.gamescopeSession.enable = true;
        tuning.maxMapCount.enable = true;
      }
      {
        # Exercise coexistence with the software picker's license policy.
        nixpkgs.config.allowUnfreePredicate = p: lib.getName p == "example-proprietary";
      };
  armSteam = mk "aarch64-linux" {
    enable = true;
    steam.enable = true;
  } { };
  badSession = mk "x86_64-linux" {
    enable = true;
    steam.gamescopeSession.enable = true;
  } { };
  orphan = mk "x86_64-linux" { gamemode.enable = true; } { };
  componentSelections = map (settings: mk "x86_64-linux" ({ enable = true; } // settings) { }) [
    { gamescope.enable = false; }
    { gamemode.enable = false; }
    {
      gamemode.enable = false;
      gamescope.enable = false;
      steam.enable = true;
    }
  ];
  tunedOverride = mk "aarch64-linux" {
    enable = true;
    tuning.maxMapCount.enable = true;
  } { boot.kernel.sysctl."vm.max_map_count" = 2097152; };
  overridden = mk "x86_64-linux" { enable = true; } {
    programs.gamemode.enable = false;
    programs.gamescope.enable = false;
  };
  desktop = mk "aarch64-linux" { enable = true; } {
    programs.hyprland.enable = true;
    xdg.portal.extraPortals = [ ];
    services.greetd.enable = true;
    services.greetd.settings.default_session = {
      command = "Hyprland";
      user = "greeter";
    };
  };
  freeCheck =
    system:
    let
      cfg = free system;
    in
    assert valid cfg;
    assert cfg.programs.gamemode.enable && cfg.programs.gamescope.enable;
    assert !cfg.programs.steam.enable;
    assert !(cfg.nixpkgs.config.allowUnfree or false);
    assert (cfg.nixpkgs.config.allowUnfreePackages or [ ]) == [ ];
    assert !cfg.programs.gamescope.capSysNice;
    assert cfg.boot.kernel.sysctl."vm.max_map_count" == 1048576;
    assert cfg.powerManagement.cpuFreqGovernor == null;
    assert !cfg.services.ananicy.enable;
    force cfg;
in
assert valid off && force off;
assert
  !off.programs.gamemode.enable && !off.programs.gamescope.enable && !off.programs.steam.enable;
assert valid steam && force steam;
assert steam.programs.steam.gamescopeSession.enable;
assert steam.hardware.graphics.enable32Bit;
assert steam.boot.kernel.sysctl."vm.max_map_count" == 16777216;
assert
  steam.nixpkgs.config.allowUnfreePackages == [
    "steam"
    "steam-unwrapped"
  ];
assert steam.nixpkgs.config.allowUnfreePredicate { pname = "example-proprietary"; };
assert !(steam.nixpkgs.config.allowUnfreePredicate { pname = "unrelated"; });
assert !steam.programs.steam.remotePlay.openFirewall;
assert !steam.programs.steam.localNetworkGameTransfers.openFirewall;
assert !armSteam.programs.steam.enable && !valid armSteam;
assert !valid badSession && !valid orphan;
assert builtins.all (cfg: valid cfg && force cfg) componentSelections;
assert valid tunedOverride && tunedOverride.boot.kernel.sysctl."vm.max_map_count" == 2097152;
assert
  valid overridden && !overridden.programs.gamemode.enable && !overridden.programs.gamescope.enable;
assert valid desktop && force desktop;
assert desktop.programs.hyprland.enable && desktop.xdg.portal.enable;
assert desktop.services.greetd.settings.default_session.command == "Hyprland";
{
  disabled = true;
  freeX86 = freeCheck "x86_64-linux";
  freeARM = freeCheck "aarch64-linux";
  steamX86 = true;
  invalidSelectionsRejected = true;
  nativeOverridesPreserved = true;
  independentComponents = true;
  waylandConfigurationPreserved = true;
}
