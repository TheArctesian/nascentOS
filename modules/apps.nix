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
  selected = if software then config.nascent.software.selected else [ "neovim" ];
  unfreePackages = with pkgs; [
    obsidian
    slack
    spotify
    zoom-us
  ];
in
{
  options.nascent.apps = {
    enable = lib.mkEnableOption "the portable daily tools mapped from the personal Brewfile";
    desktop.enable = lib.mkEnableOption "the larger desktop application set";
    unfree.enable = lib.mkEnableOption "selected proprietary applications from the personal Brewfile";
  };
  config = lib.mkMerge [
    (lib.mkIf (config.nascent.desktop.enable && builtins.elem "neovim" selected) {
      # LazyVim dependencies, without Home Manager or an immutable user config.
      environment.systemPackages = with pkgs; [
        gcc
        gnumake
        unzip
        fd
        tree-sitter
        nodejs
        lazygit
      ];
    })
    (lib.mkIf config.nascent.apps.enable {
      programs.fish.enable = true;
      environment.systemPackages =
        (with pkgs; [
          actionlint
          azure-storage-azcopy
          azure-cli
          bat
          glow
          btop
          cloudflared
          eza
          fd
          gh
          git-filter-repo
          gitleaks
          go
          mpv
          nodejs
          jdk
          pipx
          poppler
          python3
          rustc
          cargo
          rustup
          sl
          tesseract
          uv
          yazi
          yt-dlp
          zellij
          zoxide
          opencode
        ])
        ++ lib.optional (builtins.elem "neovim" selected) pkgs.neovim;
    })
    (lib.mkIf config.nascent.apps.desktop.enable {
      environment.systemPackages =
        (with pkgs; [
          beekeeper-studio
          blender
          ghostty
          keepassxc
          obs-studio
          signal-desktop
          zotero
        ])
        ++ lib.optionals (!software) (
          with pkgs;
          [
            brave
            neovide
            vscodium
            zed-editor
          ]
        );
    })
    (lib.mkIf config.nascent.apps.unfree.enable {
      nixpkgs.config.allowUnfreePackages = map lib.getName unfreePackages;
      environment.systemPackages = unfreePackages;
    })
  ];
}
