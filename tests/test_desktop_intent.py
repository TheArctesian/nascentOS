import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('intent', Path(os.environ['NASCENT_SOURCE']) / 'lib/desktop_intent.py')
intent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(intent)


class DesktopIntentTests(unittest.TestCase):
    def test_phrases(self):
        self.assertEqual(intent.route('Pull up my browser!'), {'action': 'browser.open'})
        self.assertEqual(intent.route('close my browser'), {'action': 'browser.close'})
        self.assertEqual(intent.route('open terminal; rm -rf /'), {'action': 'none'})

    def test_reject_model_code_and_extra_arguments(self):
        for value in ({'action': 'exec', 'command': 'false'}, {'action': 'browser.close', 'window': '0x1'}, {'action': []}, 'browser.open'):
            with self.assertRaises(ValueError):
                intent.validate(value)

    def test_open_uses_fixed_argv(self):
        calls = []
        intent.execute({'action': 'browser.open'}, launch=lambda *args, **kwargs: calls.append(args[0]))
        self.assertEqual(calls, [['nascent-browser']])

    def test_selected_chromium_excludes_installed_firefox(self):
        with tempfile.TemporaryDirectory() as temporary:
            configuration = Path(temporary) / 'software-runtime.json'
            configuration.write_text(json.dumps({'browser': 'chromium'}))
            clients = [{'class': 'firefox', 'address': '0x1'}, {'class': 'chromium', 'address': '0x2'}]
            with patch.object(intent, 'BROWSER_CONFIG', configuration):
                windows = intent.browser_windows(run=lambda *args, **kwargs: SimpleNamespace(stdout=json.dumps(clients)))
            self.assertEqual(windows, [clients[1]])

    def test_no_selection_uses_only_known_desktop_default(self):
        with tempfile.TemporaryDirectory() as temporary:
            configuration = Path(temporary) / 'software-runtime.json'
            configuration.write_text(json.dumps({'browser': None}))
            calls = []
            def run(args, **kwargs):
                calls.append(args)
                return SimpleNamespace(stdout='chromium.desktop' if args[0] == 'xdg-settings' else json.dumps([
                    {'class': 'chromium', 'address': '0x2'}, {'class': 'firefox', 'address': '0x1'}]))
            with patch.object(intent, 'BROWSER_CONFIG', configuration):
                self.assertEqual(intent.browser_windows(run), [{'class': 'chromium', 'address': '0x2'}])
            self.assertEqual(calls[0], ['xdg-settings', 'get', 'default-web-browser'])
            with patch.object(intent, 'BROWSER_CONFIG', configuration):
                with self.assertRaises(ValueError):
                    intent.browser_windows(run=lambda *args, **kwargs: SimpleNamespace(stdout='unknown.desktop'))

    def test_targeted_normal_close(self):
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(stdout=json.dumps([{'class': 'firefox', 'address': '0xabc'}, {'class': 'kitty', 'address': '0xdef'}]))
        intent.execute({'action': 'browser.close'}, run=run)
        self.assertEqual(calls[-1], ['hyprctl', 'dispatch', 'hl.dsp.window.close({window="address:0xabc"})'])

    def test_ambiguity_and_foreign_window_do_not_dispatch(self):
        for windows, selected in (([], None), ([{'class': 'firefox', 'address': '0x1'}, {'class': 'firefox', 'address': '0x2'}], None), ([{'class': 'kitty', 'address': '0x3'}], '0x3')):
            calls = []
            def run(args, **kwargs):
                calls.append(args)
                return SimpleNamespace(stdout=json.dumps(windows))
            with self.assertRaises(ValueError):
                intent.execute({'action': 'browser.close'}, selected, run=run)
            self.assertEqual(len(calls), 1)

    def test_address_injection_rejected_before_compositor(self):
        with self.assertRaises(ValueError):
            intent.execute({'action': 'browser.close'}, '0x1"});os.execute("false")')

    def test_explicit_selection(self):
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            return SimpleNamespace(stdout=json.dumps([{'class': 'firefox', 'address': '0x1'}, {'class': 'firefox', 'address': '0x2'}]))
        intent.execute({'action': 'browser.close'}, '0x2', run=run)
        self.assertIn('address:0x2', calls[-1][-1])

    def test_local_model_response_validation(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit): return json.dumps({'message': {'content': '{"action":"exec"}'}}).encode()
        with patch.object(intent.urllib.request, 'build_opener') as mocked:
            mocked.return_value.open.return_value = Response()
            with self.assertRaises(ValueError): intent.route('open browser', 'local-model')
            request = mocked.return_value.open.call_args.args[0]
            self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/chat')


if __name__ == '__main__':
    unittest.main()
