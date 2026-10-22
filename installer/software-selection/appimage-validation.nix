# A reviewed catalog entry is the only route into the separately supplied
# AppImage resolver. This function performs no network or package evaluation.
{
  lib,
  system,
  app,
}:
let
  rawData = app.appImage or { };
  data = if builtins.isAttrs rawData then rawData else { };
  rawPin = data.pin or { };
  pin = if builtins.isAttrs rawPin then rawPin else { };
  matches = pattern: value: builtins.isString value && builtins.match pattern value != null;
  fields = [
    "repository"
    "assetName"
    "platform"
    "license"
    "pin"
    "autoActivate"
    "maxBytes"
  ];
  shape =
    builtins.isAttrs rawData
    && builtins.isAttrs rawPin
    && lib.all (key: builtins.elem key fields) (builtins.attrNames data)
    && lib.all (
      key:
      builtins.elem key [
        "version"
        "url"
        "hash"
      ]
    ) (builtins.attrNames pin);
  repository = data.repository or "";
  assetName = data.assetName or "";
  version = pin.version or "";
  asset =
    if builtins.isString assetName && builtins.isString version then
      lib.replaceStrings [ "{tag}" ] [ version ] assetName
    else
      "";
  license = data.license or "";
  licenseValid = builtins.isString license && builtins.hasAttr license lib.licenses;
  unfree = licenseValid && !(lib.licenses.${license}.free or true);
  valid =
    shape
    && matches "[a-z][a-z0-9-]*" app.id
    && matches "[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*" repository
    && matches "[A-Za-z0-9][A-Za-z0-9._+-]{0,127}" version
    && matches "[A-Za-z0-9][A-Za-z0-9._+-]*\\.AppImage" asset
    && (pin.url or "") == "https://github.com/${repository}/releases/download/${version}/${asset}"
    && matches "sha256-[A-Za-z0-9+/]{43}=" (pin.hash or "")
    && (data.platform or "") == system
    && licenseValid
    && builtins.isBool (data.autoActivate or true)
    && builtins.isInt (data.maxBytes or 1073741824)
    && (data.maxBytes or 1073741824) > 0;
  reason =
    if (app.reviewed or false) != true then
      "AppImage metadata has not been reviewed."
    else if !valid then
      "AppImage requires a native platform, known license, safe GitHub repository/release asset and explicit SHA-256 pin."
    else if unfree && !(app.proprietary or false) then
      "AppImage license requires a proprietary label; catalog review needed."
    else
      null;
in
{
  inherit reason unfree;
  available = reason == null;
}
