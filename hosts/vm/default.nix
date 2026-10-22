{ modulesPath, pkgs, ... }:
{
  imports = [ (modulesPath + "/virtualisation/qemu-vm.nix") ];
  nascent.desktop.enable = true;
  networking.hostName = "nascent-vm";
  system.stateVersion = "26.05";
  time.timeZone = "UTC";
  i18n.defaultLocale = "en_US.UTF-8";

  # Disposable guest only. Never import this module on physical hardware.
  users.users.nascent = {
    isNormalUser = true;
    extraGroups = [
      "wheel"
      "networkmanager"
      "video"
    ];
    initialPassword = "nascent";
  };
  services.greetd = {
    enable = true;
    settings.default_session.command = "${pkgs.tuigreet}/bin/tuigreet --cmd nascent-session";
  };
  virtualisation = {
    memorySize = 4096;
    cores = 4;
    diskSize = 16384;
    graphics = true;
    resolution = {
      x = 1440;
      y = 900;
    };
    # A self-contained store image works on macOS without a Linux 9p share.
    useNixStoreImage = true;
    writableStore = true;
  };
  # QEMU's basic virtual GPU uses software rendering for this prototype.
  environment.sessionVariables.LIBGL_ALWAYS_SOFTWARE = "1";
}
