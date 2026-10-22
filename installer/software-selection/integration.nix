# Assembly module for the final source layout. Native-only tests can import
# default.nix independently; resolver sources remain separately owned.
{ lib, ... }:
let
  resolver = ../../appimage-support/module.nix;
in
{
  imports = [ ./default.nix ] ++ lib.optional (builtins.pathExists resolver) resolver;
}
