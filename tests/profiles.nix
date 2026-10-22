{
  nixpkgs,
  nascentModule,
  system,
}:
let
  lib = nixpkgs.lib;
  mkProfile =
    extra:
    nixpkgs.lib.nixosSystem {
      inherit system;
      modules = [
        nascentModule
        ({ modulesPath, ... }: {
          imports = [ (modulesPath + "/virtualisation/qemu-vm.nix") ];
          nascent.desktop.enable = true;
          system.stateVersion = "26.05";
        })
      ]
      ++ extra;
    };
  generic = mkProfile [ ];
  cpu = mkProfile [
    {
      nascent.localAI.enable = true;
      nascent.apps.enable = system == "x86_64-linux";
    }
  ];
  graphics = mkProfile [
    {
      nascent.apps.desktop.enable = true;
      nascent.apps.unfree.enable = true;
    }
  ];
  nvidia = mkProfile [
    ../modules/hardware/nvidia.nix
    {
      nascent.localAI.enable = true;
      nascent.localAI.backend = "cuda";
    }
  ];
  defaults = mkProfile [ { nascent.software.enable = true; } ];
  empty = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [ ];
      };
    }
  ];
  combined = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [
          "chromium"
          "zed"
          "thunderbird"
          "protonmail-bridge"
        ];
      };
      nascent.vpn.provider = "proton";
      nascent.vpn.configureKeyring = false;
    }
  ];
  firefoxNative = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [
          "firefox"
          "neovim"
        ];
      };
      nascent.passwords = {
        manager = "keepassxc";
        firefox.enable = true;
      };
    }
  ];
  freeGaming = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [ ];
      };
      nascent.gaming.enable = true;
    }
  ];
  steam = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [ "obsidian" ];
      };
      nascent.gaming = {
        enable = true;
        steam.enable = true;
        steam.gamescopeSession.enable = true;
      };
    }
  ];
  proprietary = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [ "obsidian" ];
      };
    }
  ];
  interfaceFont = mkProfile [
    {
      nascent.software = {
        enable = true;
        selected = [ "open-dyslexic" ];
      };
    }
  ];
  valid = profile: builtins.all (item: item.assertion) profile.config.assertions;
  names = profile: map lib.getName profile.config.environment.systemPackages;
  runtime =
    profile: builtins.fromJSON profile.config.environment.etc."nascentos/software-runtime.json".text;
  allowed = profile: profile.config.nixpkgs.config.allowUnfreePackages or [ ];
  firefoxPaths =
    profile:
    lib.unique (
      map toString (
        builtins.filter (
          package: lib.getName package == "firefox"
        ) profile.config.environment.systemPackages
      )
    );
  commands = lib.findFirst (
    package: lib.getName package == "nascent-commands"
  ) null firefoxNative.config.environment.systemPackages;
  evaluated = [
    generic
    cpu
    defaults
    empty
    combined
    firefoxNative
    freeGaming
    proprietary
    interfaceFont
  ]
  ++ nixpkgs.lib.optionals (system == "x86_64-linux") [
    graphics
    nvidia
    steam
  ];
  configPaths = map (
    profile: builtins.unsafeDiscardStringContext profile.config.system.build.toplevel.drvPath
  ) evaluated;
in
assert !generic.config.services.ollama.enable;
assert cpu.config.services.ollama.host == "127.0.0.1";
assert !cpu.config.services.ollama.openFirewall;
assert cpu.config.services.ollama.loadModels == [ ];
assert system != "x86_64-linux" || nvidia.config.hardware.nvidia.open;
assert builtins.all valid evaluated;
assert builtins.all (id: builtins.elem id defaults.config.nascent.software.selected) [
  "firefox"
  "neovim"
  "fira-code"
  "font-awesome"
];
assert defaults.config.programs.firefox.enable;
assert
  runtime defaults == {
    browser = "firefox";
    editor = "neovim";
  };
