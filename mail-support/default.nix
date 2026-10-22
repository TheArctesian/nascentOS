{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.nascent.mail;
  clients = [
    "protonmail-desktop"
    "thunderbird"
    "geary"
    "evolution"
  ];
  selected = builtins.filter (id: builtins.elem id clients) cfg.clients;
  supported =
    id: lib.meta.availableOn pkgs.stdenv.hostPlatform pkgs.${id} && !(pkgs.${id}.meta.broken or false);
  desktop = id: "nascent-mail-${id}.desktop";
  entries = map (
    id:
    pkgs.makeDesktopItem {
      name = "nascent-mail-${id}";
      desktopName = if id == "protonmail-desktop" then "Proton Mail" else id;
      exec = "${lib.getExe pkgs.${id}} %u";
      noDisplay = true; # URI handler only; keep the upstream application menu entry.
      icon = if id == "protonmail-desktop" then "proton-mail" else id;
      categories = [
        "Network"
        "Email"
      ];
      mimeTypes = [ "x-scheme-handler/mailto" ];
    }
  ) (builtins.filter supported selected);
in
{
  options.nascent.mail = {
    enable = lib.mkEnableOption "selected mail clients and desktop integration";
    clients = lib.mkOption {
      type = lib.types.listOf (lib.types.enum clients);
      default = [ "protonmail-desktop" ];
      description = "Only these clients are installed; Proton Desktop requires x86_64 Linux at this pin.";
    };
    defaultClient = lib.mkOption {
      type = lib.types.nullOr (lib.types.enum clients);
      default = if cfg.clients == [ ] then null else builtins.head cfg.clients;
      description = "System mailto default; user MIME preferences take precedence. Null leaves it unset.";
    };
    bridge.enable = lib.mkEnableOption "Proton Bridge GUI for manually configured IMAP/SMTP clients";
    bridge.credentialStore = lib.mkOption {
      type = lib.types.enum [
        "gnome-keyring"
        "existing"
      ];
      default = "gnome-keyring";
      description = "Provide GNOME Keyring, or reuse an already configured Secret Service/Pass store.";
    };
  };
  config = lib.mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.clients == lib.unique cfg.clients;
        message = "nascent.mail.clients contains duplicates.";
      }
      {
        assertion = cfg.defaultClient == null || builtins.elem cfg.defaultClient cfg.clients;
        message = "nascent.mail.defaultClient must be an installed mail client.";
      }
    ]
    ++ map (id: {
      assertion = supported id;
      message = "nascent.mail: ${id} is unavailable on ${pkgs.stdenv.hostPlatform.system}; choose an available client or Proton web.";
    }) selected;
    environment.systemPackages =
      map (id: pkgs.${id}) (builtins.filter supported selected)
      ++ entries
      ++ lib.optional cfg.bridge.enable pkgs.protonmail-bridge-gui;
    programs.geary.enable = builtins.elem "geary" selected;
    programs.evolution.enable = builtins.elem "evolution" selected;
    services.gnome.gnome-keyring.enable = lib.mkIf (
      cfg.bridge.enable && cfg.bridge.credentialStore == "gnome-keyring"
    ) true;
    xdg.mime.defaultApplications."x-scheme-handler/mailto" = lib.mkIf (cfg.defaultClient != null) (
      lib.mkDefault (desktop cfg.defaultClient)
    );
    xdg.mime.addedAssociations."x-scheme-handler/mailto" = map desktop selected;
  };
}
