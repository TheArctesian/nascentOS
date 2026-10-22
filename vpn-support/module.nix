{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.vpn;
  selected = cfg.provider != null;
  proton = cfg.provider == "proton";
  manual = cfg.provider == "networkmanager";
  client = {
    mullvad = "${pkgs.mullvad-vpn}/bin/mullvad-vpn";
    proton = "${pkgs.proton-vpn}/bin/protonvpn-app";
    ivpn = "${pkgs.ivpn-ui}/bin/ivpn-ui";
    networkmanager = "${pkgs.networkmanagerapplet}/bin/nm-connection-editor";
  };
  launcher = pkgs.writeShellScriptBin "nascent-vpn" ''
    exec ${client.${if selected then cfg.provider else "networkmanager"}} "$@"
  '';
in
{
  options.nascent.vpn = {
    provider = lib.mkOption {
      type = lib.types.nullOr (
        lib.types.enum [
          "mullvad"
          "proton"
          "ivpn"
          "networkmanager"
        ]
      );
      default = null;
      description = "One VPN client, or null for none. Sign in and connect after installation.";
    };
    configureKeyring = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Enable the shared GNOME Keyring Secret Service and greetd PAM unlock for Proton. Disable only if the session supplies a Secret Service.";
    };
    mullvad = {
      earlyBootBlocking = lib.mkEnableOption "Mullvad early boot blocking (review upstream limitations first)";
      splitTunneling = lib.mkEnableOption "the privileged Mullvad exclusion wrapper";
    };
  };

  config = lib.mkIf selected (
    lib.mkMerge [
      {
        assertions = [
          {
            assertion = config.networking.networkmanager.enable;
            message = "nascent VPN desktop integration requires NetworkManager.";
          }
          {
            assertion = builtins.elem pkgs.stdenv.hostPlatform.system [
              "x86_64-linux"
              "aarch64-linux"
            ];
            message = "nascent VPN supports x86_64-linux and aarch64-linux only.";
          }
          {
            assertion = cfg.provider != "ivpn" || pkgs.stdenv.hostPlatform.system == "x86_64-linux";
            message = "The pinned IVPN GUI supports x86_64-linux only.";
          }
          {
            assertion =
              (config.services.mullvad-vpn.enable == (cfg.provider == "mullvad"))
              && (config.services.ivpn.enable == (cfg.provider == "ivpn"))
              && !config.services.expressvpn.enable;
            message = "nascent VPN selection conflicts with another enabled provider daemon.";
          }
          {
            assertion =
              cfg.provider == "mullvad" || (!cfg.mullvad.earlyBootBlocking && !cfg.mullvad.splitTunneling);
            message = "Mullvad-specific options require the Mullvad provider.";
          }
        ];
        networking.networkmanager.enable = lib.mkDefault true;
        security.polkit.enable = true;
        environment.etc."nascentos/vpn.json".text = builtins.toJSON {
          provider = cfg.provider;
          command = "nascent-vpn";
          statusSource = "Selected client; network reachability alone does not verify VPN protection.";
        };
        environment.systemPackages = [
          launcher
          pkgs.networkmanagerapplet
          (pkgs.makeDesktopItem {
            name = "nascent-vpn";
            desktopName = "VPN connection";
            comment = "Open the selected VPN client for status and connection settings";
            exec = "nascent-vpn";
            icon = "network-vpn";
            categories = [ "Network" ];
          })
        ];
      }
      (lib.mkIf (cfg.provider == "mullvad") {
        services.mullvad-vpn = {
          enable = true;
          package = pkgs.mullvad-vpn;
          enableExcludeWrapper = cfg.mullvad.splitTunneling;
          enableEarlyBootBlocking = cfg.mullvad.earlyBootBlocking;
        };
      })
      (lib.mkIf proton {
        environment.systemPackages = [ pkgs.proton-vpn ];
        networking.networkmanager.plugins = [ pkgs.networkmanager-openvpn ];
        services.gnome.gnome-keyring.enable = lib.mkIf cfg.configureKeyring (lib.mkDefault true);
        security.pam.services.greetd.enableGnomeKeyring = lib.mkIf cfg.configureKeyring (
          lib.mkDefault true
        );
      })
      (lib.mkIf (cfg.provider == "ivpn") {
        services.ivpn.enable = true;
        environment.systemPackages = [ pkgs.ivpn-ui ];
      })
      (lib.mkIf manual {
        networking.networkmanager.plugins = [ pkgs.networkmanager-openvpn ];
      })
    ]
  );
}
