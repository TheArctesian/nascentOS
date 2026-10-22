"""Small checked patch against the pinned NixOS Calamares extension."""
import ast
from pathlib import Path
import sys


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Pinned Calamares extension changed: missing/ambiguous patch anchor')
    return text.replace(before, after)


def patch(text):
    text = replace_once(text, 'import re\n', 'import re\nimport sys\nsys.path.insert(0, os.path.dirname(__file__))\nfrom nascent_install import prepare\n')
    anchor = '    libcalamares.utils.host_env_process_output(["cp", "/dev/stdin", config], None, cfg)'
    text = replace_once(text, anchor, anchor + '''
    try:
        prepare(root_mount_point, config)
    except (OSError, ValueError, KeyError) as error:
        return (_("nascentOS configuration failed"), str(error))
''')
    text = replace_once(text, '            "nixos-install",\n', '            "nixos-install",\n            "--flake",\n            root_mount_point + "/etc/nixos#nascent",\n')
    # The nascentOS module supplies portable audio; don't inherit the stock desktop's 32-bit assumption.
    text = replace_once(text, '        cfg += cfgmisc\n', '        cfg += ""\n')
    text = replace_once(text,
        '  services.displayManager.autoLogin.enable = true;\n  services.displayManager.autoLogin.user = "@@username@@";',
        '  services.greetd.settings.initial_session = {\n    command = "nascent-session";\n    user = "@@username@@";\n  };')
    # The software picker owns browser selection on the installed system.
    text = replace_once(text, '  programs.firefox.enable = true;',
                        '  # Browser packages are selected in nascent-software.nix.')
    ast.parse(text)
    return text


if __name__ == '__main__':
    path = Path(sys.argv[1]) / 'modules/nixos/main.py'
    path.write_text(patch(path.read_text()))
