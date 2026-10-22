{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (lib) mkOption mkEnableOption types;
  cfg = config.services.nascentAppImages;
  state = "/var/lib/nascent-appimages";
  recipeSource = builtins.path {
    path = ./.;
    name = "nascent-appimage-support";
    filter = path: type: !(lib.hasInfix "__pycache__" path) && !(lib.hasSuffix ".pyc" path);
  };
  pinFor = id: app: {
    inherit id;
    inherit (app) repository platform license;
    inherit (app.pin) version url hash;
  };
  seeds = lib.mapAttrs (
    id: app:
    import ./package.nix {
      inherit pkgs;
      pin = pinFor id app;
    }
  ) cfg.apps;
  updaterConfig = pkgs.writeText "nascent-appimages.json" (
    builtins.toJSON {
      stateDir = state;
      nixpkgsPath = "${pkgs.path}";
      buildFile = "${recipeSource}/build.nix";
      recipePath = "${recipeSource}";
      apps = lib.mapAttrs (id: app: {
        inherit (app)
          repository
          assetName
          maxBytes
          autoActivate
          ;
        pin = pinFor id app;
        initialPackage = "${seeds.${id}}";
      }) cfg.apps;
    }
  );
  updater = pkgs.writeShellApplication {
    name = "nascent-appimages";
    runtimeInputs = [
      pkgs.python3
      pkgs.nix
    ];
    text = ''
      exec python3 ${./updater.py} --config ${updaterConfig} "$@"
    '';
  };
  launcher =
    id: app:
    pkgs.symlinkJoin {
      name = "${id}-managed-appimage";
      paths = [
        (pkgs.writeShellScriptBin id ''
          package=${lib.escapeShellArg "${state}/${id}/current/package"}
          if [ ! -e "$package" ]; then package=${seeds.${id}}; fi
          exec "$package/bin/${id}" "$@"
        '')
        (pkgs.makeDesktopItem {
          name = "nascent-appimage-${id}";
          desktopName = app.displayName;
          exec = "${id} %U";
          icon = "application-x-executable";
          categories = [ "Utility" ];
          terminal = false;
        })
      ];
    };
in
{
  options.services.nascentAppImages = {
    enable = mkEnableOption "curated Nix-wrapped AppImages and their update watchdog";
    onCalendar = mkOption {
      type = types.str;
      default = "daily";
    };
    apps = mkOption {
      default = { };
      description = "Explicit allowlist; no applications are selected by default.";
      type = types.attrsOf (
        types.submodule (
          { name, ... }: {
            options = {
              displayName = mkOption {
                type = types.str;
                default = name;
              };
              repository = mkOption { type = types.strMatching "[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"; };
              assetName = mkOption {
                type = types.str;
                description = "Exact release asset filename; optional {tag} placeholder. No regex or URL.";
              };
              platform = mkOption {
                type = types.enum [
                  "x86_64-linux"
                  "aarch64-linux"
                ];
              };
              license = mkOption {
                type = types.str;
                description = "Explicit key in lib.licenses; selection acknowledges vendor licensing.";
              };
              maxBytes = mkOption {
                type = types.ints.positive;
                default = 1073741824;
              };
              autoActivate = mkOption {
                type = types.bool;
                default = true;
              };
              pin = {
                version = mkOption { type = types.str; };
                url = mkOption {
                  type = types.str;
                  description = "Reviewed, versioned vendor GitHub release asset URL.";
                };
                hash = mkOption { type = types.strMatching "sha256-[A-Za-z0-9+/]{43}="; };
              };
            };
          }
        )
      );
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = lib.mapAttrsToList (id: app: {
      assertion =
        builtins.match "[a-z][a-z0-9-]*" id != null
        && app.platform == pkgs.stdenv.hostPlatform.system
        && builtins.hasAttr app.license lib.licenses
        && lib.hasPrefix "https://github.com/${app.repository}/releases/download/" app.pin.url;
      message = "AppImage ${id}: require a safe lowercase ID, native platform, lib.licenses key and versioned URL in the allowlisted repository.";
    }) cfg.apps;
    environment.systemPackages = [ updater ] ++ lib.mapAttrsToList launcher cfg.apps;
    users.groups.nascent-appimages = { };
    users.users.nascent-appimages = {
      isSystemUser = true;
      group = "nascent-appimages";
      home = state;
    };
    systemd.services.nascent-appimages = {
      description = "Validate and update selected vendor AppImages";
      wants = [ "network-online.target" ];
      after = [
        "network-online.target"
        "nix-daemon.service"
      ];
      serviceConfig = {
        Type = "oneshot";
        User = "nascent-appimages";
        Group = "nascent-appimages";
        StateDirectory = "nascent-appimages";
        StateDirectoryMode = "0755";
        UMask = "0022";
        ExecStart = "${updater}/bin/nascent-appimages update";
        TimeoutStartSec = "2h";
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        RestrictSUIDSGID = true;
      };
    };
    systemd.timers.nascent-appimages = lib.mkIf (cfg.apps != { }) {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = cfg.onCalendar;
        RandomizedDelaySec = "1h";
        Persistent = true;
      };
    };
  };
}
