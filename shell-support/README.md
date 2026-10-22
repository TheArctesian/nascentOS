# Interactive Zsh support

This scoped module uses the baseline's pinned nixpkgs commit
`cd4ea8d57de16f4810bc5f14207bac45fbf19f67`, without Home Manager.

## Integration contract

Copy `shell-support/` into the final source and add
`../shell-support/integration.nix` to `modules/default.nix` imports. The adapter
defaults `nascent.shell.enable` to `nascent.desktop.enable`. Standalone consumers
can import `shell-support/module.nix` and set `nascent.shell.enable = true`.

`nascent.shell.defaultShell` accepts `"zsh"` (default) or `"bash"`.
It sets `users.defaultUserShell` at priority 900, above NixOS's Bash default but
below ordinary administrator assignments. Explicit `users.users.<name>.shell`
values are respected. NixOS applies this to declared users with
`useDefaultShell` (including normal users), so new Calamares-created normal users
inherit Zsh without injecting usernames into installer output. An installer may
write `nascent.shell.defaultShell` to offer an optional choice; no picker schema
change is required. Review generated users that explicitly set a shell.

No account database is migrated here. Applying NixOS configuration can update
declared existing users who inherit its default; preserve their explicit shell
when integrating with an existing installation. This component has not been
applied to the running VM or host.

Kitty continues to use the account login shell; do not add a forced Kitty shell
command. Bash remains installed, and script/agent entry points retain explicit
Bash shebangs or invocations. No shell aliases or script interpreters are changed.
The desktop already provides Fira Code and Nord; this module adds no terminal or
font override. Nord's ANSI palette colors the prompt blocks.

## Personal configuration

During interactive startup, a user-owned writable copy of the Boxfish theme is
seeded at `~/.config/nascentos/zsh/boxfish.zsh-theme`, and a personal `.zshrc` is
seeded under `${ZDOTDIR:-$HOME}`. Existing files and links are never replaced.
The system loads the personal theme after Oh My Zsh; Zsh subsequently reads the
personal `.zshrc`, where users can override prompt, bindings, and preferences.
No activation script writes to anyone's home. New seed files have mode 600.
Failed home writes fall back to the system theme.

Packages and plugin sources stay in the Nix store. Oh My Zsh updates are disabled;
startup does not clone plugins or run installers. The writable theme is intentionally
not refreshed on rebuild; compare it with `/etc/nascentos/zsh/boxfish.zsh-theme`
to adopt later changes. Existing custom `.zshrc` content can override these defaults.

## Boxfish provenance and rendering

This is a Zsh port of [joelwanner/theme-boxfish](https://github.com/joelwanner/theme-boxfish)
at commit `7c448cef4c61e7b66e8f57afd14c6a6764b19dc7`, rather than a Fish script
sourced into Zsh. The original MIT license is preserved in `assets/BOXFISH-LICENSE`
and installed beside the system theme, including its original copyright placeholder.

The upstream ASCII-only blocks are preserved: blue abbreviated directory,
green clean branch, yellow dirty branch, and bold white ` ! ` on red after an
error. No right prompt or Powerline font is required. As upstream, a detached
HEAD omits the branch block. The port escapes literal percent signs and disables
prompt substitution to keep directory and branch names literal.

Emacs bindings remain the Oh My Zsh default. To enable vi mode and its compact
indicator, add `bindkey -v` and `NASCENT_BOXFISH_VI=1` to `.zshrc`. Insert is
green, command is red, and an active visual region is yellow. Fish's distinct
`replace_one` mode has no matching Zsh keymap and is not represented separately.

## Validation

Bootstrap/gate: install Nix and Python 3, then run `bash shell-support/tests/check`.
It fetches pinned native packages from Nix, checks Nix formatting, evaluates both
Linux architectures, parses the generated NixOS zshrc, and runs six temporary-HOME
runtime tests using native pinned Zsh. The scoped worktree has no root flake or
root `scripts/check`; run the baseline's `scripts/check` after integration.

The runtime test loads packaged Oh My Zsh, zsh-users autosuggestions and syntax
highlighting; it verifies an actual history suggestion, Git completion, prompt
blocks, error status, vi repaint, safe path expansion, ownership, and preserved
personal edits/dangling links. It does not claim Linux login/Kitty/visual highlighting
runtime coverage. A fresh installed-system gate should check `/etc/passwd`, open
Kitty, accept a grey history suggestion with Right, observe valid/invalid command
colors, and verify custom edits after a second login. No guest reboot or deployment
is part of this component's validation.
