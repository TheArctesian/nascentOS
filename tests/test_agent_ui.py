"""Exercise graphical agent routing without a desktop or provider calls."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(os.environ.get('NASCENT_SOURCE', Path(__file__).resolve().parents[1]))


class AgentUITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.mock_bin = self.root / 'bin'
        self.mock_bin.mkdir()
        self.log = self.root / 'calls.jsonl'
        self.config = self.root / 'config/nascentos'
        self.adapters = self.config / 'agents'
        self.adapters.mkdir(parents=True)
        self.env = dict(os.environ, HOME=str(self.root), XDG_CONFIG_HOME=str(self.root / 'config'),
                        PATH=str(self.mock_bin) + os.pathsep + str(SOURCE / 'bin') + os.pathsep + os.environ['PATH'],
                        UI_LOG=str(self.log), UI_CHOICE='', UI_CANCEL='0')
        for command in ('zenity', 'nascent-launch'):
            path = self.mock_bin / command
            path.write_text(f'#!{sys.executable}\n' + '''import json, os, sys
from pathlib import Path
with Path(os.environ['UI_LOG']).open('a') as output:
    output.write(json.dumps([Path(sys.argv[0]).name] + sys.argv[1:]) + '\\n')
if Path(sys.argv[0]).name == 'zenity' and '--list' in sys.argv:
    if os.environ['UI_CANCEL'] == '1':
        sys.exit(1)
    print(os.environ['UI_CHOICE'])
''')
            path.chmod(0o755)

    def adapter(self, name, executable=True):
        path = self.adapters / name
        path.write_text('#!/usr/bin/env bash\necho "Provider must not run during UI tests" >&2\nexit 99\n')
        path.chmod(0o755 if executable else 0o644)

    def run_ui(self):
        result = subprocess.run(['bash', str(SOURCE / 'bin/nascent-agent-ui')], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_fresh_state_shows_guidance_without_terminal_or_paths(self):
        calls = self.run_ui()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0:2], ['zenity', '--info'])
        self.assertIn('No agent is configured', ' '.join(calls[0]))
        self.assertNotIn(str(self.root), ' '.join(calls[0]))
        self.assertFalse((self.config / 'agent').exists())

    def test_non_executable_adapter_is_not_available(self):
        self.adapter('unconfigured', executable=False)
        calls = self.run_ui()
        self.assertEqual(calls[0][0:2], ['zenity', '--info'])
        self.assertEqual(len(calls), 1)

    def test_cancel_does_not_select_or_open_terminal(self):
        self.adapter('local')
        self.env['UI_CANCEL'] = '1'
        calls = self.run_ui()
        self.assertEqual(calls[0][0:2], ['zenity', '--list'])
        self.assertEqual(len(calls), 1)
        self.assertFalse((self.config / 'agent').exists())

    def test_valid_current_launches_normal_cli_in_terminal(self):
        self.adapter('local')
        (self.config / 'agent').write_text('local\n')
        self.assertEqual(self.run_ui(), [['nascent-launch', 'terminal', 'nascent-agent', 'run']])

    def test_no_selection_offers_available_adapters_and_saves_choice(self):
        self.adapter('local')
        self.env['UI_CHOICE'] = 'local'
        calls = self.run_ui()
        self.assertEqual(calls[0][0:2], ['zenity', '--list'])
        self.assertEqual(calls[-1], ['nascent-launch', 'terminal', 'nascent-agent', 'run'])
        self.assertEqual((self.config / 'agent').read_text(), 'local\n')

    def test_missing_selected_adapter_can_be_replaced(self):
        self.adapter('replacement')
        (self.config / 'agent').write_text('removed\n')
        self.env['UI_CHOICE'] = 'replacement'
        calls = self.run_ui()
        self.assertEqual(calls[0][0:2], ['zenity', '--list'])
        self.assertEqual(calls[-1][0], 'nascent-launch')
        self.assertEqual((self.config / 'agent').read_text(), 'replacement\n')

    def test_unavailable_dialog_output_is_rejected(self):
        self.adapter('local')
        self.env['UI_CHOICE'] = 'other; touch bad'
        calls = self.run_ui()
        self.assertEqual([call[0] for call in calls], ['zenity', 'zenity'])
        self.assertIn('--info', calls[-1])
        self.assertFalse((self.config / 'agent').exists())


if __name__ == '__main__':
    unittest.main()
