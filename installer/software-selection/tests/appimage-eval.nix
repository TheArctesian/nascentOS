# Synthetic metadata only: no catalog entry, download, build, or update enabled.
{ nixpkgs, system }:
let
  pkgs = import nixpkgs { inherit system; };
  lib = pkgs.lib;
  reviewed = {
    id = "synthetic-appimage";
    name = "Synthetic contract fixture";
    kind = "package";
    backend = "appimage";
    platforms = [ system ];
    proprietary = false;
    reviewed = true;
    appImage = {
      repository = "example/fixture";
      assetName = "fixture-{tag}.AppImage";
      platform = system;
      license = "mit";
      autoActivate = false;
      maxBytes = 1024;
      pin = {
        version = "v1.0";
        url = "https://github.com/example/fixture/releases/download/v1.0/fixture-v1.0.AppImage";
        hash = lib.fakeHash;
      };
    };
  };
  evaluate =
    app:
    builtins.head
      (import ../availability.nix {
        inherit pkgs;
        catalog.apps = [ app ];
      }).apps;
  alter = changes: reviewed // { appImage = reviewed.appImage // changes; };
  invalid = [
    (reviewed // { reviewed = false; })
    (reviewed // { appImage = "malformed"; })
    (alter { platform = "riscv64-linux"; })
    (alter { license = "not-a-license"; })
    (alter { maxBytes = -1; })
    (alter { extraArgument = true; })
    (alter { pin = { }; })
    (alter {
      pin = reviewed.appImage.pin // {
        url = "https://example.com/fixture.AppImage";
      };
    })
    (alter {
      pin = reviewed.appImage.pin // {
        url = reviewed.appImage.pin.url + "?token=bad";
      };
    })
    (alter {
      pin = reviewed.appImage.pin // {
        hash = "missing-hash";
      };
    })
    (alter { assetName = "other.AppImage"; })
    (alter { license = "unfree"; })
  ];
  resolver =
    present:
    lib.evalModules {
      modules = [
        ({ lib, ... }: {
          options = {
            assertions = lib.mkOption {
              type = lib.types.listOf lib.types.attrs;
              default = [ ];
            };
          }
          // lib.optionalAttrs present {
            services = {
              nascentAppImages = {
                enable = lib.mkOption {
                  type = lib.types.bool;
                  default = false;
                };
                apps = lib.mkOption {
                  type = lib.types.attrs;
                  default = { };
                };
              };
            };
          };
        })
        ({ options, ... }: {
          config = import ../appimage-integration.nix {
            inherit lib options;
            apps = [ reviewed ];
          };
        })
      ];
    };
  missing = (resolver false).config;
  configured = (resolver true).config;
in
assert (evaluate reviewed).available;
assert !(evaluate reviewed).packageUnfree;
assert builtins.all (app: !(evaluate app).available) invalid;
assert !(builtins.head missing.assertions).assertion;
assert builtins.all (entry: entry.assertion) configured.assertions;
assert configured.services.nascentAppImages.enable;
assert configured.services.nascentAppImages.apps.${reviewed.id}.displayName == reviewed.name;
assert configured.services.nascentAppImages.apps.${reviewed.id}.pin == reviewed.appImage.pin;
{
  metadata = "passed";
  resolverContract = "passed";
  inherit system;
}
