# SPDX-License-Identifier: GPL-3.0-only
# Adapted from Garuda Nix Subsystem gaming.nix; see SOURCES.md.
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.gaming;
  supported = package: lib.meta.availableOn pkgs.stdenv.hostPlatform package;
  steamSupported = pkgs.stdenv.hostPlatform.system == "x86_64-linux";
in
{
  options.nascent.gaming = {
    enable = lib.mkEnableOption "the optional nascentOS gaming profile";
    gamemode.enable = lib.mkOption {
      type = lib.types.bool;
      default = cfg.enable;
      description = "Enable Feral GameMode on demand; use gamemoderun for each game.";
    };
    gamescope.enable = lib.mkOption {
      type = lib.types.bool;
      default = cfg.enable;
      description = "Install gamescope for nested game sessions inside the existing desktop.";
    };
    steam = {
      enable = lib.mkEnableOption ''
        proprietary Steam (x86_64 Linux only). Selecting this permits only the
        Steam package names in Nixpkgs, not all unfree software. Valve terms
        and game licenses remain the user's responsibility
      '';
      gamescopeSession.enable = lib.mkEnableOption ''
        the additional Steam gamescope session entry. Requires Steam and
        gamescope; does not replace the Hyprland login session
      '';
    };
    tuning.maxMapCount.enable = lib.mkEnableOption ''
      Garuda's optional vm.max_map_count=16777216 compatibility setting for
      games needing many memory mappings (system-wide, not a speed guarantee)
    '';
  };

  config = lib.mkMerge [
    {
      assertions = [
        {
          assertion =
            cfg.enable
            || !(
              cfg.gamemode.enable
              || cfg.gamescope.enable
              || cfg.steam.enable
              || cfg.steam.gamescopeSession.enable
              || cfg.tuning.maxMapCount.enable
            );
          message = "nascent.gaming components require nascent.gaming.enable = true.";
        }
        {
          assertion = !cfg.enable || pkgs.stdenv.hostPlatform.isLinux;
          message = "nascent.gaming requires a Linux target.";
        }
        {
          assertion = !cfg.gamemode.enable || supported pkgs.gamemode;
          message = "GameMode is unavailable on this target according to Nixpkgs metadata.";
        }
        {
          assertion = !cfg.gamescope.enable || supported pkgs.gamescope;
          message = "gamescope is unavailable on this target according to Nixpkgs metadata.";
        }
        {
          assertion = !cfg.steam.enable || steamSupported;
          message = "nascent.gaming Steam requires x86_64-linux with x86 32-bit compatibility; ARM emulation is not provided.";
        }
        {
          assertion = !cfg.steam.gamescopeSession.enable || (cfg.steam.enable && cfg.gamescope.enable);
          message = "The Steam gamescope session requires both nascent.gaming.steam.enable and nascent.gaming.gamescope.enable.";
        }
      ];
    }
    (lib.mkIf cfg.enable {
      programs.gamemode.enable = lib.mkDefault cfg.gamemode.enable;
      programs.gamescope.enable = lib.mkDefault cfg.gamescope.enable;
      programs.steam.enable = lib.mkDefault (cfg.steam.enable && steamSupported);
      programs.steam.gamescopeSession.enable = lib.mkDefault cfg.steam.gamescopeSession.enable;
      # Nixpkgs merges this list additively, including with the software picker's
      # allowUnfreePredicate; never broaden the global unfree policy.
      nixpkgs.config = lib.mkIf cfg.steam.enable {
        allowUnfreePackages = [
          "steam"
          "steam-unwrapped"
        ];
      };
      boot.kernel.sysctl."vm.max_map_count" = lib.mkIf cfg.tuning.maxMapCount.enable (
        lib.mkOverride 950 16777216
      );
    })
  ];
}
