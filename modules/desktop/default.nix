{
  config,
  lib,
  pkgs,
  options,
  ...
}:
let
  themeEtc = (import ./themes.nix { }).environment.etc;
  # Cumulative history of shipped theme defaults; nascent-theme refreshes only untouched copies.
  shippedDefaults = builtins.readFile ./shipped-defaults.sha256;
  unrecordedDefaults = lib.filter (line: !(lib.hasInfix line shippedDefaults)) (
    lib.mapAttrsToList (
      name: file: "${builtins.hashString "sha256" file.text}  ${lib.removePrefix "nascentos/" name}"
    ) themeEtc
  );
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
              pkgs.util-linux
              pkgs.libnotify
              pkgs.grim
              pkgs.slurp
              pkgs.wl-clipboard
              pkgs.cliphist
              pkgs.brightnessctl
              pkgs.playerctl
              pkgs.wireplumber
              pkgs.xrdb
              pkgs.git
              pkgs.fzf
              pkgs.brotli
              pkgs.rsync
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
  # Theme tools would fight the shipped theme; keep them installed but out of the launcher.
  hiddenApps = lib.hiPrio (
    pkgs.runCommand "nascent-hidden-apps" { } ''
      mkdir -p $out/share/applications
      for id in kvantummanager qt5ct qt6ct nm-connection-editor; do
        printf '[Desktop Entry]\nType=Application\nName=%s\nNoDisplay=true\n' "$id" > $out/share/applications/$id.desktop
      done
    ''
  );
  # Nord on the virtual console, so the greeter and TTYs match the desktop.
  consolePalette = [
    "2e3440"
    "bf616a"
    "a3be8c"
    "ebcb8b"
    "81a1c1"
    "b48ead"
    "88c0d0"
    "e5e9f0"
    "4c566a"
    "bf616a"
    "a3be8c"
    "ebcb8b"
    "81a1c1"
    "b48ead"
    "8fbcbb"
    "eceff4"
  ];
  # tuigreet centres each greeting line; equal-width lines keep the ridge art aligned.
  greeting = pkgs.runCommand "nascent-greeting" { } ''
    awk '{ printf "%-27s\n", $0 }' ${../../assets/branding/terminal-logo.txt} > $out
    printf '\nnascentOS' >> $out
  '';
  greeter = pkgs.writeShellScript "nascent-greeter" ''
    exec ${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session \
      --greeting "$(cat ${greeting})" --time --time-format '%A %d %B  %H:%M' \
      --remember --remember-user-session --asterisks --asterisks-char '•' \
      --window-padding 2 --container-padding 2 --prompt-padding 1 \
      --power-shutdown 'systemctl poweroff' --power-reboot 'systemctl reboot' \
      --theme 'border=blue;text=white;prompt=cyan;time=brightblack;action=brightblack;button=cyan;container=black;input=white;greet=cyan;title=cyan'
  '';
in
{
  config = lib.mkIf config.nascent.desktop.enable {
    console = {
      colors = lib.mkDefault consolePalette;
      # The 8x16 kernel font is unreadably small on HiDPI laptop panels.
      font = lib.mkDefault "ter-v32b";
      packages = [ pkgs.terminus_font ];
      earlySetup = lib.mkDefault true;
    };
    services.greetd.settings.default_session.command = lib.mkDefault "${greeter}";
    assertions = [
      {
        assertion = unrecordedDefaults == [ ];
        message = "Append to modules/desktop/shipped-defaults.sha256 so installed copies can be refreshed:\n${lib.concatLines unrecordedDefaults}";
      }
    ];
    programs.hyprland.enable = true;
    programs.firefox.enable = lib.mkDefault (builtins.elem "firefox" selected);
    environment.variables.EDITOR = lib.mkOverride 900 "nascent-editor";
    environment.variables.VISUAL = lib.mkOverride 900 "nascent-editor";
    environment.sessionVariables.XCURSOR_THEME = lib.mkDefault "Nordic-cursors";
    environment.sessionVariables.XCURSOR_SIZE = lib.mkDefault "24";
    environment.sessionVariables.XKB_DEFAULT_LAYOUT = lib.mkDefault config.services.xserver.xkb.layout;
    environment.sessionVariables.XKB_DEFAULT_VARIANT = lib.mkDefault config.services.xserver.xkb.variant;
    programs.dconf.enable = true;
    programs.dconf.profiles.user.databases = [
      {
        settings."org/gnome/desktop/interface" = {
          gtk-theme = "Nordic";
          icon-theme = "Papirus-Dark";
          color-scheme = "prefer-dark";
          cursor-theme = "Nordic-cursors";
          cursor-size = lib.gvariant.mkInt32 24;
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
      hiddenApps
      session
      commands
      kitty
      fuzzel
      waybar
      mako
      hyprlock
      hypridle
      fastfetch
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
      pkgs.nerd-fonts.jetbrains-mono
    ];
    fonts.fontconfig.defaultFonts.monospace = lib.mkDefault [ "Fira Code" ];
    environment.etc = themeEtc // {
      "nascentos/software-runtime.json".text = builtins.toJSON { inherit browser editor; };
      "xdg/Kvantum/kvantum.kvconfig".text = "[General]\ntheme=Nordic\n";
      "xdg/qt6ct/qt6ct.conf".text = "[Appearance]\nstyle=kvantum\nicon_theme=Papirus-Dark\n";
      "xdg/gtk-3.0/settings.ini".text =
        "[Settings]\ngtk-theme-name=Nordic\ngtk-icon-theme-name=Papirus-Dark\ngtk-cursor-theme-name=Nordic-cursors\ngtk-cursor-theme-size=24\n";
      "xdg/gtk-4.0/settings.ini".text =
        "[Settings]\ngtk-theme-name=Nordic\ngtk-icon-theme-name=Papirus-Dark\ngtk-cursor-theme-name=Nordic-cursors\ngtk-cursor-theme-size=24\n";
      # Users import this stable path, so nixpkgs updates never leave a dangling store import.
      "nascentos/gtk-4.0.css".text = ''
        @import url("${pkgs.nordic}/share/themes/Nordic/gtk-4.0/gtk.css");
        ${builtins.readFile ./gtk4-overrides.css}
      '';
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
      "nascentos/shipped-defaults.sha256".text = shippedDefaults;
      # Dim, lock, then blank the panel when idle; ~/.config/hypr/hypridle.conf overrides it.
      "xdg/fastfetch/config.jsonc".text = builtins.toJSON {
        logo = {
          type = "file";
          source = "/etc/nascentos/branding/terminal-logo.txt";
          color."1" = "cyan";
          padding = {
            top = 2;
            right = 4;
          };
        };
        display = {
          separator = "  ";
          color.keys = "blue";
          key.width = 9;
        };
        modules = [
          {
            type = "title";
            color = {
              user = "cyan";
              host = "cyan";
            };
          }
          "separator"
          {
            type = "os";
            key = "os";
            format = "nascentOS · NixOS {version}";
          }
          {
            type = "kernel";
            key = "kernel";
          }
          {
            type = "wm";
            key = "wm";
          }
          {
            type = "terminal";
            key = "term";
          }
          {
            type = "shell";
            key = "shell";
          }
          {
            type = "packages";
            key = "pkgs";
          }
          {
            type = "memory";
            key = "memory";
          }
          {
            type = "uptime";
            key = "uptime";
          }
          "break"
          {
            type = "colors";
            symbol = "circle";
          }
        ];
      };
      "xdg/hypr/hypridle.conf".text = ''
        general {
          lock_cmd = pidof hyprlock || nascent-launch lock
          before_sleep_cmd = loginctl lock-session
          after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms({ action = "on" })'
        }
        listener {
          timeout = 300
          on-timeout = ${pkgs.brightnessctl}/bin/brightnessctl -s set 10%
          on-resume = ${pkgs.brightnessctl}/bin/brightnessctl -r
        }
        listener {
          timeout = 600
          on-timeout = loginctl lock-session
        }
        listener {
          timeout = 660
          on-timeout = hyprctl dispatch 'hl.dsp.dpms({ action = "off" })'
          on-resume = hyprctl dispatch 'hl.dsp.dpms({ action = "on" })'
        }
      '';

    };
  };
}
