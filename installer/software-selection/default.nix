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
            assertion = builtins.all (id: builtins.hasAttr id byId) cfg.selected;
            message = "Unknown nascent software IDs: ${lib.concatStringsSep ", " (lib.subtractLists known cfg.selected)}.";
          }
        ]
        ++ map (app: {
          assertion = app.available && app.kind == "package";
          message = "Cannot select ${app.id}: ${if app.reason == null then "unavailable" else app.reason}";
        }) chosen;
        nixpkgs.config.allowUnfreePackages = unfreeNames;
        environment.systemPackages = map getPackage applications;
        environment.etc = lib.listToAttrs (
          map
            (id: {
              name = "nascentos/agent-adapters/${id}";
              value = {
                mode = "0555";
                text = ''
                  #!/usr/bin/env bash
                  set -euo pipefail
                  exec ${id} "$@"
                '';
              };
            })
            (
              lib.filter (id: builtins.elem id cfg.selected) [
                "codex"
                "opencode"
              ]
            )
        );
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
