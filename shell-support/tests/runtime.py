"""Temporary-HOME tests; no host configuration or accounts are changed."""
import json
import os
import pty
from pathlib import Path
import select
import signal
import subprocess
import tempfile
import time
import unittest

ASSETS = Path(__file__).resolve().parents[1] / "assets"
PACKAGES = json.loads(Path(os.environ["NASCENT_SHELL_PACKAGES"]).read_text())
ZSH, OMZ, SUGGEST, HIGHLIGHT, _ = [p["outputs"]["out"] for p in PACKAGES]


class Runtime(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.env = dict(os.environ, HOME=str(self.home), ZDOTDIR=str(self.home),
                        NASCENT_ZSH_SEED_DIR=str(ASSETS), TERM="xterm-256color",
                        LINES="24", COLUMNS="100")
        self.env.pop("ZSH", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_zsh(self, code, interactive=False):
        result = subprocess.run([f"{ZSH}/bin/zsh", "-df" + ("i" if interactive else ""), "-c", code],
                                cwd=self.home, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_seed_keeps_edits_and_umask(self):
        seed = f'source "{ASSETS}/seed.zsh"'
        self.run_zsh(f'umask 022; {seed}; [[ $(umask) == 022 ]]')
        rc = self.home / ".zshrc"
        theme = self.home / ".config/nascentos/zsh/boxfish.zsh-theme"
        self.assertTrue(rc.is_file() and theme.is_file())
        self.assertEqual(rc.stat().st_uid, os.getuid())
        self.assertEqual(rc.stat().st_mode & 0o777, 0o600)
        rc.write_text("# personal\n")
        theme.write_text("# edited theme\n")
        self.run_zsh(seed)
        self.assertEqual(rc.read_text(), "# personal\n")
        self.assertEqual(theme.read_text(), "# edited theme\n")

    def test_seed_preserves_dangling_link(self):
        (self.home / ".zshrc").symlink_to(self.home / "not-created")
        self.run_zsh(f'source "{ASSETS}/seed.zsh"')
        self.assertTrue((self.home / ".zshrc").is_symlink())
        self.assertFalse((self.home / "not-created").exists())

    def test_real_fresh_interactive_startup_before_newuser(self):
        binary = os.environ.get("NASCENT_STARTUP_ZSH")
        self.assertTrue(binary and Path(binary).is_file(),
                        "Environment failure: build the native startup fixture using shell-support/tests/check")
        # Unlike the other tests, do not pass -d/-f, source seed manually, or
        # pre-create a .zshenv: exercise the binary's actual global startup path.
        pid, terminal = pty.fork()
        if pid == 0:
            os.chdir(self.home)
            os.execve(binary, [binary, "-il"], self.env)
        output = b""
        status = None
        try:
            os.write(terminal, b'print -r -- NASCENT_FRESH_STARTUP_READY; '
                     b'(( $+functions[_nascent_boxfish_precmd] )) || exit 17; exit 0\n')
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if select.select([terminal], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(terminal, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output += chunk
                waited, current = os.waitpid(pid, os.WNOHANG)
                if waited:
                    status = current
                    break
            # PTY EOF can precede waitpid reporting the exiting shell by a few
            # milliseconds; allow that final transition within the same timeout.
            while status is None and time.monotonic() < deadline:
                waited, current = os.waitpid(pid, os.WNOHANG)
                if waited:
                    status = current
                else:
                    time.sleep(0.01)
            self.assertIsNotNone(status, output.decode(errors="replace"))
            self.assertEqual(os.waitstatus_to_exitcode(status), 0, output.decode(errors="replace"))
            self.assertIn(b"NASCENT_FRESH_STARTUP_READY", output)
            self.assertNotIn(b"configuration function for new users", output)
            self.assertNotIn(b"zsh-newuser-install", output)
            self.assertTrue((self.home / ".zshrc").is_file())
            self.assertTrue((self.home / ".config/nascentos/zsh/boxfish.zsh-theme").is_file())
            print("Fresh native interactive login reached Boxfish without new-user wizard")
        finally:
            if status is None:
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
            os.close(terminal)

    def test_native_startup_negative_control_reaches_newuser(self):
        binary = os.environ.get("NASCENT_STARTUP_ZSH")
        self.assertTrue(binary and Path(binary).is_file(), "Native startup fixture is required")
        pid, terminal = pty.fork()
        if pid == 0:
            os.chdir(self.home)
            os.execve(binary, [binary, "-il"], {**self.env, "NASCENT_STARTUP_TEST_SKIP_SEED": "1"})
        output = b""
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if select.select([terminal], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(terminal, 65536)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output += chunk
                    if b"configuration function for new users" in output:
                        break
            self.assertIn(b"configuration function for new users", output,
                          output.decode(errors="replace"))
            self.assertFalse((self.home / ".zshrc").exists())
        finally:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            os.close(terminal)

    def test_prompt_states_and_literal_path(self):
        repo = self.home / "project%F{red}"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
        prefix = f'source "{ASSETS}/boxfish.zsh-theme"; cd "{repo}"; '
        clean = self.run_zsh(prefix + 'true; _nascent_boxfish_precmd; print -r -- $PROMPT')
        self.assertIn("%K{green} main ", clean)
        self.assertIn("~/project%%F{red}", clean)
        rendered = self.run_zsh(prefix + 'true; _nascent_boxfish_precmd; print -P -- "$PROMPT"')
        self.assertIn("\x1b[44m", rendered)
        self.assertIn("\x1b[42m", rendered)
        self.assertIn("~/project%F{red}", rendered)
        print("Boxfish clean ANSI rendering:", repr(rendered))
        (repo / "new").write_text("dirty")
        dirty = self.run_zsh(prefix + 'false; _nascent_boxfish_precmd; print -r -- $PROMPT')
        self.assertIn("%K{yellow} main ", dirty)
        self.assertIn(" ! ", dirty)
        self.assertNotIn(" ! ", clean)

    def test_prompt_expansion_cannot_execute_path(self):
        path = self.home / "$(touch injected)"
        path.mkdir()
        self.run_zsh(f'source "{ASSETS}/boxfish.zsh-theme"; cd \'{path}\'; true; '
                     '_nascent_boxfish_precmd; print -P -- "$PROMPT"')
        self.assertFalse((path / "injected").exists())

    def test_vi_mode_cell_preserves_prompt(self):
        output = self.run_zsh(f'source "{ASSETS}/boxfish.zsh-theme"; NASCENT_BOXFISH_VI=1; '
                               'KEYMAP=viins; false; _nascent_boxfish_precmd; '
                               'function zle() { :; }; KEYMAP=vicmd; _nascent_boxfish_keymap; '
                               'print -r -- $PROMPT')
        self.assertTrue(output.startswith("%K{red} %k"))
        self.assertIn(" ! ", output)
        self.assertIn("%K{blue}", output)

    def test_official_plugins_load_and_suggest(self):
        self.run_zsh(f'''
          export ZSH={OMZ}/share/oh-my-zsh
          ZSH_CACHE_DIR=$HOME/.cache/oh-my-zsh
          HISTSIZE=100
          SAVEHIST=100
          mkdir -p "$ZSH_CACHE_DIR"
          plugins=(git)
          ZSH_THEME=''
          zstyle ':omz:update' mode disabled
          source "$ZSH/oh-my-zsh.sh"
          source {SUGGEST}/share/zsh-autosuggestions/zsh-autosuggestions.zsh
          source {HIGHLIGHT}/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
          source "{ASSETS}/boxfish.zsh-theme"
          (( $+functions[_zsh_highlight] && $+functions[_zsh_autosuggest_start] )) || exit 11
          print -s 'echo nascent-suggestion'
          print -s 'pwd' # Zsh excludes the current event from $history.
          _zsh_autosuggest_strategy_history 'echo nasc'
          [[ $suggestion == 'echo nascent-suggestion' ]] || exit 12
          (( $+functions[_git] )) || exit 13
        ''', interactive=True)


if __name__ == "__main__":
    unittest.main()
