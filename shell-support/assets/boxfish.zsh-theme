# Zsh port of joelwanner/theme-boxfish, MIT; see BOXFISH-LICENSE.
# Reference commit: 7c448cef4c61e7b66e8f57afd14c6a6764b19dc7
# Blue abbreviated path, green clean/yellow dirty branch, red error block.
autoload -Uz add-zsh-hook add-zle-hook-widget
unsetopt prompt_subst
setopt prompt_percent

_nascent_boxfish_precmd() {
  local last_status=$?
  local cwd=$PWD branch dirty part
  if [[ $PWD == $HOME ]]; then
    cwd='~'
  elif [[ $PWD == $HOME/* ]]; then
    cwd="~/${PWD#$HOME/}"
  fi
  local -a parts
  parts=("${(@s:/:)cwd}")
  local i
  for (( i=1; i < ${#parts}; i++ )); do
    part=$parts[i]
    if [[ $part != '~' && -n $part ]]; then
      parts[i]=${part[1]}
      [[ $part == .* ]] && parts[i]=${part[1,2]}
    fi
  done
  cwd=${(j:/:)parts}
  # Escape prompt percent sequences from paths and branch names.
  cwd=${cwd//\%/%%}
  PROMPT=''
  if [[ ${NASCENT_BOXFISH_VI:-0} == 1 ]]; then
    case ${KEYMAP:-viins} in
      vicmd) PROMPT+='%K{red} %k' ;;
      visual) PROMPT+='%K{yellow} %k' ;;
      *) PROMPT+='%K{green} %k' ;;
    esac
  fi
  (( last_status == 0 )) || PROMPT+='%B%F{white}%K{red} ! %k%f%b'
  PROMPT+="%F{black}%K{blue} $cwd %k%f"
  if branch=$(command git symbolic-ref --quiet --short HEAD 2>/dev/null); then
    dirty=$(command git status --porcelain --ignore-submodules=dirty 2>/dev/null)
    branch=${branch//\%/%%}
    if [[ -n $dirty ]]; then
      PROMPT+="%F{black}%K{yellow} $branch %k%f"
    else
      PROMPT+="%F{black}%K{green} $branch %k%f"
    fi
  fi
  PROMPT+=' '
  RPROMPT=''
}
_nascent_boxfish_keymap() {
  # Repaint only the mode cell; preserve the previous command's error status.
  [[ ${NASCENT_BOXFISH_VI:-0} == 1 ]] || return 0
  local color=green
  [[ $KEYMAP == vicmd ]] && color=red
  (( ${REGION_ACTIVE:-0} > 0 )) && color=yellow
  [[ $PROMPT == "%K{$color} %k"* ]] && return 0
  PROMPT="%K{$color} %k${PROMPT#* %k}"
  zle reset-prompt
}
add-zsh-hook precmd _nascent_boxfish_precmd
add-zle-hook-widget keymap-select _nascent_boxfish_keymap
add-zle-hook-widget line-pre-redraw _nascent_boxfish_keymap
