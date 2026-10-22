{ pkgs }:
let
  python = pkgs.python3.withPackages (ps: [ ps.pyside6 ]);
  manifest = pkgs.writeText "nascent-software-manifest.json" (
    builtins.toJSON (import ./availability.nix { inherit pkgs; })
  );
in
pkgs.runCommand "nascent-software-selection"
  {
    nativeBuildInputs = [
      pkgs.makeWrapper
      pkgs.qt6.wrapQtAppsHook
    ];
    buildInputs = [
      pkgs.qt6.qtbase
      pkgs.qt6.qtwayland
      pkgs.qt6.qtsvg
    ];
    dontWrapQtApps = true;
    meta = {
      description = "nascentOS graphical installer software picker and selection recorder";
      license = pkgs.lib.licenses.agpl3Only;
      platforms = [
        "aarch64-linux"
        "x86_64-linux"
      ];
    };
  }
  ''
    mkdir -p $out/bin $out/lib/nascent-software-selection $out/share/nascent-software-selection
    cp ${./.}/*.py $out/lib/nascent-software-selection/
    mkdir -p $out/lib/nascent-software-selection/vpn-support
    cp ${../../vpn-support/installer_adapter.py} $out/lib/nascent-software-selection/vpn-support/installer_adapter.py
    cp ${../../vpn-support/catalog.json} $out/lib/nascent-software-selection/vpn-support/catalog.json
    cp ${manifest} $out/share/nascent-software-selection/manifest.json
    makeWrapper ${python}/bin/python3 $out/bin/nascent-software-picker \
      --prefix PYTHONPATH : $out/lib/nascent-software-selection \
      --add-flags "$out/lib/nascent-software-selection/picker.py" \
      --add-flags "--manifest $out/share/nascent-software-selection/manifest.json" \
      --add-flags "--icon-path ${pkgs.papirus-icon-theme}/share/icons"
    makeWrapper ${python}/bin/python3 $out/bin/nascent-software-record \
      --prefix PYTHONPATH : $out/lib/nascent-software-selection \
      --add-flags "$out/lib/nascent-software-selection/handoff.py record" \
      --add-flags "--manifest $out/share/nascent-software-selection/manifest.json"
    wrapQtApp $out/bin/nascent-software-picker
  ''
