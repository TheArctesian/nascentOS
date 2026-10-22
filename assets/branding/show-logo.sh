#!/bin/sh
# Render the mountain outline; explicit --color also works when piped to Fastfetch.
set -eu

case ${1:-auto} in
    --plain) mode=plain ;;
    --color) mode=color ;;
    auto)
        mode=plain
        if [ -t 1 ] && [ "${TERM:-dumb}" != dumb ] && [ -z "${NO_COLOR+x}" ]; then
            mode=color
        fi
        ;;
    *) printf 'Usage: %s [--plain|--color]\n' "$0" >&2; exit 2 ;;
esac

branding_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$mode" = plain ]; then
    cat "$branding_dir/terminal-logo.txt"
else
    # Nord frost blue; no background is forced.
    awk '
        { printf "\033[38;2;129;161;193m%s\033[0m\n", $0 }
    ' "$branding_dir/terminal-logo.txt"
fi
