# Desktop changes

An optional agent reference, inspired by Omarchy's focused `agents/skills/` layout.
No provider automatically loads this file. Read the repository's own AGENTS.md
and user instructions before using it.

- Change portable defaults in modules/; keep disks, boot and drivers per host.
- Nord is the default. Palettes in modules/desktop/themes.nix generate app configs.
- User-owned theme/agent selections live in $XDG_CONFIG_HOME/nascentos.
- Commands in bin/ have one job and route through nascent; preserve argument arrays.
- Run scripts/check and the relevant CLI tests; Linux boot and interactive graphics
  are separate gates. Never report VM/hardware success from evaluation alone.
- Avoid secrets in source; provider adapters own their own authentication/permissions.
