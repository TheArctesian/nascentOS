# Copy to hosts/<machine>/default.nix and generate hardware-configuration.nix
# on that machine. This example assumes UEFI; review boot/storage before use.
{ pkgs, ... }:
{
  imports = [
    ./hardware-configuration.nix
    # ../../modules/hardware/nvidia.nix # only after identifying the GPU
  ];
  nascent.desktop.enable = true;
  # Personal presets for the first x86 machine; disable sets you do not want.
  nascent.apps.enable = true;
  nascent.apps.desktop.enable = true;
  nascent.apps.unfree.enable = true;
  nascent.localAI.enable = true;
  networking.hostName = "nascent";
  system.stateVersion = "26.05";
  time.timeZone = "UTC";
  i18n.defaultLocale = "en_US.UTF-8";
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;
  users.users.owner = {
    isNormalUser = true;
    extraGroups = [
      "wheel"
      "networkmanager"
    ];
    # Set a password interactively after installation (see docs/install.md).
  };
  services.greetd = {
    enable = true;
    settings.default_session.command = "${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session";
  };
}
