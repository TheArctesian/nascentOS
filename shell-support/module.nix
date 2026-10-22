{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.shell;
in
{
  options.nascent.shell = {
    enable = lib.mkEnableOption "the nascentOS interactive Zsh environment";
    defaultShell = lib.mkOption {
      type = lib.types.enum [
        "zsh"
        "bash"
      ];
      default = "zsh";
      description = "Default login shell for declared users using the system default.";
    };
  };

  config = lib.mkIf cfg.enable {
    users.defaultUserShell = lib.mkOverride 900 (
      if cfg.defaultShell == "zsh" then pkgs.zsh else pkgs.bashInteractive
    );
    environment.systemPackages = [
      pkgs.bashInteractive
      pkgs.git
    ];
    environment.shells = [ pkgs.bashInteractive ];
    programs.zsh = {
      enable = true;
      enableGlobalCompInit = false; # Oh My Zsh owns compinit.
      ohMyZsh = {
        enable = true;
        theme = ""; # The writable Boxfish port is loaded below.
        plugins = [ "git" ];
        preLoaded = ''
          zstyle ':omz:update' mode disabled
          DISABLE_AUTO_UPDATE=true
        '';
      };
      autosuggestions = {
        enable = true;
        highlightStyle = "fg=8";
        strategy = [ "history" ];
      };
      syntaxHighlighting.enable = true;
      # Zsh invokes zsh/newuser after global zshenv, before global zshrc.
      # Bootstrap here so a fresh interactive user never enters that wizard.
      shellInit = lib.mkBefore ''
        if [[ -o interactive ]]; then
          ${builtins.readFile ./assets/seed.zsh}
        fi
      '';
      promptInit = ''
        if [[ -r "$HOME/.config/nascentos/zsh/boxfish.zsh-theme" ]]; then
          source "$HOME/.config/nascentos/zsh/boxfish.zsh-theme"
        else
          source /etc/nascentos/zsh/boxfish.zsh-theme
        fi
      '';
    };
    environment.etc = {
      "nascentos/zsh/boxfish.zsh-theme".source = ./assets/boxfish.zsh-theme;
      "nascentos/zsh/zshrc".source = ./assets/zshrc;
      "nascentos/zsh/BOXFISH-LICENSE".source = ./assets/BOXFISH-LICENSE;
    };
  };
}
