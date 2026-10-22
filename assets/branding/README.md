# nascentOS branding

`main-logo.png` is the approved **main logo**, copied unchanged from the original
built-in ImageGen output. The design was based on the user's home photograph:
a bay between hills, a distant central mountain, tropical foreground, and a
Nord-inspired stencil treatment with subtle dithering. The original generated
file is preserved outside the repository. This provenance records no additional
license grant for the user's photograph.

SHA-256: `421812bf8c068ffc8999289d5ea0d6be1e4b85199140b71101adb2cc79ed872c`

`social-preview.png` is the separately delivered 1280×640 GitHub sharing asset
derived from the approved main logo. Saving it here does not update the GitHub
repository's social-preview setting.

`terminal-logo.txt` is a separate, hand-authored mountain ridge outline,
27 columns maximum by 4 rows. The central peak and smaller flanking slopes
simplify the landscape for terminal use. Use a monospace font; allow at least
27 columns for the art and additional room for adjacent system information.

## Preview

From the repository root:

```sh
sh assets/branding/show-logo.sh --plain
sh assets/branding/show-logo.sh --color
```

Without an argument, the script uses Nord truecolor on a terminal, unless
`NO_COLOR` is set or `TERM=dumb`; redirected output defaults to plain text.
`--color` explicitly emits ANSI colors, including when piped. Truecolor support
is needed for exact Nord colors; plain text works without it.

## Fetch tools

Examples assume the repository root is the current directory. Replace paths
with installed absolute asset paths when integrating into the OS configuration.
No fetch tool is installed or configured by these assets.

### Fastfetch

[Upstream logo options](https://github.com/fastfetch-cli/fastfetch/wiki/Logo-options)
document raw text files and standard input:

```sh
fastfetch --logo-type file-raw --logo "$PWD/assets/branding/terminal-logo.txt"
sh assets/branding/show-logo.sh --color | fastfetch --file-raw -
```

### Neofetch

[Upstream custom ASCII format](https://github.com/dylanaraps/neofetch/wiki/Custom-Ascii-art-file-format)
requires escaped backslashes. `terminal-logo.neofetch.txt` contains the same art
with each backslash doubled for Neofetch's escape processing. Do not display
that adapter file directly with `cat`.

```sh
neofetch --ascii "$PWD/assets/branding/terminal-logo.neofetch.txt"
```

Regenerate the adapter after editing the plain art:

```sh
python3 - <<'PY'
from pathlib import Path
p = Path('assets/branding')
(p / 'terminal-logo.neofetch.txt').write_text(
    (p / 'terminal-logo.txt').read_text().replace('\\', '\\\\'))
PY
```

### pfetch (original POSIX sh implementation)

The original [pfetch configuration](https://github.com/dylanaraps/pfetch#configuration)
uses `PF_ASCII` to choose a built-in logo; it does not provide an arbitrary logo
file option. This portable example prints the outline **above** the information,
omitting pfetch's own logo:

```sh
sh assets/branding/show-logo.sh
PF_INFO='title os host kernel uptime pkgs memory' pfetch
```

Forks and rewrites named pfetch may have different options. This example targets
`dylanaraps/pfetch`, not every implementation with that name.

## Verification

Checked 2026-10-22: original image byte equality and SHA-256; shell syntax;
ASCII-only content and dimensions; plain output equality; stripping ANSI from
the colored output reproduces the plain file exactly. Rendered the escaped
adapter with upstream Neofetch (`--config none --logo`) and verified all 4
lines survived intact. Ran upstream POSIX pfetch with `PF_SOURCE=''` and
`PF_INFO='os kernel'` to check the information-only path without user config.
The upstream scripts were downloaded to temporary files, not installed.
Fastfetch commands were verified against upstream documentation; its executable
was unavailable here. The repository currently documents no bootstrap or gates.
