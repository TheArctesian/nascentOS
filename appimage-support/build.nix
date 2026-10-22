{ nixpkgsPath, pinPath }:
let
  pin = builtins.fromJSON (builtins.readFile pinPath);
  pkgs = import nixpkgsPath {
    system = pin.platform;
    config.allowUnfree = true; # Only the explicitly selected package is evaluated.
  };
in
import ./package.nix { inherit pkgs pin; }
