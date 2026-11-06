{ ... }:
let
  palettes = {
    nord = {
      background = "2e3440";
      crust = "242933";
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
      crust = "16161e";
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
          general = { col = { active_border = { colors = { "rgb(${p.accent})", "rgb(${builtins.elemAt p.colors 4})" }, angle = 45 }, inactive_border = "rgb(${p.surface})" } },
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
          height = 34;
          margin-top = 8;
          margin-left = 10;
          margin-right = 10;
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
            "custom/notify"
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
            max-length = 48;
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
          "custom/notify" = {
            exec = "nascent-notify status";
            return-type = "json";
            interval = "once";
            signal = 8;
            on-click = "nascent-notify dnd";
            on-click-right = "nascent-notify restore";
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
        * { font-family: "JetBrainsMono Nerd Font", "JetBrainsMono NF", monospace; font-size: 13px; min-height: 0; }
        window#waybar { background: alpha(#${p.crust}, 0.9); color: #${p.foreground}; border-radius: 8px; border: 1px solid alpha(#${p.surface}, 0.9); }
        tooltip { background: #${p.crust}; color: #${p.foreground}; border: 1px solid #${p.surface}; border-radius: 8px; }
        tooltip label { padding: 4px 6px; }
        #workspaces { margin: 0 4px 0 0; }
        #workspaces button { color: #${p.foreground}; padding: 0 7px; margin: 4px 1px; border: none; border-radius: 5px; background: transparent; box-shadow: inset 0 -2px transparent; transition: all 160ms ease-out; }
        #workspaces button.empty { color: #${p.muted}; }
        #workspaces button.active { background: #${p.surface}; color: #${p.accent}; box-shadow: inset 0 -2px #${p.accent}; }
        #workspaces button.urgent { background: #${builtins.elemAt p.colors 1}; color: #${p.crust}; }
        #workspaces button:hover { background: alpha(#${p.surface}, 0.7); box-shadow: inset 0 -2px #${p.muted}; text-shadow: none; }
        #window { padding: 0 10px; color: alpha(#${p.foreground}, 0.8); }
        window#waybar.empty #window { padding: 0; }
        #clock { font-weight: bold; padding: 0 12px; }
        #cpu, #memory, #disk, #pulseaudio, #battery, #custom-clipboard, #custom-notify, #custom-power, #tray { padding: 0 8px; }
        #custom-power { padding: 0 12px 0 8px; }
        #pulseaudio:hover, #custom-clipboard:hover, #custom-notify:hover, #custom-power:hover, #clock:hover { background: alpha(#${p.surface}, 0.7); border-radius: 5px; }
        #custom-notify { color: #${builtins.elemAt p.colors 4}; }
        #custom-notify.dnd { color: #${p.muted}; }
        #pulseaudio.muted { color: #${p.muted}; }
        #battery.warning:not(.charging) { color: #${builtins.elemAt p.colors 3}; }
        #battery.critical:not(.charging) { color: #${builtins.elemAt p.colors 1}; }
        #custom-install { background: #${p.accent}; color: #${p.crust}; padding: 0 14px; margin: 4px 6px; border-radius: 5px; font-weight: bold; }
        #custom-install:hover { background: #${p.foreground}; }
      '';
    }
    {
      name = "nascentos/themes/${name}/kitty.conf";
      value.text = ''
        font_family JetBrainsMono Nerd Font
        font_size 11
        background #${p.background}
        foreground #${p.foreground}
        cursor #${p.accent}
        cursor_trail 1
        selection_background #${p.surface}
        selection_foreground #${p.foreground}
        url_color #${p.accent}
        window_padding_width 14
        confirm_os_window_close 0
        # Hyprland decides window size; a remembered "maximized" state would cover tiled siblings.
        remember_window_size no
        tab_bar_style powerline
        active_tab_background #${p.accent}
        active_tab_foreground #${p.crust}
        inactive_tab_background #${p.surface}
        inactive_tab_foreground #${p.foreground}
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
        font=JetBrainsMono Nerd Font:size=12
        prompt="❯  "
        icon-theme=Papirus-Dark
        width=44
        lines=9
        horizontal-pad=22
        vertical-pad=18
        inner-pad=12
        line-height=26
        layer=overlay
        [colors]
        background=${p.crust}d9
        text=${p.foreground}ff
        prompt=${p.accent}ff
        placeholder=${p.muted}ff
        input=${p.foreground}ff
        match=${p.accent}ff
        selection=${p.surface}ff
        selection-text=${p.foreground}ff
        selection-match=${p.accent}ff
        border=${p.surface}ff
        [border]
        width=1
        radius=10
      '';
    }
    {
      name = "nascentos/themes/${name}/hyprlock.conf";
      value.text = ''
        general {
          hide_cursor = true
          ignore_empty_input = true
        }
        animations {
          enabled = true
          bezier = nascentOut, 0.22, 1, 0.36, 1
          animation = fadeIn, 1, 4, nascentOut
          animation = fadeOut, 1, 3, nascentOut
          animation = inputFieldDots, 1, 2, nascentOut
        }
        background {
          monitor =
          path = screenshot
          color = rgb(${p.background})
          blur_passes = 3
          blur_size = 8
          brightness = 0.6
        }
        label {
          monitor =
          text = $TIME
          color = rgb(${p.foreground})
          font_size = 88
          font_family = JetBrainsMono Nerd Font ExtraBold
          position = 0, 160
          halign = center
          valign = center
        }
        label {
          monitor =
          text = cmd[update:60000] date +'%A %d %B'
          color = rgba(${p.foreground}cc)
          font_size = 18
          font_family = JetBrainsMono Nerd Font
          position = 0, 70
          halign = center
          valign = center
        }
        input-field {
          monitor =
          size = 320, 52
          position = 0, -40
          halign = center
          valign = center
          outline_thickness = 2
          rounding = 10
          dots_size = 0.22
          dots_spacing = 0.35
          outer_color = rgb(${p.surface})
          inner_color = rgba(${p.crust}e6)
          font_color = rgb(${p.foreground})
          check_color = rgb(${p.accent})
          fail_color = rgb(${builtins.elemAt p.colors 1})
          capslock_color = rgb(${builtins.elemAt p.colors 3})
          font_family = JetBrainsMono Nerd Font
          placeholder_text = <span foreground="##${p.muted}">󰌾  $USER</span>
          fail_text = <i>$FAIL</i>
          fade_on_empty = false
        }
      '';
    }
    {
      name = "nascentos/themes/${name}/mako.conf";
      value.text = ''
        font=JetBrainsMono Nerd Font 10
        background-color=#${p.crust}e0
        text-color=#${p.foreground}
        border-color=#${p.surface}
        progress-color=over #${p.accent}55
        border-size=1
        border-radius=10
        padding=14,16
        margin=10
        width=380
        icons=1
        icon-path=/run/current-system/sw/share/icons/Papirus-Dark
        max-icon-size=40
        default-timeout=6000
        layer=overlay
        [urgency=low]
        text-color=#${p.foreground}cc
        [urgency=critical]
        border-color=#${builtins.elemAt p.colors 1}
        default-timeout=0
        [mode=do-not-disturb]
        invisible=1
        [app-name=nascent-osd]
        anchor=top-center
        width=300
        history=0
        icons=1
        max-icon-size=24
        format=<b>%s</b>
        progress-color=over #${p.accent}66
        invisible=0
      '';
    }
  ];
in
{
  environment.etc = builtins.listToAttrs (
    builtins.concatLists (builtins.attrValues (builtins.mapAttrs themeFiles palettes))
  );
}
