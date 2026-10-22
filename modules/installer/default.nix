{
  lib,
  pkgs,
  modulesPath,
  nascentSource,
  ...
}:
let
  installerDesign = import ../../installer-design/integration.nix { inherit pkgs; };
  software = import ../../installer/software-selection/package.nix { inherit pkgs; };
  baseExtensions = pkgs.calamares-nixos-extensions.overrideAttrs (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.python3 ];
    postPatch =
      (old.postPatch or "")
      + ''
        python3 ${./patch-extension.py} .
        cp ${../../lib}/hardware.py modules/nixos/hardware.py
        cp ${../../lib}/install_target.py modules/nixos/nascent_install.py
        mkdir -p branding/nascent
        cp ${../../assets/branding}/main-logo.png branding/nascent/main-logo.png
        cp ${./branding.json} branding/nascent/branding.desc
        substituteInPlace config/settings.conf \
          --replace-fail 'branding: nixos' 'branding: nascent' \
          --replace-fail 'prompt-install: false' 'prompt-install: true' \
          --replace-fail '  - notesqml@unfree' '  # NVIDIA license choice is explicit in the hardware preflight'
        cat > config/modules/packagechooser.conf <<'CONFIG'
        mode: required
        method: legacy
        labels:
          step: Desktop
        default: nascent
        items:
          - id: nascent
            packages: [nascent]
            name: nascentOS
            description: "Nord Hyprland desktop, writable LazyVim, agent tools and optional local inference."
        CONFIG
      ''
      + installerDesign.extensionPostPatch;
  });
  extensions = import ../../installer/software-selection/extension.nix {
    inherit pkgs;
    extensions = baseExtensions;
  };
  installer =
    (pkgs.calamares-nixos.override {
      calamares-nixos-extensions = extensions;
    }).overrideAttrs
      (old: {
        inherit (installerDesign.installerAttrs old) nativeBuildInputs postPatch;
        qtWrapperArgs = (old.qtWrapperArgs or [ ]) ++ [
          "--set QT_QPA_PLATFORM xcb"
          "--set QT_STYLE_OVERRIDE kvantum"
          "--set QT_QPA_PLATFORMTHEME qt5ct"
          "--prefix XDG_CONFIG_DIRS : /etc/xdg"
          "--prefix XDG_DATA_DIRS : ${pkgs.nordic}/share"
          "--prefix QT_PLUGIN_PATH : ${pkgs.qt6Packages.qtstyleplugin-kvantum}/${pkgs.qt6Packages.qtbase.qtPluginPrefix}:${pkgs.qt6Packages.qt6ct}/${pkgs.qt6Packages.qtbase.qtPluginPrefix}"
        ];
        postInstall = (old.postInstall or "") + ''
          # Every visible installer entry goes through hardware review first.
          find $out/share/applications -name '*.desktop' -exec sed -i \
            -e 's|^Exec=.*|Exec=nascent-install|' \
            -e 's|^TryExec=.*|TryExec=nascent-install|' \
            -e 's|^Name=.*|Name=Install nascentOS|' \
            -e 's|^Icon=.*|Icon=/etc/nascentos/branding/main-logo.png|' {} +
        '';
      });
  launch = pkgs.writeShellApplication {
    name = "nascent-install";
    runtimeInputs = [
      pkgs.zenity
      pkgs.python3
      pkgs.coreutils
      pkgs.hyprland
      pkgs.xhost
      software
    ];
    text = ''
      exec ${pkgs.python3}/bin/python3 ${../../lib}/install_launcher.py \
        --installer ${installer}/bin/calamares \
        --record-helper ${../../lib}/install_target.py \
        --software-picker ${software}/bin/nascent-software-picker \
        --software-recorder ${software}/bin/nascent-software-record
    '';
  };
in
{
  imports = [ (modulesPath + "/installer/cd-dvd/installation-cd-graphical-base.nix") ];
  nascent.desktop.enable = true;
  programs.partition-manager.enable = true;
  i18n.supportedLocales = [ "all" ];
  environment.systemPackages = [
    installer
    extensions
    launch
    pkgs.glibcLocales
  ];
  environment.etc."nascentos-source".source = nascentSource;
  environment.etc."nascentos/live-installer".text = "Install nascentOS\n";
  # Live-only access and autologin come from the upstream installation-device
  # module. They are never imported by the installed target's configuration.
  services.openssh.enable = lib.mkForce false;
  services.greetd = {
    enable = true;
    settings = {
      initial_session = {
        command = "nascent-session";
        user = "nixos";
      };
      default_session.command = "${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session";
    };
  };
  isoImage.edition = "nascent-graphical";
  isoImage.volumeID = "NASCENTOS_${pkgs.stdenv.hostPlatform.qemuArch}";
}
