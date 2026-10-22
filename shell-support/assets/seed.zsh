# Runs as the interactive user, never from activation or as another account.
() (
  emulate -L zsh
  (( EUID != 0 )) || return 0
  local seed_dir=${NASCENT_ZSH_SEED_DIR:-/etc/nascentos/zsh}
  local personal="$HOME/.config/nascentos/zsh"
  [[ -d $HOME && -O $HOME && -w $HOME ]] || return 0
  umask 077
  mkdir -p -- "$personal" || return 0
  local source_file target
  for source_file target in \
    "$seed_dir/boxfish.zsh-theme" "$personal/boxfish.zsh-theme" \
    "$seed_dir/zshrc" "${ZDOTDIR:-$HOME}/.zshrc"; do
    # Dangling links count as personal files too. Never replace them.
    if [[ ! -e $target && ! -L $target && -r $source_file ]]; then
      (setopt noclobber; cat -- "$source_file" > "$target") 2>/dev/null || true
    fi
  done
)
