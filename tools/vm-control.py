#!/usr/bin/env python3
"""QMP screen/input controls for the task-local disposable installer VM."""
import argparse
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import time

ROOT = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
INSTANCE = os.environ.get('NASCENT_VM_INSTANCE', 'install-test')
if INSTANCE not in ('install-test', 'install-verify'):
    raise ValueError('NASCENT_VM_INSTANCE must be install-test or install-verify')
STATE = ROOT / '.vm' / INSTANCE


class QMP:
    def __enter__(self):
        self.socket = socket.socket(socket.AF_UNIX)
        self.socket.settimeout(15)
        self.socket.connect(str(STATE / 'qmp.sock'))
        self.file = self.socket.makefile('rwb', buffering=0)
        json.loads(self.file.readline())
        self.call('qmp_capabilities')
        return self

    def __exit__(self, *args):
        self.file.close()
        self.socket.close()

    def call(self, command, arguments=None):
        self.file.write((json.dumps({'execute': command, 'arguments': arguments or {}}) + '\n').encode())
        while True:
            result = json.loads(self.file.readline())
            if 'error' in result:
                raise RuntimeError(result['error'])
            if 'return' in result:
                return result['return']

    def key(self, keys):
        result = self.call('human-monitor-command', {'command-line': 'sendkey ' + keys + ' 20'})
        # QMP acknowledges before releasing the keys; wait before another chord.
        time.sleep(0.08)
        return result

    def screenshot(self, path):
        self.call('screendump', {'filename': str(path), 'format': 'png'})
        with path.open('rb') as source:
            header = source.read(24)
        return struct.unpack('>II', header[16:24])


def type_text(qmp, text):
    plain = {' ': 'spc', '\n': 'ret', '.': 'dot', '/': 'slash', '-': 'minus',
             '=': 'equal', ',': 'comma', ';': 'semicolon', "'": 'apostrophe',
             '[': 'bracket_left', ']': 'bracket_right', '\\': 'backslash', '`': 'grave_accent'}
    shifted = dict(zip('!@#$%^&*()_+{}:"<>?~|',
                       ['1','2','3','4','5','6','7','8','9','0','minus','equal','bracket_left',
                        'bracket_right','semicolon','apostrophe','comma','dot','slash','grave_accent','backslash']))
    for character in text:
        if character in plain:
            key = plain[character]
        elif character in shifted:
            key = 'shift-' + shifted[character]
        elif character.isascii() and character.isalnum():
            key = ('shift-' if character.isupper() else '') + character.lower()
        else:
            raise ValueError('Unsupported input character: ' + repr(character))
        qmp.key(key)
        time.sleep(0.035)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('status')
    sub.add_parser('screenshot').add_argument('name', nargs='?', default='screen.png')
    sub.add_parser('key').add_argument('keys')
    sub.add_parser('type').add_argument('text')
    click = sub.add_parser('click')
    click.add_argument('x', type=int)
    click.add_argument('y', type=int)
    args = parser.parse_args()
    with QMP() as qmp:
        if args.action == 'status':
            print(json.dumps(qmp.call('query-status')))
        elif args.action == 'screenshot':
            path = STATE / Path(args.name).name
            print(path, qmp.screenshot(path))
        elif args.action == 'key':
            if any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in args.keys):
                raise ValueError('Use QEMU key names joined by hyphens')
            qmp.key(args.keys)
        elif args.action == 'type':
            type_text(qmp, args.text)
        elif args.action == 'click':
            width, height = qmp.screenshot(STATE / 'last-screen.png')
            if not (0 <= args.x < width and 0 <= args.y < height):
                raise ValueError('Click outside display')
            qmp.call('input-send-event', {'events': [
                {'type': 'abs', 'data': {'axis': 'x', 'value': round(args.x * 32767 / (width - 1))}},
                {'type': 'abs', 'data': {'axis': 'y', 'value': round(args.y * 32767 / (height - 1))}}]})
            # XWayland must process pointer motion before the click focuses a widget.
            time.sleep(0.8)
            qmp.call('input-send-event', {'events': [
                {'type': 'btn', 'data': {'down': True, 'button': 'left'}}]})
            # Separate sync frames so a Wayland client observes the button press.
            time.sleep(0.1)
            qmp.call('input-send-event', {'events': [
                {'type': 'btn', 'data': {'down': False, 'button': 'left'}}]})
            time.sleep(0.35)


if __name__ == '__main__':
    main()