assert lib.unique defaults.config.fonts.fontconfig.defaultFonts.monospace == [ "Fira Code" ];
assert builtins.all (name: builtins.elem name (map lib.getName defaults.config.fonts.packages)) [
  "fira-code"
  "font-awesome"
];
assert !empty.config.programs.firefox.enable;
assert
  runtime empty == {
    browser = null;
    editor = null;
  };
assert builtins.all (name: !(builtins.elem name (names empty))) [
  "firefox"
  "chromium"
  "neovim"
  "zed-editor"
];
assert
  runtime combined == {
    browser = "chromium";
    editor = "zed";
  };
assert !combined.config.programs.firefox.enable;
assert builtins.all (name: builtins.elem name (names combined)) [
  "chromium"
  "zed-editor"
  "thunderbird"
];
assert builtins.all
  (
    package: builtins.elem (toString package) (map toString combined.config.environment.systemPackages)
  )
  [
    combined.pkgs.protonmail-bridge-gui
    combined.pkgs.proton-vpn
  ];
assert combined.config.nascent.mail.clients == [ "thunderbird" ];
assert combined.config.nascent.mail.bridge.enable;
assert combined.config.nascent.passwords.keyring == "gnome";
assert combined.config.services.gnome.gnome-keyring.enable;
assert combined.config.security.pam.services.greetd.enableGnomeKeyring;
assert combined.config.security.pam.services.hyprlock.enableGnomeKeyring;
assert !combined.config.services.passSecretService.enable;
assert builtins.all (pam: !pam.kwallet.enable) (
  builtins.attrValues combined.config.security.pam.services
);
assert
  builtins.length (
    lib.unique (
      map toString (
        builtins.filter (
          package: lib.getName package == "gnome-keyring"
        ) combined.config.services.dbus.packages
      )
    )
  ) == 1;
assert !combined.config.services.mullvad-vpn.enable && !combined.config.services.ivpn.enable;
assert combined.config.networking.networkmanager.enable;
assert !combined.config.systemd.user.services ? nascent-password-manager;
assert firefoxNative.config.programs.firefox.nativeMessagingHosts.packages != [ ];
assert
  firefoxPaths firefoxNative == [ (toString firefoxNative.config.programs.firefox.finalPackage) ];
assert
  toString firefoxNative.config.programs.firefox.finalPackage != toString firefoxNative.pkgs.firefox;
assert lib.hasInfix
  (builtins.unsafeDiscardStringContext "${firefoxNative.config.programs.firefox.finalPackage}/bin")
  (builtins.unsafeDiscardStringContext commands.installPhase);
assert freeGaming.config.programs.gamemode.enable && freeGaming.config.programs.gamescope.enable;
assert !freeGaming.config.programs.steam.enable;
assert allowed freeGaming == [ ];
assert !(freeGaming.config.nixpkgs.config.allowUnfree or false);
assert system != "aarch64-linux" || (!valid steam && !steam.config.programs.steam.enable);
assert
  system != "x86_64-linux"
  || (
    steam.config.programs.steam.enable
    && steam.config.programs.steam.gamescopeSession.enable
    && steam.config.hardware.graphics.enable32Bit
  );
assert
  system != "x86_64-linux"
  || builtins.all (name: builtins.elem name (allowed steam)) [
    "steam"
    "steam-unwrapped"
    "obsidian"
  ];
assert system != "x86_64-linux" || !(steam.config.nixpkgs.config.allowUnfree or false);
assert !(proprietary.config.nixpkgs.config.allowUnfree or false);
assert allowed proprietary == [ "obsidian" ];
assert builtins.elem "obsidian" (names proprietary);
assert interfaceFont.config.fonts.fontconfig.defaultFonts.sansSerif == [ "OpenDyslexic" ];
assert interfaceFont.config.fonts.fontconfig.defaultFonts.monospace == [ "Fira Code" ];
builtins.deepSeq configPaths (
  nixpkgs.legacyPackages.${system}.runCommand "nascent-profile-evaluation" { } ''
    printf '%s\n' ${nixpkgs.lib.escapeShellArgs configPaths} > $out
  ''
)
