{ nascentModule }:
{
  name = "nascentos-boot";
  nodes.machine = { pkgs, ... }: {
    imports = [ nascentModule ];
    nascent.desktop.enable = true;
    system.stateVersion = "26.05";
    services.greetd = {
      enable = true;
      settings.default_session.command = "${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session";
    };
  };
  testScript = ''
    machine.start()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("greetd.service")
    machine.wait_for_unit("NetworkManager.service")
    machine.succeed("test -s /etc/nascentos/hyprland.lua")
    machine.succeed("command -v nascent-session Hyprland kitty fuzzel waybar hyprlock")
    machine.fail("systemctl is-active sshd.service")
  '';
}
