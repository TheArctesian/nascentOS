# Opt in per host, after confirming its GPU. Not part of the common defaults.
{ lib, ... }:
{
  nixpkgs.config.allowUnfreePackages = [
    "nvidia-x11"
    "nvidia-settings"
    "nvidia-persistenced"
  ];
  services.xserver.videoDrivers = [ "nvidia" ];
  hardware.nvidia = {
    modesetting.enable = true;
    # Suitable for recent GPUs (including Ampere/RTX 3080); verify the actual card.
    open = lib.mkDefault true;
  };
}
