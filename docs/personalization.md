# Writable personal configuration

System packages/defaults are pinned by the flake. Session startup copies missing
theme bundles and the selected personal LazyVim config into the user's XDG config
directory, dereferencing Nix store symlinks and making the copies writable. Existing
user directories/files are never replaced. No Home Manager is used.

`nascent menu` (Super + Space) offers apps, terminal, themes, agent, lock and logout.
`nascent launch apps` (Super + D) opens the application launcher directly.
The inset bar's **nascentOS** button reopens the menu. In the live ISO, the bar
also has **Install nascentOS**, available with Super + I and in the menu.
Typing a letter in the menu filters its choices; Escape dismisses it.

```sh
nascent theme list
nascent theme set tokyo-night
nascent theme set nord
nascent wallpaper set /absolute/path/to/your/image.png
nascent editor
```

Nord is the default across compositor borders, bar, terminal ANSI palette, launcher,
notifications and lock screen. The second bundled palette is Tokyo Night. Selected
themes persist through logout and system rebuilds. Switching reloads Hyprland,
Waybar and mako; new terminals/launchers/locks use the selection. Existing terminal
windows retain their colors. Personal LazyVim stays Nord independently.
Nordic GTK and Kvantum/Qt defaults theme application windows too; these defaults
remain overridable through normal personal GTK/Qt settings. The Tokyo Night
command switches the bundled desktop components; it does not change application
GTK/Qt themes.

Edit `~/.config/nascentos/themes/<name>/` directly, then select that theme again to
reload. Copy a complete theme directory under a new simple name to create a theme.
Edit `~/.config/nascentos/waybar.json` for bar modules and
`~/.config/nascentos/hyprland.lua` for compositor overrides. Personal overrides run
last. `~/.config/kitty/kitty.conf` is loaded after the selected terminal palette.
Use `$XDG_CONFIG_HOME` instead of `~/.config` if set. No rebuild is needed for these
edits. Shipped defaults update only with the system; existing personal copies do
not get silently refreshed.

## Wallpaper source

The supplied [TheArctesian/wallpapers repository](https://github.com/TheArctesian/wallpapers/tree/2105e063afd839fdd06b47eaf426716fcffa21b4)
at revision `2105e063afd839fdd06b47eaf426716fcffa21b4` keeps original images in
`raw/` and Nord-dithered renders in `screens/<width>x<height>/`. Existing geometries
are `1080x1920`, `2560x1440` and `3024x1964`. It has no license file at this revision,
so image/code redistribution rights are unresolved. The selected default is the
existing `screens/2560x1440/home1.png`, copied unchanged to
`assets/wallpapers/home1-nord.png` (Git blob
`6366ec73eff21f4b20ffee1f9eaddc7ba5450585`). It places the Nord-dithered home photo
centrally on a Nord background. The original `raw/home1.JPG` is preserved separately
as `assets/wallpapers/home1.JPG` (Git blob
`ce854da0d30d58f1d6b64c521e62c26bc40f722a`). Both follow the user's explicit request.
No other upstream images or scripts are bundled, and broader
redistribution rights for the wallpaper collection remain unresolved.

Explicitly fetch one of your rendered images into your writable local data directory:

```sh
nascent wallpaper fetch 2560x1440/bamboo.png
```

This pinned fetch downloads one image from `screens/` and selects it. Browse the
source for other names; the simple fetch helper accepts names containing letters,
digits, underscores and hyphens. For names containing spaces, download manually
and use `nascent wallpaper set FILE`. The command does not run the upstream
Docker renderer or COSMIC/macOS wallpaper backends. swaybg applies the selected
image across outputs; per-monitor geometry matching/render generation is future work.

## LazyVim and application inventory

Canonical upstream: [TheArctesian/DotFiles](https://github.com/TheArctesian/DotFiles/tree/602357c47db57de7c9d956788508842be1449e15).
The local clean checkout at `Scripts/Personal/dotfiles` matched remote HEAD
`602357c47db57de7c9d956788508842be1449e15`. Its `.config/nvim` was copied unchanged
into `assets/nvim`, preserving its Apache-2.0 license, Nord plugin setup and plugin lock
file. `nascent editor` bootstraps that config only when no nvim config
exists. LazyVim/lazy.nvim installs plugins on first launch with network access;
that first-run workflow has not been tested here. No plugin authentication state,
secret environment files or credential stores were copied.

The Brewfile is at that revision's repository root, rather than under legacy.
`docs/Brewfile.source` preserves the inspected inventory. `modules/apps.nix` maps
its portable developer CLI set (`nascent.apps.enable`), desktop apps
(`nascent.apps.desktop.enable`) and selected proprietary apps
(`nascent.apps.unfree.enable`) separately. Enable these per host; they're not all
installed in the small VM by default. Desktop preset includes Brave, Ghostty,
KeepassXC, Neovide, OBS, Blender, Beekeeper Studio, Signal, VSCodium, Zed and Zotero;
the proprietary preset adds Obsidian, Slack, Spotify and Zoom.

Not automatically migrated: XcodeGen/fastlane and macOS-only apps (Caffeine,
Raycast, XQuartz, native ChatGPT/Claude/Codex clients), Docker Desktop (Linux
engine setup is a separate permission/service choice), GitHub Desktop, Android/
Unity/gaming stacks, Teams/WhatsApp wrappers, Zen, Proton desktop/VPN integration
and the OpenCode desktop app. OpenCode CLI is in the developer preset. Brew's
OpenWhispr entry is addressed initially with the optional Whisper CLI, not an
assertion of push-to-talk desktop parity. Multiple Python versions are collapsed
to the pinned Python 3; project-specific versions should use project flakes.
Other personal dotfiles remain in the source repo until individually reviewed;
macOS window-manager scripts are not applied to Hyprland.

## Approved logo

The main logo is preserved unchanged at `assets/branding/main-logo.png`, separate
from the original home-photo wallpaper. It brands the Calamares welcome/sidebar
and installer application icon. `nascent logo --plain` or `nascent logo --color`
uses the approved ASCII artwork installed at `/etc/nascentos/branding/`.
See `assets/branding/README.md` for provenance and Neofetch/pfetch/Fastfetch adapters;
that asset README describes the separate branding task's original verification.
The original renderer remains unchanged; the integrated shell gate excludes only
ShellCheck's style warning SC1007 for its intentional POSIX empty `CDPATH` assignment.
