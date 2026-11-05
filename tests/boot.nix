{ nascentModule }:
{
  name = "nascentos-boot";
  nodes.machine = { ... }: {
    imports = [ nascentModule ];
    nascent.desktop.enable = true;
    system.stateVersion = "26.05";
    services.greetd.enable = true;
  };
  testScript = ''
    machine.start()
    machine.wait_for_unit("multi-user.target")
    machine.wait_for_unit("greetd.service")
    machine.succeed("grep -q nascent-greeter /etc/greetd/config.toml")
    machine.wait_for_unit("NetworkManager.service")
    machine.succeed("test -s /etc/nascentos/hyprland.lua")
    machine.succeed("command -v nascent-session Hyprland kitty fuzzel waybar hyprlock")
    machine.fail("systemctl is-active sshd.service")
  '';
}
