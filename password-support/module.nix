{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.passwords;
  catalog = builtins.fromJSON (builtins.readFile ./catalog.json);
  selected = lib.findFirst (app: app.id == cfg.manager) null catalog.apps;
  package = if selected == null then null else pkgs.${selected.package};
  available = package != null && lib.meta.availableOn pkgs.stdenv.hostPlatform package;
  gnome = cfg.keyring == "gnome";
in
{
  options.nascent.passwords = {
    enable = lib.mkEnableOption "password manager and session credential support";
    manager = lib.mkOption {
      type = lib.types.enum [
        "proton-pass"
        "keepassxc"
        "bitwarden"
        "none"
      ];
      default = "proton-pass";
      description = "Preferred personal vault; independent of the session Secret Service.";
    };
    desktop.enable = lib.mkOption {
      type = lib.types.bool;
      default = available;
      description = "Install the selected native desktop app when supported by pinned nixpkgs.";
    };
    desktop.autostart = lib.mkEnableOption "vault app startup with graphical-session.target";
    firefox.enable = lib.mkEnableOption "the selected manager's user-disableable Firefox extension policy";
    keyring = lib.mkOption {
      type = lib.types.enum [
        "gnome"
        "external"
        "none"
      ];
      default = "gnome";
      description = "GNOME Keyring, an independently configured single provider, or no Secret Service.";
    };
    pamServices = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [
        "greetd"
        "login"
        "hyprlock"
        "passwd"
      ];
      description = "PAM services receiving GNOME Keyring unlock/password-change integration.";
    };
    protonCli.enable = lib.mkEnableOption "the separately authenticated Proton Pass CLI";
    protonCli.persistentKeyring = lib.mkEnableOption "CLI session-key storage in D-Bus Secret Service";
  };

  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      {
        assertions = [
          {
            assertion = !cfg.desktop.enable || available;
            message = "Selected password desktop app is unavailable on this platform. Use the browser extension or choose another manager.";
          }
          {
            assertion = !cfg.desktop.autostart || cfg.desktop.enable;
            message = "Password desktop autostart requires desktop.enable.";
          }
          {
            assertion = !cfg.firefox.enable || selected != null;
            message = "Password Firefox integration requires a selected manager.";
          }
          {
            assertion = !cfg.protonCli.enable || cfg.manager == "proton-pass";
            message = "Proton CLI requires manager = proton-pass.";
          }
          {
            assertion = !cfg.protonCli.persistentKeyring || (cfg.protonCli.enable && gnome);
            message = "Persistent Proton CLI storage requires the CLI and the managed GNOME Keyring.";
          }
          {
            assertion = !(gnome && config.services.passSecretService.enable);
            message = "Choose one Secret Service provider; passSecretService conflicts with GNOME Keyring.";
          }
          {
            assertion =
              !(
                gnome && builtins.any (pam: pam.kwallet.enable) (builtins.attrValues config.security.pam.services)
              );
            message = "Disable KWallet PAM integration before selecting GNOME Keyring.";
          }
          {
            assertion = gnome || !config.services.gnome.gnome-keyring.enable;
            message = "Disable GNOME Keyring when selecting external/none; do not run competing providers.";
          }
        ];
        services.gnome.gnome-keyring.enable = lib.mkIf gnome true;
        security.pam.services = lib.mkIf gnome (
          lib.genAttrs cfg.pamServices (_: {
            enableGnomeKeyring = true;
          })
        );
        environment.systemPackages =
          lib.optional (cfg.desktop.enable && available) package
          ++ lib.optional cfg.protonCli.enable pkgs.proton-pass-cli;
        environment.etc."nascentos/password-support.json".text = builtins.toJSON {
          manager = cfg.manager;
          keyring = cfg.keyring;
          desktop = cfg.desktop.enable;
          firefox = cfg.firefox.enable;
          # Public capability/configuration metadata only. Never store vault data here.
          protonDesktopSshAgent = false;
        };
      }
      (lib.mkIf (cfg.firefox.enable && selected != null) {
        programs.firefox = {
          enable = true;
          policies.OfferToSaveLoginsDefault = lib.mkDefault false;
          policies.ExtensionSettings.${selected.firefoxId} = {
            installation_mode = "normal_installed";
            install_url = "https://addons.mozilla.org/firefox/downloads/latest/${selected.firefoxSlug}/latest.xpi";
          };
          nativeMessagingHosts.packages = lib.optional (cfg.manager == "keepassxc") pkgs.keepassxc;
        };
      })
      (lib.mkIf (cfg.desktop.autostart && available) {
        systemd.user.services.nascent-password-manager = {
          description = "Preferred password vault";
          wantedBy = [ "graphical-session.target" ];
          partOf = [ "graphical-session.target" ];
          after = [ "graphical-session-pre.target" ];
          serviceConfig.ExecStart = lib.getExe package;
        };
      })
      (lib.mkIf cfg.protonCli.persistentKeyring {
        environment.sessionVariables = {
          PROTON_PASS_KEY_PROVIDER = "keyring";
          PROTON_PASS_LINUX_KEYRING = "dbus";
        };
      })
    ]
  );
}
