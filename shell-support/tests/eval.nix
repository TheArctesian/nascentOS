{ nixpkgs }:
let
  lib = nixpkgs.lib;
  mk =
    system: extra:
    (lib.nixosSystem {
      inherit system;
      modules = [
        ../module.nix
        {
          system.stateVersion = "26.05";
          boot.loader.grub.enable = false;
          fileSystems."/" = {
            device = "/dev/test";
            fsType = "ext4";
          };
          users.users.newuser.isNormalUser = true;
          users.users.explicit = {
            isNormalUser = true;
            shell = nixpkgs.legacyPackages.${system}.bashInteractive;
          };
        }
        extra
      ];
    }).config;
in
lib.genAttrs [ "aarch64-linux" "x86_64-linux" ] (
  system:
  let
    pkgs = nixpkgs.legacyPackages.${system};
    disabled = mk system { };
    enabled = mk system { nascent.shell.enable = true; };
    bash = mk system {
      nascent.shell = {
        enable = true;
        defaultShell = "bash";
      };
    };
    integrated = mk system {
      imports = [ ../integration.nix ];
      options.nascent.desktop.enable = lib.mkEnableOption "desktop fixture";
      config.nascent.desktop.enable = true;
    };
  in
  assert !disabled.programs.zsh.enable;
  assert builtins.all (a: a.assertion) enabled.assertions;
  assert enabled.users.users.newuser.shell == pkgs.zsh;
  assert enabled.users.users.explicit.shell == pkgs.bashInteractive;
  assert bash.users.users.newuser.shell == pkgs.bashInteractive;
  assert integrated.nascent.shell.enable;
  assert enabled.programs.zsh.ohMyZsh.enable;
  assert enabled.programs.zsh.ohMyZsh.theme == "";
  assert enabled.programs.zsh.autosuggestions.enable;
  assert enabled.programs.zsh.syntaxHighlighting.enable;
  assert !enabled.programs.zsh.enableGlobalCompInit;
  assert builtins.elem pkgs.bashInteractive enabled.environment.systemPackages;
  assert lib.hasInfix "mode disabled" enabled.programs.zsh.interactiveShellInit;
  assert lib.hasInfix "seed_dir" enabled.programs.zsh.shellInit;
  assert lib.hasInfix "EUID != 0" enabled.environment.etc.zshenv.text;
  assert !(lib.hasInfix "seed_dir" enabled.programs.zsh.interactiveShellInit);
  {
    passed = true;
    zshrc = enabled.environment.etc.zshrc.text;
    zshenv = enabled.environment.etc.zshenv.text;
    shellInit = enabled.programs.zsh.shellInit;
    defaults = {
      shell = "${enabled.users.defaultUserShell}/bin/zsh";
      inherit (pkgs.zsh) version;
    };
    versions = lib.genAttrs [ "oh-my-zsh" "zsh-autosuggestions" "zsh-syntax-highlighting" ] (
      name: pkgs.${name}.version
    );
  }
)
