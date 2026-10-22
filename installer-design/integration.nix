# Import from modules/installer/default.nix and use the two adapters below.
{ pkgs }:
{
  # Apply after the existing nascent branding copy in the extensions postPatch.
  extensionPostPatch = ''
    cp ${./branding/stylesheet.qss} branding/nascent/stylesheet.qss
  '';

  # Apply to the existing calamares-nixos derivation, before the launch wrapper.
  installerAttrs = old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.python3 ];
    postPatch = (old.postPatch or "") + ''
      python3 ${./apply.py} . ${./NascentLayout.h}
    '';
  };
}
