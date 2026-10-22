{
  pkgs,
  catalog ? builtins.fromJSON (builtins.readFile ./catalog.json),
}:
let
  lib = pkgs.lib;
  system = pkgs.stdenv.hostPlatform.system;
  inspect =
    app:
    let
      path = lib.splitString "." (app.package or "");
      exists = app ? package && lib.hasAttrByPath path pkgs;
      package = lib.attrByPath path null pkgs;
      meta = if exists then package.meta or { } else { };
      licenses = lib.toList (meta.license or [ ]);
      unfree = builtins.any (license: !(license.free or true)) licenses;
      supported = builtins.elem system app.platforms;
      nativeSupported = exists && lib.meta.availableOn pkgs.stdenv.hostPlatform package;
      broken = meta.broken or false;
      mismatch = unfree && !(app.proprietary or false);
      appImage = import ./appimage-validation.nix { inherit lib system app; };
      reason =
        if !supported then
          "Not offered on ${system}; supported platforms: ${lib.concatStringsSep ", " app.platforms}."
        else if app.kind == "manual" then
          app.reason or "Requires a manual installation and license review."
        else if app.kind == "web" then
          "No native pinned nixpkgs package; web shortcuts are not installable choices."
        else if app.kind != "package" then
          "Unknown installation type."
        else if (app.backend or "nixpkgs") == "appimage" then
          appImage.reason
        else if (app.backend or "nixpkgs") != "nixpkgs" then
          "Installation backend ${app.backend} is not supported; only pinned nixpkgs packages can be selected."
        else if !exists then
          "Package ${app.package or "(missing)"} is absent from pinned nixpkgs."
        else if !nativeSupported then
          "Pinned nixpkgs does not support this package on ${system}."
        else if broken then
          "Pinned nixpkgs marks this package as broken."
        else if mismatch then
          "Package license metadata requires a proprietary label; catalog review needed."
        else
          null;
    in
    app
    // {
      available = reason == null;
      inherit reason;
    }
    // lib.optionalAttrs (app.kind == "package" && exists) {
      packageUnfree = unfree;
    }
    // lib.optionalAttrs (app.kind == "package" && (app.backend or "nixpkgs") == "appimage") {
      packageUnfree = appImage.unfree;
    };
in
catalog
// {
  inherit system;
  apps = map inspect catalog.apps;
}
