# Pure mapping: stable picker IDs to mail options. No account/provider inference.
{ lib, selected }:
let
  priority = [
    "protonmail-desktop"
    "thunderbird"
    "geary"
    "evolution"
  ];
  clients = builtins.filter (id: builtins.elem id selected) priority;
  bridge = builtins.elem "protonmail-bridge" selected;
in
{
  enable = clients != [ ] || bridge;
  inherit clients;
  defaultClient = if clients == [ ] then null else builtins.head clients;
  bridge.enable = bridge;
}
