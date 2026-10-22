# The coordinator imports the resolver module alongside the software module.
# Keeping this adapter separate permits contract tests without external apps.
{
  lib,
  options,
  apps,
}:
let
  resolverAvailable =
    lib.hasAttrByPath [ "services" "nascentAppImages" "apps" ] options
    && lib.hasAttrByPath [ "services" "nascentAppImages" "enable" ] options;
in
{
  assertions = [
    {
      assertion = apps == [ ] || resolverAvailable;
      message = "Selected AppImages require the services.nascentAppImages resolver module.";
    }
  ];
}
// lib.optionalAttrs resolverAvailable {
  services.nascentAppImages = lib.mkIf (apps != [ ]) {
    enable = true;
    apps = lib.listToAttrs (
      map (app: lib.nameValuePair app.id (app.appImage // { displayName = app.name; })) apps
    );
  };
}
