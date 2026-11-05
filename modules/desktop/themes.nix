{ ... }:
let
  palettes = {
    nord = {
      background = "2e3440";
      surface = "3b4252";
      foreground = "eceff4";
      muted = "4c566a";
      accent = "88c0d0";
      orange = "d08770";
      colors = [
        "3b4252"
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
    };
    tokyo-night = {
      background = "1a1b26";
      surface = "24283b";
      foreground = "c0caf5";
      muted = "414868";
      accent = "7aa2f7";
      orange = "ff9e64";
      colors = [
        "15161e"
        "f7768e"
        "9ece6a"
        "e0af68"
        "7aa2f7"
        "bb9af7"
        "7dcfff"
        "a9b1d6"
        "414868"
        "f7768e"
        "9ece6a"
        "e0af68"
        "7aa2f7"
        "bb9af7"
        "7dcfff"
        "c0caf5"
      ];
    };
  };
  themeFiles = name: p: [
    {
      name = "nascentos/themes/${name}/hyprland.lua";
      value.text = ''
        hl.config({
          general = { col = { active_border = "rgb(${p.accent})", inactive_border = "rgb(${p.muted})" } },
          misc = { background_color = "rgb(${p.background})" },
        })
      '';
    }
    {
      # Layout follows the owner's Polybar: workspaces + title left, date centre, stats right,
      # each stat's icon tinted and its value in the foreground colour.
      name = "nascentos/themes/${name}/waybar.json";
      value.text =
        let
          tint = color: icon: "<span color='#${color}'>${icon}</span>";
          red = builtins.elemAt p.colors 1;
          green = builtins.elemAt p.colors 2;
          yellow = builtins.elemAt p.colors 3;
          blue = builtins.elemAt p.colors 4;
          purple = builtins.elemAt p.colors 5;
        in
        builtins.toJSON {
          layer = "top";
          position = "top";
          height = 30;
          margin-top = 7;
          margin-left = 7;
          margin-right = 7;
          spacing = 0;
          modules-left = [
            "hyprland/workspaces"
            "hyprland/window"
          ];
          modules-center = [ "clock" ];
          modules-right = [
            "custom/install"
            "cpu"
            "memory"
            "disk"
            "pulseaudio"
            "battery"
            "custom/clipboard"
            "custom/power"
            "tray"
          ];
          "hyprland/workspaces" = {
            format = "{icon}";
            format-icons = {
              "1" = "";
              "2" = "";
              "3" = "";
              "4" = "󰬡";
              "5" = "󰍩";
              "6" = "";
              "7" = "󰽰";
              "8" = "";
              "9" = "";
              default = "";
            };
            persistent-workspaces."*" = 9;
            on-click = "activate";
          };
          "hyprland/window" = {
            format = "{title}";
            max-length = 60;
            separate-outputs = true;
          };
          clock = {
            format = "{:%a %d %b  %H:%M}";
            tooltip-format = "<tt>{calendar}</tt>";
          };
          cpu = {
            interval = 2;
            format = "${tint p.orange ""} {usage}%";
          };
          memory = {
            interval = 2;
            format = "${tint purple ""} {percentage}%";
          };
          disk = {
            interval = 25;
            path = "/";
            format = "${tint purple "󰋊"} {percentage_used}%";
          };
          pulseaudio = {
            format = "${tint blue "{icon}"} {volume}%";
            format-muted = "${tint red "󰝟"} muted";
            format-icons = [
              "󰕿"
              "󰖀"
              "󰕾"
            ];
            on-click = "pavucontrol";
            on-click-right = "nascent-media volume mute";
            scroll-step = 5;
          };
          battery = {
            states = {
              warning = 25;
              critical = 15;
            };
            format = "${tint green "{icon}"} {capacity}%";
            format-charging = "${tint blue "󰢜"} {capacity}%";
            format-plugged = "${tint blue "󰚥"} {capacity}%";
            format-icons = [
              "󰂎"
              "󰁺"
              "󰁻"
              "󰁼"
              "󰁽"
              "󰁾"
              "󰁿"
              "󰂀"
              "󰂁"
              "󰂂"
              "󰁹"
            ];
          };
          "custom/clipboard" = {
            format = "${tint yellow "󰅌"}";
            tooltip-format = "Clipboard history · Super+V";
            on-click = "nascent-clipboard pick";
          };
          "custom/power" = {
            format = "${tint red "⏻"}";
            tooltip-format = "Power · Super+Shift+E";
            on-click = "nascent-power";
          };
          tray.spacing = 6;
          "custom/install" = {
            exec = ''if command -v nascent-install >/dev/null 2>&1; then printf '%s\n' '{"text":"Install nascentOS","tooltip":"Open installer · Super+I"}'; else printf '%s\n' '{"text":""}'; fi'';
            return-type = "json";
            interval = "once";
            on-click = "nascent-install";
          };
        };
    }
    {
      name = "nascentos/themes/${name}/waybar.css";
      value.text = ''
        * { font-family: "JetBrainsMono Nerd Font", "JetBrainsMono NF", monospace; font-size: 14px; min-height: 0; }
        window#waybar { background: #${p.background}; color: #${p.foreground}; border-radius: 6px; }
        #workspaces button { color: #${p.foreground}; padding: 0 9px; border: none; border-radius: 0; border-bottom: 3px solid transparent; background: transparent; }
        #workspaces button.empty { color: #${p.muted}; }
        #workspaces button.active { background: #${p.surface}; border-bottom-color: #${p.accent}; }
        #workspaces button.urgent { background: #${builtins.elemAt p.colors 1}; color: #${p.background}; }
        #workspaces button:hover { background: #${p.surface}; box-shadow: none; text-shadow: none; }
        #workspaces button:first-child { border-top-left-radius: 6px; border-bottom-left-radius: 6px; }
        #window { padding: 0 12px; }
        #clock, #cpu, #memory, #disk, #pulseaudio, #battery, #custom-clipboard, #custom-power, #tray { padding: 0 8px; }
        #custom-power { padding-right: 12px; }
        #battery.warning:not(.charging) { color: #${builtins.elemAt p.colors 3}; }
        #battery.critical:not(.charging) { color: #${builtins.elemAt p.colors 1}; }
        #custom-install { background: #${p.accent}; color: #${p.background}; padding: 0 14px; margin: 3px; border-radius: 4px; font-weight: bold; }
        #custom-install:hover { background: #${p.foreground}; }
        tooltip { background: #${p.background}; color: #${p.foreground}; border: 1px solid #${p.accent}; border-radius: 6px; }
      '';
    }
    {
      name = "nascentos/themes/${name}/kitty.conf";
      value.text = ''
        font_family Fira Code
        font_size 11
        background #${p.background}
        foreground #${p.foreground}
        cursor #${p.accent}
        selection_background #${p.muted}
        selection_foreground #${p.foreground}
        window_padding_width 12
      ''
      + builtins.concatStringsSep "\n" (
        builtins.genList (i: "color${toString i} #${builtins.elemAt p.colors i}") 16
      )
      + "\n";
    }
    {
      name = "nascentos/themes/${name}/fuzzel.ini";
      value.text = ''
        [main]
        font=sans-serif:size=12
        icon-theme=Papirus-Dark
        width=42
        lines=10
        horizontal-pad=24
        vertical-pad=18
        [colors]
        background=${p.background}f5
        text=${p.foreground}ff
        match=${p.accent}ff
        selection=${p.surface}ff
        selection-text=${p.foreground}ff
        selection-match=${p.accent}ff
        border=${p.accent}ff
        [border]
        width=2
        radius=8
      '';
    }
    {
      name = "nascentos/themes/${name}/hyprlock.conf";
      value.text = ''
        background {
          color = rgb(${p.background})
        }
        input-field {
          monitor =
          size = 300, 50
          position = 0, -40
          outer_color = rgb(${p.accent})
          inner_color = rgb(${p.surface})
          font_color = rgb(${p.foreground})
          placeholder_text = Password
        }
      '';
    }
    {
      name = "nascentos/themes/${name}/mako.conf";
      value.text = ''
        font=sans-serif 11
        background-color=#${p.background}
        text-color=#${p.foreground}
        border-color=#${p.accent}
        border-size=2
        border-radius=8
        padding=16
        default-timeout=7000
      '';
    }
  ];
in
{
  environment.etc = builtins.listToAttrs (
    builtins.concatLists (builtins.attrValues (builtins.mapAttrs themeFiles palettes))
  );
}
