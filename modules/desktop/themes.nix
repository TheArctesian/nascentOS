{ ... }:
let
  palettes = {
    nord = {
      background = "2e3440";
      surface = "3b4252";
      foreground = "eceff4";
      muted = "4c566a";
      accent = "88c0d0";
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
      name = "nascentos/themes/${name}/waybar.css";
      value.text = ''
        * { font-family: sans-serif, "Font Awesome 7 Free", "Font Awesome 6 Free", "FontAwesome"; font-size: 13px; }
        window#waybar { background: #${p.background}; color: #${p.foreground}; border: 1px solid #${p.muted}; border-radius: 6px; }
        button { min-height: 28px; border: none; border-radius: 4px; }
        #workspaces button { color: #${p.foreground}; padding: 0 10px; border-bottom: 2px solid transparent; }
        #workspaces button.active { background: #${p.surface}; color: #${p.accent}; border-bottom-color: #${p.accent}; }
        #custom-menu, #clock, #network, #pulseaudio, #tray { padding: 0 12px; }
        #custom-menu { color: #${p.accent}; font-weight: bold; }
        #custom-install { background: #${p.accent}; color: #${p.background}; padding: 0 14px; margin: 4px; border-radius: 4px; font-weight: bold; }
        #custom-menu:hover, #clock:hover, #network:hover, #pulseaudio:hover { background: #${p.surface}; }
        #custom-install:hover { background: #${p.foreground}; }
        tooltip { background: #${p.background}; color: #${p.foreground}; border: 1px solid #${p.accent}; }
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
