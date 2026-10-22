"""Live-session installer entry: review hardware, elevate, and keep failures visible."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import textwrap

from hardware import scan

TITLE = 'Install nascentOS'


@contextmanager
def root_display_access(log):
    """Temporarily admit only the local root user to this live XWayland server."""
    result = subprocess.run(['xhost'], capture_output=True, text=True, check=False)
    log.write(result.stdout + result.stderr)
    log.flush()
    if result.returncode != 0:
        raise ValueError('Could not inspect XWayland display access; see the launch log.')
    existing = any(line.strip() == 'SI:localuser:root' for line in result.stdout.splitlines())
    added = False
    try:
        if not existing:
            subprocess.run(['xhost', '+SI:localuser:root'], stdout=log, stderr=log, check=True)
            added = True
        log.flush()
        yield
    finally:
        if added:
            try:
                subprocess.run(['xhost', '-SI:localuser:root'], stdout=log, stderr=log, check=True)
            except (OSError, subprocess.CalledProcessError) as error:
                log.write('Failed to revoke temporary local-root display access: ' + str(error) + '\n')
                raise ValueError('Could not revoke temporary local-root display access. '
                                 'Run xhost -SI:localuser:root in the live session.') from error
            finally:
                log.flush()


def dialog(arguments, **kwargs):
    # GTK's Cairo renderer avoids repeated unsupported Vulkan probes in software VMs.
    return subprocess.run(['zenity', *arguments], env={**os.environ, 'GSK_RENDERER': 'cairo'}, **kwargs)


def focus_existing():
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        return False
    try:
        result = subprocess.run(['hyprctl', '-j', 'clients'], capture_output=True, text=True, check=True)
        clients = json.loads(result.stdout)
        for client in clients:
            app = str(client.get('class', '')).lower()
            title = str(client.get('title', ''))
            if ('calamares' in app or (app == 'zenity' and title.startswith(TITLE))):
                address = str(client.get('address', ''))
                if re.fullmatch(r'0x[0-9a-fA-F]+', address):
                    subprocess.run(['hyprctl', 'dispatch',
                                    'hl.dsp.focus({window="address:' + address + '"})'],
                                   check=True, capture_output=True)
                    return True
    except (OSError, ValueError, subprocess.CalledProcessError):
        pass
    return False


def summary(report):
    machine = ' '.join(filter(None, (report['manufacturer'], report['model']))) or 'Unknown computer'
    devices = ', '.join(gpu['vendor'] + ':' + gpu['device'] for gpu in report['gpus']) or 'No PCI display device'
    lines = [machine, f"{report['system'] or 'Unsupported architecture'} · {report['firmware']}",
             'Graphics: ' + devices, '',
             'Choose the graphics profile. Storage, boot and your user account are configured in the next steps.',
             'No disk changes happen during this review.']
    if report['warnings']:
        lines.extend(['', 'Hardware notes:', *report['warnings']])
    return '\n'.join(textwrap.fill(line, width=76) if line else '' for line in lines)


def review_software(picker, recorder, log):
    if not picker or not recorder:
        raise ValueError('The software picker is missing from this installer package.')
    choices = subprocess.run([picker], stdout=subprocess.PIPE,
                             stderr=log, text=True, check=False)
    if choices.returncode == 1:
        return False
    if choices.returncode != 0:
        raise ValueError('Could not open the software selection window.')
    if len(choices.stdout) > 16384:
        raise ValueError('Software selection is too large.')
    subprocess.run(['/run/wrappers/bin/pkexec', recorder],
                   input=choices.stdout, text=True, stdout=log, stderr=log, check=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer', required=True)
    parser.add_argument('--record-helper', required=True)
    parser.add_argument('--software-picker')
    parser.add_argument('--software-recorder')
    args = parser.parse_args()
    state = Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local/state'))) / 'nascentos'
    state.mkdir(parents=True, exist_ok=True)
    logfile = state / 'installer-launch.log'
    lock = (state / 'installer-launch.lock').open('w')
    if focus_existing():
        return 0
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        dialog(['--info', '--no-markup', '--title=' + TITLE,
                '--text=The installer is already opening. Please wait for its hardware review or installer window.'])
        return 0
    with logfile.open('a') as log:
        try:
            report = scan()
            if not report['system'] or report['family'] != 'generic':
                raise ValueError('This platform needs a supported boot/kernel configuration before installation.\n' + summary(report))
            recommended = report['recommended']
            choice = dialog(['--list', '--radiolist', '--no-markup', '--width=760', '--height=500',
                             '--title=' + TITLE + ' — hardware review', '--text=' + summary(report),
                             '--ok-label=Continue', '--cancel-label=Cancel', '--print-column=2',
                             '--column=Select', '--column=Profile', '--column=Graphics support',
                             str(recommended == 'generic').upper(), 'generic', 'Standard kernel and Mesa',
                             str(recommended == 'nvidia-open').upper(), 'nvidia-open', 'Modern NVIDIA (unfree driver)'],
                            capture_output=True, text=True)
            log.write(choice.stderr)
            log.flush()
            if choice.returncode == 1:
                return 0
            if choice.returncode != 0:
                raise ValueError('Could not display the hardware review.')
            profile = choice.stdout.strip()
            if profile not in ('generic', 'nvidia-open'):
                raise ValueError('Choose a graphics profile before continuing.')
            if profile == 'nvidia-open':
                confirmation = dialog(['--question', '--no-markup', '--title=' + TITLE,
                                       '--text=NVIDIA open requires a supported Turing-or-newer GPU and enables the unfree NVIDIA driver. Continue with this profile?',
                                       '--ok-label=Use NVIDIA', '--cancel-label=Cancel'])
                if confirmation.returncode != 0:
                    return 0
            subprocess.run(['/run/wrappers/bin/pkexec', sys.executable, args.record_helper,
                            'record', '--profile', profile], stdout=log, stderr=log, check=True)
            if not review_software(args.software_picker, args.software_recorder, log):
                return 0
            # Invoke the packaged program directly so its allow_gui polkit policy
            # preserves DISPLAY/XAUTHORITY. Its Qt wrapper explicitly uses XWayland.
            with root_display_access(log):
                subprocess.run(['/run/wrappers/bin/pkexec', args.installer],
                               stdout=log, stderr=log, check=True)
            return 0
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            log.write(str(error) + '\n')
            log.flush()
            details = '\n'.join(textwrap.fill(line, 80) for line in logfile.read_text(errors='replace').splitlines()[-8:])
            dialog(['--error', '--no-markup', '--width=700', '--title=' + TITLE,
                    '--text=' + textwrap.fill(str(error), 80) + '\n\nYou can reopen Install nascentOS and try again.\n'
                    + 'Launch log: ' + str(logfile) + '\n\n' + details])
            return 1


if __name__ == '__main__':
    sys.exit(main())
