{
  config,
  lib,
  pkgs,
  options,
  ...
}:
let
  cfg = config.nascent.software;
  catalog = builtins.fromJSON (builtins.readFile ./catalog.json);
  manifest = import ./availability.nix { inherit pkgs catalog; };
  byId = lib.listToAttrs (map (app: lib.nameValuePair app.id app) manifest.apps);
  known = lib.filter (id: builtins.hasAttr id byId) cfg.selected;
  chosen = map (id: byId.${id}) known;
  native = lib.filter (
    app: app.kind == "package" && app.available && (app.backend or "nixpkgs") == "nixpkgs"
  ) chosen;
  appImages = lib.filter (
    app: app.kind == "package" && app.available && (app.backend or "nixpkgs") == "appimage"
  ) chosen;
  appImageIntegration = import ./appimage-integration.nix {
    inherit lib options;
    apps = appImages;
  };
  fonts = lib.filter (app: (app.role or "application") == "font") native;
  applications = lib.filter (app: (app.role or "application") != "font") native;
  getPackage =
    app:
    if app.id == "firefox" && config.programs.firefox.enable then
      config.programs.firefox.finalPackage
    else
      lib.getAttrFromPath (lib.splitString "." app.package) pkgs;
  # The predicate contains only explicitly selected unfree packages. Merely
  # displaying an optional proprietary application never permits its build.
  unfreeNames =
    map (app: lib.getName (getPackage app)) (lib.filter (app: app.packageUnfree or false) native)
    ++ map (app: app.id) (lib.filter (app: app.packageUnfree or false) appImages);
  # Any nixpkgs attribute the user chose in `nascent software search`.
  extraPaths = map (name: lib.splitString "." name) cfg.packages;
  extraKnown = lib.filter (path: lib.hasAttrByPath path pkgs) extraPaths;
  extraPackages = map (path: lib.getAttrFromPath path pkgs) extraKnown;
  agentAdapters = {
    claude-code = "claude";
    codex = "codex";
    opencode = "opencode";
  };
in
{
  options.nascent.software = {
    enable = lib.mkEnableOption "the installer-selected software profile";
    selected = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = map (app: app.id) (
        lib.filter (app: (app.default or false) && app.available && app.kind == "package") manifest.apps
      );
      description = "Stable software catalog IDs selected during installation.";
    };
    packages = lib.mkOption {
      type = lib.types.listOf (lib.types.strMatching "[A-Za-z0-9_+-][A-Za-z0-9_.+-]*");
      default = [ ];
      example = [
        "ripgrep"
        "python3Packages.requests"
      ];
      description = "Extra nixpkgs attribute paths chosen with `nascent software search`. Listing an unfree package here permits it.";
    };
  };
  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      appImageIntegration
      {
        assertions = [
          {
            assertion = builtins.length cfg.selected == builtins.length (lib.unique cfg.selected);
            message = "nascent.software.selected contains duplicate IDs.";
          }
          {
            assertion = builtins.length extraKnown == builtins.length extraPaths;
            message = "Unknown nixpkgs packages in nascent.software.packages: ${lib.concatStringsSep ", " (map (lib.concatStringsSep ".") (lib.subtractLists extraKnown extraPaths))}.";
          }
          {
            assertion = builtins.all (id: builtins.hasAttr id byId) cfg.selected;
            message = "Unknown nascent software IDs: ${lib.concatStringsSep ", " (lib.subtractLists known cfg.selected)}.";
          }
        ]
        ++ map (app: {
          assertion = app.available && app.kind == "package";
          message = "Cannot select ${app.id}: ${if app.reason == null then "unavailable" else app.reason}";
        }) chosen;
        nixpkgs.config.allowUnfreePackages = unfreeNames ++ map lib.getName extraPackages;
        environment.systemPackages = map getPackage applications ++ extraPackages;
        # Catalog ID -> agent adapter name (the provider's command).
        environment.etc = lib.mapAttrs' (id: command: {
          name = "nascentos/agent-adapters/${command}";
          value = {
            mode = "0555";
            text = ''
              #!/usr/bin/env bash
              set -euo pipefail
              exec ${command} "$@"
            '';
          };
        }) (lib.filterAttrs (id: _: builtins.elem id cfg.selected) agentAdapters);
        fonts.packages = map getPackage fonts;
        fonts.fontconfig.defaultFonts = {
          monospace = lib.mkIf (builtins.elem "fira-code" cfg.selected) (lib.mkDefault [ "Fira Code" ]);
          sansSerif = lib.mkIf (builtins.elem "open-dyslexic" cfg.selected) (
            lib.mkDefault [ "OpenDyslexic" ]
          );
        };
      }
    ]
  );
}
