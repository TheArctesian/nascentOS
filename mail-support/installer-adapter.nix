# Import alongside installer/software-selection/integration.nix in final assembly.
{
  config,
  lib,
  options,
  ...
}:
{
  imports = [ ./default.nix ];
  config = lib.mkIf (lib.hasAttrByPath [ "nascent" "software" "selected" ] options) {
    nascent.mail = lib.mkIf config.nascent.software.enable (
      lib.mapAttrs (_: value: lib.mkDefault value) (
        import ./selection.nix {
          inherit lib;
          selected = config.nascent.software.selected;
        }
      )
    );
  };
}
