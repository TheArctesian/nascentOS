# Apply to the existing nascentOS-patched extensions, before passing them to
# calamares-nixos.override. The original hardware/storage handoff stays intact.
{ pkgs, extensions }:
let
  manifest = pkgs.writeText "nascent-software-manifest.json" (
    builtins.toJSON (import ./availability.nix { inherit pkgs; })
  );
in
extensions.overrideAttrs (old: {
  nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.python3 ];
  postPatch = (old.postPatch or "") + ''
    python3 ${./patch-extension.py} . ${manifest}
    cp ${./handoff.py} modules/nixos/nascent_software.py
    cp ${./nascent_software_model.py} modules/nixos/nascent_software_model.py
    cp ${./nascent_optional_profiles.py} modules/nixos/nascent_optional_profiles.py
    mkdir -p modules/nixos/vpn-support
    cp ${../../vpn-support/installer_adapter.py} modules/nixos/vpn-support/installer_adapter.py
    cp ${../../vpn-support/catalog.json} modules/nixos/vpn-support/catalog.json
  '';
})
