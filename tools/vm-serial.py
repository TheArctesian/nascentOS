#!/usr/bin/env python3
"""Run a console command only in the separate disposable verification VM."""
import argparse
from pathlib import Path
import re
import socket
import subprocess
import time
import uuid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--timeout', type=float, default=30)
parser.add_argument('command')
args = parser.parse_args()
root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
# Deliberately cannot connect to the user's interactive install-test session.
path = root / '.vm/install-verify/serial.sock'
marker = 'NASCENT_VM_DONE_' + uuid.uuid4().hex
payload = args.command + '; nascent_vm_exit=$?; printf "\\n' + marker + ':%s\\n" "$nascent_vm_exit"\n'
pattern = re.compile(rb'(?:\r*\n)' + marker.encode() + rb':([0-9]+)\r*\n')
deadline = time.monotonic() + args.timeout
output = b''
match = None
with socket.socket(socket.AF_UNIX) as connection:
    connection.connect(str(path))
    connection.settimeout(1)
    connection.sendall(payload.encode())
    while time.monotonic() < deadline:
        try:
            block = connection.recv(65536)
        except TimeoutError:
            continue
        if not block:
            break
        output += block
        match = pattern.search(output)
        if match:
            break
    else:
        match = None

text = output.decode(errors='replace')
text = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', '', text)
text = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)
print(text)
if match is None:
    raise SystemExit('Timed out before the guest returned a command exit status')
raise SystemExit(int(match.group(1)))
