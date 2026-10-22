{
  description = "nascentOS: an experimental, configurable NixOS desktop";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/cd4ea8d57de16f4810bc5f14207bac45fbf19f67";

  outputs =
    { self, nixpkgs }:
    let
      linuxSystems = [
        "aarch64-linux"
        "x86_64-linux"
      ];
      hostSystems = linuxSystems ++ [
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      forSystems = systems: nixpkgs.lib.genAttrs systems;
      guestSystem = host: builtins.replaceStrings [ "darwin" ] [ "linux" ] host;
      mkInstaller =
        system:
        nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            self.nixosModules.default
            ./modules/installer
            { _module.args.nascentSource = self; }
          ];
        };
      mkVM =
        system: host:
        nixpkgs.lib.nixosSystem {
          inherit system;
          modules = [
            self.nixosModules.default
            ./hosts/vm
            { virtualisation.host.pkgs = import nixpkgs { system = host; }; }
          ];
        };
    in
    {
      nixosModules.default = import ./modules;
      nixosModules.nvidia = import ./modules/hardware/nvidia.nix;
      nixosConfigurations = {
        vm-aarch64 = mkVM "aarch64-linux" "aarch64-linux";
        vm-x86_64 = mkVM "x86_64-linux" "x86_64-linux";
        installer-aarch64 = mkInstaller "aarch64-linux";
        installer-x86_64 = mkInstaller "x86_64-linux";
      };
      packages = forSystems hostSystems (
        host:
        {
          # QEMU and the launcher run on the host; the guest remains Linux.
          vm = (mkVM (guestSystem host) host).config.system.build.vm;
          default = self.packages.${host}.vm;
        }
        // nixpkgs.lib.optionalAttrs (builtins.elem host linuxSystems) {
          installer = (mkInstaller host).config.system.build.isoImage;
          # Faster local iteration; keep the normal installer compression unchanged.
          installer-dev =
            ((mkInstaller host).extendModules {
              modules = [ { isoImage.squashfsCompression = "zstd -Xcompression-level 3"; } ];
            }).config.system.build.isoImage;
        }
      );
      formatter = forSystems hostSystems (system: nixpkgs.legacyPackages.${system}.nixfmt);
      checks = forSystems hostSystems (
        system:
        {
          cli =
            nixpkgs.legacyPackages.${system}.runCommand "nascent-cli-check"
              {
                nativeBuildInputs = with nixpkgs.legacyPackages.${system}; [
                  bash
                  coreutils
                  python3
                  shellcheck
                ];
              }
              ''
                export NASCENT_SOURCE=${self}
                export NIXPKGS_SOURCE=${nixpkgs}
                shellcheck ${self}/bin/* ${self}/scripts/*
                # Preserve the approved renderer; its POSIX empty CDPATH assignment is intentional.
                shellcheck --exclude=SC1007 ${self}/assets/branding/show-logo.sh
                python3 ${self}/tests/cli.py
                python3 ${self}/tests/test_desktop_intent.py
                python3 ${self}/tests/test_installer.py
                python3 ${self}/tests/test_agent_ui.py
                python3 ${self}/tests/test_install_launcher.py
                python3 -m unittest discover -s ${self}/installer/software-selection/tests -p 'test_*.py'
                python3 -m unittest discover -s ${self}/appimage-support/tests -p 'test_*.py'
                python3 -m unittest discover -s ${self}/mail-support/tests -p 'test_*.py'
                python3 -m unittest discover -s ${self}/vpn-support/tests -p 'test_*.py'
                python3 -m unittest discover -s ${self}/release-support -p 'test_*.py'
                touch $out
              '';
        }
        // nixpkgs.lib.optionalAttrs (builtins.elem system linuxSystems) {
          installer =
            let
              cfg = (mkInstaller system).config;
            in
            assert cfg.nascent.desktop.enable;
            assert !cfg.services.desktopManager.gnome.enable;
            assert !cfg.services.openssh.enable;
            assert cfg.services.greetd.settings.initial_session.user == "nixos";
            assert builtins.stringLength cfg.isoImage.volumeID <= 32;
            nixpkgs.legacyPackages.${system}.runCommand "nascent-installer-config" { } "touch $out";
          profiles = import ./tests/profiles.nix {
            inherit nixpkgs system;
            nascentModule = self.nixosModules.default;
          };
          boot = nixpkgs.legacyPackages.${system}.testers.runNixOSTest (
            import ./tests/boot.nix {
              nascentModule = self.nixosModules.default;
            }
          );
        }
      );
    };
}
