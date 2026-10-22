{
  config,
  lib,
  pkgs,
  ...
}:
{
  imports = [
    ./desktop
    ./local-ai.nix
    ./apps.nix
    ../installer/software-selection/integration.nix
    ../mail-support/installer-adapter.nix
    ../password-support/catalog-adapter.nix
    ../vpn-support/module.nix
    ../gaming-support
    ../shell-support/integration.nix
  ];

  options.nascent.desktop.enable = lib.mkEnableOption "the nascentOS Hyprland desktop prototype";

  config = lib.mkIf config.nascent.desktop.enable {
    nix.settings.experimental-features = [
      "nix-command"
      "flakes"
    ];
    networking.networkmanager.enable = lib.mkDefault true;
    security.rtkit.enable = true;
    services.pipewire = {
      enable = true;
      alsa.enable = true;
      pulse.enable = true;
    };
    environment.systemPackages =
      with pkgs;
      [
        bashInteractive
        coreutils
        findutils
        gnused
        gawk
        ripgrep
        fd
        fzf
        jq
        yq-go
        git
        git-lfs
        gh
        curl
        wget
        rsync
        openssh
        diffutils
        patch
        gnutar
        gzip
        bzip2
        xz
        zip
        unzip
        just
        gnumake
        pkg-config
        shellcheck
        shfmt
        python3
        uv
      ]
      ++ lib.optional (!config.nascent.software.enable) pkgs.neovim;
  };
}
