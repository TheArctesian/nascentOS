# Import from modules/default.nix alongside the existing desktop module.
{ config, lib, ... }:
{
  imports = [ ./module.nix ];
  nascent.shell.enable = lib.mkDefault config.nascent.desktop.enable;
}
