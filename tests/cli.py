"""Exercise runtime selection, ownership, and argument forwarding without a desktop."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(os.environ['NASCENT_SOURCE'])
bash_shebang = '#!' + shutil.which('bash') + '\n'
with tempfile.TemporaryDirectory() as temporary:
    home = Path(temporary)
    data = home / 'data'
    for name in ('nord', 'tokyo-night'):
        bundle = data / 'themes' / name
        bundle.mkdir(parents=True)
        for filename in ('kitty.conf', 'waybar.css', 'fuzzel.ini', 'mako.conf', 'hyprland.lua', 'hyprlock.conf'):
            (bundle / filename).write_text(name)
    (data / 'nvim').mkdir()
    (data / 'nvim/init.lua').write_text('-- original')
    target = data / 'read-only-color'
    target.write_text('nord')
    target.chmod(0o444)
    (data / 'themes/nord/kitty.conf').unlink()
    (data / 'themes/nord/kitty.conf').symlink_to(target)
    env = {**os.environ, 'HOME': str(home), 'XDG_CONFIG_HOME': str(home / 'config'),
           'NASCENT_DATA_DIR': str(data), 'PATH': str(root / 'bin') + ':' + os.environ['PATH']}
    env.pop('HYPRLAND_INSTANCE_SIGNATURE', None)
    env.pop('WAYLAND_DISPLAY', None)

    def run(*args, ok=True):
        result = subprocess.run(['bash', str(root / 'bin' / 'nascent'), *args], env=env,
                                capture_output=True, text=True)
        assert (result.returncode == 0) == ok, (args, result.stdout, result.stderr)
        return result.stdout.strip()

    assert run('theme', 'current') == 'nord'
    run('theme', 'init')
    config = home / 'config/nascentos'
    personal = config / 'themes/nord/kitty.conf'
    assert not personal.is_symlink()
    assert personal.stat().st_mode & 0o200
    personal.write_text('personal edits')
    run('theme', 'init')
    assert personal.read_text() == 'personal edits'
    stable_path = run('theme', 'path')
    run('theme', 'set', 'tokyo-night')
    assert run('theme', 'current') == 'tokyo-night'
    assert run('theme', 'path') == stable_path
    assert (Path(stable_path) / 'kitty.conf').read_text() == 'tokyo-night'
    run('theme', 'set', '../invalid', ok=False)
    assert run('theme', 'current') == 'tokyo-night'
    run('theme', 'set', 'nord')
    assert personal.read_text() == 'personal edits'
    run('editor', 'init')
    nvim = home / 'config/nvim/init.lua'
    assert nvim.read_text() == '-- original'
    nvim.write_text('-- personal')
    run('editor', 'init')
    assert nvim.read_text() == '-- personal'
    assert run('agent', 'current') == ''
    run('agent', 'run', ok=False)
    adapters = config / 'agents'
    shipped = data / 'agent-adapters'
    shipped.mkdir()
    shipped_codex = shipped / 'codex'
    shipped_codex.write_text(bash_shebang + 'exec codex "$@"\n')
    shipped_codex.chmod(0o444)
    # An unselected/unshipped tool is never manufactured by init.
    run('agent', 'init')
    seeded_codex = adapters / 'codex'
    assert seeded_codex.read_text() == shipped_codex.read_text()
    assert not seeded_codex.is_symlink()
    assert seeded_codex.stat().st_mode & 0o200 and seeded_codex.stat().st_mode & 0o100
    assert run('agent', 'list') == 'codex'
    assert run('agent', 'current') == ''
    seeded_codex.write_text(bash_shebang + 'printf "personal adapter\\n"\n')
    (shipped / 'opencode').write_text(bash_shebang + 'exec opencode "$@"\n')
    (adapters / 'opencode').symlink_to(adapters / 'missing-personal-target')
    run('agent', 'init')
    assert 'personal adapter' in seeded_codex.read_text()
    assert (adapters / 'opencode').is_symlink()
    assert os.readlink(adapters / 'opencode') == str(adapters / 'missing-personal-target')
    # Adapter commands resolve the normal user PATH and forward literal arguments.
    provider_bin = home / 'provider-fixtures'
    provider_bin.mkdir()
    provider = provider_bin / 'codex'
    provider.write_text(bash_shebang + 'printf "%s\\n" "$@"\n')
    provider.chmod(0o755)
    env['PATH'] = str(provider_bin) + ':' + env['PATH']
    seeded_codex.unlink()
    run('agent', 'init')
    run('agent', 'set', 'codex')
    assert run('agent', 'run', 'literal space', '$(false)', '--flag') == 'literal space\n$(false)\n--flag'
    run('agent', 'init')
    assert run('agent', 'current') == 'codex'
    adapter = adapters / 'test'
    adapter.write_text(bash_shebang + 'printf "%s\\n" "$@"\n')
    adapter.chmod(0o755)
    run('agent', 'set', 'test')
    assert run('agent', 'run', 'a b', '$(false)', '--flag') == 'a b\n$(false)\n--flag'
    run('agent', 'set', '../bad', ok=False)
    run('agent', 'set', 'missing', ok=False)
    assert run('agent', 'current') == 'test'
    image = home / 'my wallpaper.png'
    image.write_text('fixture')
    run('wallpaper', 'set', str(image))
    assert (config / 'wallpaper').resolve() == image
    run('wallpaper', 'set', str(home / 'missing'), ok=False)
    run('ai', 'transcribe', str(home / 'missing'), str(image), ok=False)
print('CLI ownership, theme persistence, argument forwarding and input checks passed.')
