# Agent-friendly baseline tools

Reviewed primary manifests on 2026-10-22:

- [OpenAI codex-universal Dockerfile](https://github.com/openai/codex-universal/blob/47f4f0eb5337083e2f610db0d15558932cb4901d/Dockerfile), revision `47f4f0eb5337083e2f610db0d15558932cb4901d`: git/git-lfs, ripgrep, fd, jq, HTTP/download utilities, rsync, make/pkg-config and archives.
- [Anthropic Claude Code devcontainer](https://github.com/anthropics/claude-code/blob/1132b8a98e93300bb3822197fb7eee12ce4fb906/.devcontainer/Dockerfile), revision `1132b8a98e93300bb3822197fb7eee12ce4fb906`: git, jq, gh, fzf, shell/editor and process/network tools.

These are evidence for tool selection, not copied Dockerfiles or security policy.
Their broad language matrices and container-specific firewall/permission settings
are not carried into the OS.

Default packages when the desktop module is enabled:

| Purpose | Nix packages |
| --- | --- |
| Shell and text | bashInteractive, coreutils, findutils, gnused, gawk |
| Search/discovery | ripgrep, fd, fzf |
| Structured data | jq, yq-go |
| Version control | git, git-lfs, gh |
| Transfer | curl, wget, rsync, openssh (client; no sshd enabled) |
| Patch/diff | diffutils, patch |
| Archives | gnutar, gzip, bzip2, xz, zip, unzip |
| Tasks and scripts | just, gnumake, pkg-config, python3, uv |
| Editor and checks | neovim/LazyVim, shellcheck, shfmt |

The desktop also includes gcc, nodejs, tree-sitter and lazygit for LazyVim's common
plugin/tooling needs. Language-specific toolchains and heavier IDEs belong in a
project devShell or an explicit personal package profile. `nascent.apps.enable`
adds the existing Brewfile's developer preferences; those are distinct from the
universal defaults. The default editor is `nascent-editor`, with writable personal
LazyVim configuration. No Home Manager is used.
