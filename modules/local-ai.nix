{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.localAI;
in
{
  options.nascent.localAI = {
    enable = lib.mkEnableOption "local inference and Whisper transcription tools";
    backend = lib.mkOption {
      type = lib.types.enum [
        "cpu"
        "cuda"
      ];
      default = "cpu";
      description = "Optional inference backend; CUDA requires a separately selected NVIDIA driver profile.";
    };
    runtimePackage = lib.mkOption {
      type = lib.types.package;
      default = if cfg.backend == "cuda" then pkgs.ollama-cuda else pkgs.ollama-cpu;
      description = "Replaceable Ollama-compatible runtime package.";
    };
  };
  config = lib.mkIf cfg.enable {
    # An explicit CUDA backend permits only its pinned CUDA package family.
    # Other selected unfree applications use the additive package-name list.
    nixpkgs.config.allowUnfreePredicate = lib.mkIf (cfg.backend == "cuda") (
      package: lib.hasPrefix "${pkgs.cudaPackages.cudaNamePrefix}-" package.name
    );
    services.ollama = {
      enable = true;
      package = cfg.runtimePackage;
      host = "127.0.0.1";
      openFirewall = false;
      loadModels = [ ];
    };
    environment.systemPackages = [
      # CPU transcription remains useful without a GPU or CUDA build.
      (pkgs.whisper-cpp.override { cudaSupport = false; })
      pkgs.ffmpeg
    ];
  };
}
