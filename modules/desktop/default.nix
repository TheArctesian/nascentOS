{
  config,
  lib,
  pkgs,
  options,
  ...
}:
let
  software =
    lib.hasAttrByPath [ "nascent" "software" "enable" ] options && config.nascent.software.enable;
  selected =
    if software then
      config.nascent.software.selected
    else
      [
        "firefox"
        "neovim"
      ];
  browser =
    if builtins.elem "firefox" selected then
      "firefox"
    else if builtins.elem "chromium" selected then
      "chromium"
    else
      null;
  editor = lib.findFirst (id: builtins.elem id selected) null [
    "neovim"
    "zed"
    "vscodium"
    "cursor"
  ];
  commands = pkgs.stdenvNoCC.mkDerivation {
    pname = "nascent-commands";
    version = "0.1.0";
    src = ../../bin;
    nativeBuildInputs = [ pkgs.makeWrapper ];
    installPhase = ''
      mkdir -p $out/bin
      cp nascent* $out/bin/
      patchShebangs $out/bin
      for command in $out/bin/*; do
        wrapProgram "$command" --prefix PATH : ${
          lib.makeBinPath (
            [
              pkgs.coreutils
              pkgs.gawk
              pkgs.procps
              pkgs.kitty
              pkgs.fuzzel
              pkgs.waybar
              pkgs.mako
              config.programs.hyprland.package
              pkgs.hyprlock
              pkgs.swaybg
              pkgs.python3
              pkgs.xdg-utils
              pkgs.gtk3
              pkgs.curl
              pkgs.systemd
              pkgs.zenity
            ]
            ++ lib.optional config.programs.firefox.enable config.programs.firefox.finalPackage
          )
        }:$out/bin
      done
    '';
  };
  session = pkgs.writeShellApplication {
    name = "nascent-session";
    runtimeInputs = [
      config.programs.hyprland.package
      pkgs.dbus
      commands
    ];
    text = ''
      export XDG_CURRENT_DESKTOP=Hyprland
      export XDG_SESSION_TYPE=wayland
      if [[ -z ''${XDG_RUNTIME_DIR:-} || ! -S $XDG_RUNTIME_DIR/bus ]]; then
        echo 'The login session bus is unavailable. Log in again before starting the desktop.' >&2
        exit 1
      fi
      export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
      nascent-theme init
      nascent-editor init
      nascent-agent init
      trap '
        systemctl --user stop nascent-session.target graphical-session.target nascent-wallpaper.service
        systemctl --user unset-environment WAYLAND_DISPLAY DISPLAY HYPRLAND_INSTANCE_SIGNATURE
      ' EXIT
      status=0
      start-hyprland -- --config /etc/nascentos/hyprland.lua || status=$?
      exit "$status"
    '';
  };
in
{
  config = lib.mkIf config.nascent.desktop.enable {
    programs.hyprland.enable = true;
    programs.firefox.enable = lib.mkDefault (builtins.elem "firefox" selected);
    environment.variables.EDITOR = lib.mkOverride 900 "nascent-editor";
    environment.variables.VISUAL = lib.mkOverride 900 "nascent-editor";
    environment.sessionVariables.XKB_DEFAULT_LAYOUT = lib.mkDefault config.services.xserver.xkb.layout;
    environment.sessionVariables.XKB_DEFAULT_VARIANT = lib.mkDefault config.services.xserver.xkb.variant;
    programs.dconf.enable = true;
    programs.dconf.profiles.user.databases = [
      {
        settings."org/gnome/desktop/interface" = {
          gtk-theme = "Nordic";
          icon-theme = "Papirus-Dark";
          color-scheme = "prefer-dark";
        };
      }
    ];
    qt = {
      enable = true;
      platformTheme = "qt5ct";
      style = "kvantum";
    };
    security.polkit.enable = true;
    security.pam.services.hyprlock = { };
    xdg.portal.extraPortals = [ pkgs.xdg-desktop-portal-gtk ];
    xdg.portal.config.hyprland = {
      default = [
        "hyprland"
        "gtk"
      ];
      "org.freedesktop.impl.portal.FileChooser" = [ "gtk" ];
    };

    environment.systemPackages = with pkgs; [
      session
      commands
      kitty
      fuzzel
      waybar
      mako
      hyprlock
      wl-clipboard
      pavucontrol
      networkmanagerapplet
      polkit_gnome
      papirus-icon-theme
      nordic
      glib.bin
    ];
    systemd.user.services.nascent-wallpaper = {
      description = "nascentOS selected wallpaper";
      partOf = [ "graphical-session.target" ];
      serviceConfig.ExecStart = "${commands}/bin/nascent-wallpaper run";
    };
    systemd.user.targets.nascent-session = {
      description = "nascentOS graphical session";
      bindsTo = [ "graphical-session.target" ];
      wants = [ "graphical-session-pre.target" ];
      after = [ "graphical-session-pre.target" ];
    };
    fonts.packages = [
      pkgs.fira-code
      pkgs.font-awesome
    ];
    fonts.fontconfig.defaultFonts.monospace = lib.mkDefault [ "Fira Code" ];
    environment.etc = (import ./themes.nix { }).environment.etc // {
      "nascentos/software-runtime.json".text = builtins.toJSON { inherit browser editor; };
      "xdg/Kvantum/kvantum.kvconfig".text = "[General]\ntheme=Nordic\n";
      "xdg/qt6ct/qt6ct.conf".text = "[Appearance]\nstyle=kvantum\nicon_theme=Papirus-Dark\n";
      "xdg/gtk-3.0/settings.ini".text =
        "[Settings]\ngtk-theme-name=Nordic\ngtk-icon-theme-name=Papirus-Dark\n";
      "xdg/gtk-4.0/settings.ini".text =
        "[Settings]\ngtk-theme-name=Nordic\ngtk-icon-theme-name=Papirus-Dark\n";
      "nascentos/gtk-4.0.css".text =
        ''@import url("${pkgs.nordic}/share/themes/Nordic/gtk-4.0/gtk.css");'';
      "nascentos/branding".source = ../../assets/branding;
      "nascentos/wallpapers".source = ../../assets/wallpapers;
      "nascentos/hardware.py".source = ../../lib/hardware.py;
      "nascentos/desktop_intent.py".source = ../../lib/desktop_intent.py;
      "nascentos/nvim".source = ../../assets/nvim;
      "nascentos/agents/skills".source = ../../agents/skills;
      "nascentos/hyprland.lua".text =
        lib.replaceStrings
          [ "/run/current-system/sw/libexec/polkit-gnome-authentication-agent-1" ]
          [ "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1" ]
          (builtins.readFile ./hyprland.lua);
      "nascentos/waybar.json".text = builtins.toJSON {
        layer = "top";
        position = "top";
        height = 36;
        margin-top = 10;
        margin-left = 12;
        margin-right = 12;
        spacing = 4;
        modules-left = [
          "custom/menu"
          "hyprland/workspaces"
        ];
        modules-center = [ "clock" ];
        modules-right = [
          "custom/install"
          "network"
          "pulseaudio"
          "tray"
        ];
        clock.format = "{:%a %d %b  %H:%M}";
        "custom/menu" = {
          format = "nascentOS";
          tooltip-format = "Open menu · Super+Space\nApplications · Super+D\nTerminal · Super+Return";
          on-click = "nascent menu";
        };
        "custom/install" = {
          exec = ''if command -v nascent-install >/dev/null 2>&1; then printf '%s\n' '{"text":"Install nascentOS","tooltip":"Open installer · Super+I"}'; else printf '%s\n' '{"text":""}'; fi'';
          return-type = "json";
          interval = "once";
          on-click = "nascent-install";
        };
      };

    };
  };
}
