{ nixpkgs }:
let
  lib = nixpkgs.lib;
  catalog = builtins.fromJSON (builtins.readFile ../catalog.json);
  mk =
    system: extra:
    (lib.nixosSystem {
      inherit system;
      modules = [
        ../module.nix
        {
          system.stateVersion = "26.05";
          boot.loader.grub.enable = false;
          fileSystems."/" = {
            device = "/dev/test";
            fsType = "ext4";
          };
        }
        extra
      ];
    }).config;
  valid = cfg: builtins.all (a: a.assertion) cfg.assertions;
  mkEnabled = system: extra: mk system ({ nascent.passwords.enable = true; } // extra);
  checksFor =
    system:
    let
      disabled = mk system { };
      defaults = mkEnabled system { };
      autostart = mk system {
        nascent.passwords = {
          enable = true;
          manager = "keepassxc";
          desktop.autostart = true;
        };
      };
      browser = mk system {
        nascent.passwords = {
          enable = true;
          firefox.enable = true;
        };
      };
      cli = mk system {
        nascent.passwords = {
          enable = true;
          protonCli = {
            enable = true;
            persistentKeyring = true;
          };
        };
      };
      keepass = mk system {
        nascent.passwords = {
          enable = true;
          manager = "keepassxc";
          firefox.enable = true;
        };
      };
      bitwarden = mk system {
        nascent.passwords = {
          enable = true;
          manager = "bitwarden";
        };
      };
      noVault = mk system {
        nascent.passwords = {
          enable = true;
          manager = "none";
        };
      };
      conflicting = mk system {
        nascent.passwords.enable = true;
        services.passSecretService.enable = true;
      };
      kwallet = mk system {
        nascent.passwords.enable = true;
        security.pam.services.greetd.kwallet.enable = true;
      };
      invalidCli = mk system {
        nascent.passwords = {
          enable = true;
          protonCli.persistentKeyring = true;
        };
      };
      external = mk system {
        nascent.passwords = {
          enable = true;
          manager = "keepassxc";
          keyring = "external";
        };
      };
      adapter =
        selection:
        mk system {
          imports = [ ../catalog-adapter.nix ];
          options.nascent.software = {
            enable = lib.mkOption {
              type = lib.types.bool;
              default = true;
            };
            selected = lib.mkOption {
              type = lib.types.listOf lib.types.str;
              default = selection;
            };
          };
        };
    in
    assert valid disabled;
    assert !disabled.services.gnome.gnome-keyring.enable;
    assert valid defaults;
    assert defaults.nascent.passwords.manager == "proton-pass";
    assert defaults.nascent.passwords.desktop.enable == (system == "x86_64-linux");
    assert defaults.services.gnome.gnome-keyring.enable;
    assert defaults.security.pam.services.greetd.enableGnomeKeyring;
    assert defaults.security.pam.services.hyprlock.enableGnomeKeyring;
    assert defaults.security.pam.services.passwd.enableGnomeKeyring;
    assert valid autostart;
    assert
      autostart.systemd.user.services.nascent-password-manager.wantedBy == [ "graphical-session.target" ];
    assert !(builtins.hasAttr "nascent-password-manager" defaults.systemd.user.services);
    assert builtins.all (
      app:
      let
        pkg = nixpkgs.legacyPackages.${system}.${app.package};
      in
      app.version == pkg.version
      &&
        (builtins.elem system app.platforms)
        == lib.meta.availableOn nixpkgs.legacyPackages.${system}.stdenv.hostPlatform pkg
    ) catalog.apps;
    assert lib.hasInfix "pam_gnome_keyring.so" defaults.security.pam.services.greetd.text;
    assert !(builtins.hasAttr "SSH_AUTH_SOCK" defaults.environment.sessionVariables);
    assert !(builtins.hasAttr "PROTON_PASS_KEY_PROVIDER" defaults.environment.sessionVariables);
    assert valid browser;
    assert !browser.programs.firefox.policies.OfferToSaveLoginsDefault;
    assert
      browser.programs.firefox.policies.ExtensionSettings."78272b6fa58f4a1abaac99321d503a20@proton.me".installation_mode
      == "normal_installed";
    assert valid cli;
    assert cli.environment.sessionVariables.PROTON_PASS_LINUX_KEYRING == "dbus";
    assert valid keepass && keepass.nascent.passwords.desktop.enable;
    assert builtins.length keepass.programs.firefox.nativeMessagingHosts.packages == 1;
    assert valid bitwarden && bitwarden.nascent.passwords.desktop.enable;
    assert valid noVault && noVault.services.gnome.gnome-keyring.enable;
    assert !noVault.nascent.passwords.desktop.enable;
    assert !valid conflicting;
    assert !valid kwallet;
    assert !valid invalidCli;
    assert valid external && !external.services.gnome.gnome-keyring.enable;
    assert valid (adapter [ "keepassxc" ]);
    assert (adapter [ "keepassxc" ]).nascent.passwords.manager == "keepassxc";
    assert (adapter [ ]).nascent.passwords.manager == "none";
    assert
      !valid (adapter [
        "proton-pass"
        "keepassxc"
      ]);
    assert
      system != "aarch64-linux"
      || !valid (
        mk system {
          nascent.passwords = {
            enable = true;
            desktop.enable = true;
          };
        }
      );
    {
      passed = true;
      packages = lib.genAttrs [ "proton-pass" "proton-pass-cli" "keepassxc" "bitwarden-desktop" ] (
        name:
        let
          pkg = nixpkgs.legacyPackages.${system}.${name};
        in
        {
          inherit (pkg) version;
          available = lib.meta.availableOn nixpkgs.legacyPackages.${system}.stdenv.hostPlatform pkg;
        }
      );
    };
in
lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] checksFor
