{ nixpkgs, system }:
let
  lib = import (nixpkgs + "/lib");
  pkgs = import nixpkgs { inherit system; };
  catalog = builtins.fromJSON (builtins.readFile ../catalog.json);
  manifest = import ../availability.nix { inherit pkgs; };
  synthetic = import ../availability.nix {
    pkgs = pkgs // {
      nascentBroken = pkgs.hello // {
        meta = pkgs.hello.meta // {
          broken = true;
        };
      };
      nascentWrongArch = pkgs.hello // {
        meta = pkgs.hello.meta // {
          platforms = [ "riscv64-linux" ];
        };
      };
      nascentMislabeled = pkgs.hello // {
        meta = pkgs.hello.meta // {
          license = lib.licenses.unfree;
        };
      };
    };
    catalog.apps =
      map
        (package: {
          id = package;
          inherit package;
          kind = "package";
          platforms = [ system ];
          proprietary = false;
        })
        [
          "nascentBroken"
          "nascentWrongArch"
          "nascentMislabeled"
          "nascentMissing"
        ];
  };
  app = id: lib.findFirst (entry: entry.id == id) null manifest.apps;
  unsupportedBackend = import ../availability.nix {
    inherit pkgs;
    catalog.apps = [
      {
        id = "external-appimage";
        kind = "package";
        package = "hello";
        backend = "appimage";
        proprietary = false;
        platforms = [ system ];
      }
    ];
  };
  evaluate =
    selected:
    (import (nixpkgs + "/nixos/lib/eval-config.nix") {
      inherit system;
      modules = [
        ../default.nix
        {
          nascent.software = {
            enable = true;
            inherit selected;
          };
          system.stateVersion = "26.05";
        }
      ];
    }).config;
  ownAssertions =
    config:
    lib.filter (
      entry:
      lib.hasPrefix "nascent.software" entry.message
      || lib.hasPrefix "Unknown nascent software" entry.message
      || lib.hasPrefix "Cannot select " entry.message
      || lib.hasPrefix "Selected AppImages " entry.message
    ) (lib.filter (entry: !entry.assertion) config.assertions);
  valid = selected: builtins.all (entry: entry.assertion) (ownAssertions (evaluate selected));
  selected = evaluate [
    "neovim"
    "cursor"
  ];
  allowsUnfree =
    package: builtins.elem (lib.getName package) selected.nixpkgs.config.allowUnfreePackages;
  fontProfile = evaluate [
    "fira-code"
    "font-awesome"
    "open-dyslexic"
  ];
  fontPackageNames = map lib.getName fontProfile.fonts.packages;
  appPackageNames = map lib.getName fontProfile.environment.systemPackages;
in
assert valid [
  "neovim"
  "firefox"
];
assert valid [ ];
assert valid [ "cursor" ];
assert !(valid [ "chatgpt-web" ]);
assert !(valid [ "unknown-app" ]);
assert
  !(valid [
    "neovim"
    "neovim"
  ]);
assert !(valid [ "unity" ]);
assert (if system == "aarch64-linux" then !(valid [ "slack" ]) else valid [ "slack" ]);
assert allowsUnfree pkgs.code-cursor;
assert !(allowsUnfree pkgs.slack);
assert (app "cursor").packageUnfree;
assert !(app "neovim").packageUnfree;
assert !(app "unity").available;
assert builtins.all (entry: !entry.available || entry.kind == "package") manifest.apps;
assert builtins.all (entry: !entry.available && entry.reason != null) synthetic.apps;
assert !(builtins.head unsupportedBackend.apps).available;
assert valid [
  "fira-code"
  "font-awesome"
  "open-dyslexic"
];
assert builtins.all (name: builtins.elem name fontPackageNames) [
  "fira-code"
  "font-awesome"
  "open-dyslexic"
];
assert builtins.all (name: !(builtins.elem name appPackageNames)) [
  "fira-code"
  "font-awesome"
  "open-dyslexic"
];
assert fontProfile.fonts.fontconfig.defaultFonts.monospace == [ "Fira Code" ];
assert fontProfile.fonts.fontconfig.defaultFonts.sansSerif == [ "OpenDyslexic" ];
assert !builtins.elem "OpenDyslexic" fontProfile.fonts.fontconfig.defaultFonts.monospace;
{
  inherit system;
  defaults = map (entry: entry.id) (lib.filter (entry: entry.default) catalog.apps);
  available = map (entry: entry.id) (lib.filter (entry: entry.available) manifest.apps);
  unavailable = map (entry: { inherit (entry) id reason; }) (
    lib.filter (entry: !entry.available) manifest.apps
  );
  selectedPackageNames = map lib.getName (lib.take 2 selected.environment.systemPackages);
  selectedNativeDrvs = map (package: package.drvPath) (
    lib.take 2 selected.environment.systemPackages
  );
  pickerDrv = (import ../package.nix { inherit pkgs; }).drvPath;
  selectedFonts = lib.filter (
    name:
    builtins.elem name [
      "fira-code"
      "font-awesome"
      "open-dyslexic"
    ]
  ) fontPackageNames;
}
