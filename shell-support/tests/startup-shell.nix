# Native fixture with the production global-init hook in Zsh's real startup path.
# No host /etc files or pre-existing user startup files are modified.
{ nixpkgs, system }:
let
  pkgs = nixpkgs.legacyPackages.${system};
  config =
    (nixpkgs.lib.nixosSystem {
      system = "aarch64-linux";
      modules = [
        ../module.nix
        {
          nascent.shell.enable = true;
          system.stateVersion = "26.05";
        }
      ];
    }).config;
in
pkgs.zsh.overrideAttrs (old: {
  configureFlags =
    old.configureFlags
    ++ map (name: "--enable-${name}=${builtins.placeholder "out"}/etc/${name}") [
      "zprofile"
      "zshrc"
      "zlogin"
      "zlogout"
    ];
  postInstall = old.postInstall + ''
    rm -f $out/etc/zshenv.zwc
    cat > $out/etc/zshenv <<'ZSHENV'
    # Test-only negative control exercises the same binary without seeding.
    if [[ ''${NASCENT_STARTUP_TEST_SKIP_SEED:-0} != 1 ]]; then
      ${config.programs.zsh.shellInit}
    fi
    ZSHENV
    cat > $out/etc/zshrc <<'ZSHRC'
    ${config.programs.zsh.promptInit}
    ZSHRC
    touch $out/etc/zprofile $out/etc/zlogin $out/etc/zlogout
  '';
})
