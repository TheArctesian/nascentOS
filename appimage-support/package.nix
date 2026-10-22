{ pkgs, pin }:
assert pkgs.stdenv.hostPlatform.system == pin.platform;
pkgs.appimageTools.wrapType2 {
  pname = pin.id;
  version = pin.version;
  src = pkgs.fetchurl {
    inherit (pin) url hash;
    name = "${pin.id}-${pin.version}.AppImage";
  };
  meta = {
    description = "Vendor AppImage for ${pin.id}";
    homepage = "https://github.com/${pin.repository}";
    license = pkgs.lib.licenses.${pin.license};
    platforms = [ pin.platform ];
    mainProgram = pin.id;
    sourceProvenance = [ pkgs.lib.sourceTypes.binaryNativeCode ];
  };
}
