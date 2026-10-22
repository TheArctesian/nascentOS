# Import alongside the software picker only after merging the catalog rows.
{ config, lib, ... }:
let
  ids = map (app: app.id) (builtins.fromJSON (builtins.readFile ./catalog.json)).apps;
  selected = builtins.filter (id: builtins.elem id ids) config.nascent.software.selected;
in
{
  imports = [ ./module.nix ];
  config = lib.mkIf config.nascent.software.enable {
    assertions = [
      {
        assertion = builtins.length selected <= 1;
        message = "Select at most one preferred password manager in the software picker.";
      }
    ];
    nascent.passwords = {
      enable = lib.mkDefault true;
      manager = lib.mkDefault (if selected == [ ] then "none" else builtins.head selected);
    };
  };
}
