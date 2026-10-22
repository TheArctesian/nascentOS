"""Offline launch safety checks; no X server, privileges, or installer is used."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import call, patch

SOURCE = Path(os.environ.get('NASCENT_SOURCE', Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('install_launcher', SOURCE / 'lib/install_launcher.py')
launcher = importlib.util.module_from_spec(spec)
with patch.object(sys, 'path', [str(SOURCE / 'lib'), *sys.path]):
    spec.loader.exec_module(launcher)


def result(stdout='', stderr='', returncode=0):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


class SoftwareReviewTests(unittest.TestCase):
    def test_cancel_does_not_elevate_or_record(self):
        with patch.object(launcher.subprocess, 'run', return_value=result(returncode=1)) as run:
            self.assertFalse(launcher.review_software('/picker', '/recorder', io.StringIO()))
        self.assertEqual(run.call_count, 1)

    def test_failed_or_oversized_picker_never_elevates(self):
        for output in (result(returncode=2), result(stdout='x' * 16385)):
            with patch.object(launcher.subprocess, 'run', return_value=output) as run:
                with self.assertRaises(ValueError):
                    launcher.review_software('/picker', '/recorder', io.StringIO())
            self.assertEqual(run.call_count, 1)

    def test_exact_json_uses_privileged_recorder_stdin_and_failure_propagates(self):
        value = '{"selected":["neovim"],"acceptedProprietary":[]}'
        failure = subprocess.CalledProcessError(1, ['/recorder'])
        log = io.StringIO()
        with patch.object(launcher.subprocess, 'run', side_effect=[result(stdout=value), failure]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                launcher.review_software('/picker', '/recorder', log)
        self.assertEqual(run.call_args_list[-1], call(
            ['/run/wrappers/bin/pkexec', '/recorder'], input=value,
            text=True, stdout=log, stderr=log, check=True))


class RootDisplayAccessTests(unittest.TestCase):
    def test_preserves_existing_exact_root_grant_even_if_installer_fails(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                log = io.StringIO()
                with patch.object(launcher.subprocess, 'run', return_value=result(
                        'access control enabled\n    SI:localuser:root\n')) as run:
                    try:
                        with launcher.root_display_access(log):
                            if fail:
                                raise subprocess.CalledProcessError(1, ['calamares'])
                    except subprocess.CalledProcessError:
                        self.assertTrue(fail)
                run.assert_called_once_with(['xhost'], capture_output=True, text=True, check=False)

    def test_temporary_grant_is_revoked_on_success_or_installer_failure(self):
        for fail in (False, True):
            with self.subTest(fail=fail):
                log = io.StringIO()
                failure = subprocess.CalledProcessError(1, ['calamares'])
                with patch.object(launcher.subprocess, 'run', return_value=result(
                        'access control enabled\n    SI:localuser:root-other\n')) as run:
                    try:
                        with launcher.root_display_access(log):
                            self.assertEqual(run.call_count, 2)
                            if fail:
                                raise failure
                    except subprocess.CalledProcessError as error:
                        self.assertIs(error, failure)
                self.assertEqual(run.call_args_list, [
                    call(['xhost'], capture_output=True, text=True, check=False),
                    call(['xhost', '+SI:localuser:root'], stdout=log, stderr=log, check=True),
                    call(['xhost', '-SI:localuser:root'], stdout=log, stderr=log, check=True),
                ])

    def test_failed_query_is_logged_and_does_not_grant_or_enter_body(self):
        log = io.StringIO()
        with patch.object(launcher.subprocess, 'run', return_value=result(
                stderr='cannot open display :0', returncode=1)) as run:
            with self.assertRaisesRegex(ValueError, 'Could not inspect XWayland'):
                with launcher.root_display_access(log):
                    self.fail('Installer must not run after failed access query')
        self.assertEqual(run.call_count, 1)
        self.assertIn('cannot open display :0', log.getvalue())

    def test_failed_grant_does_not_enter_body_or_remove_unowned_access(self):
        log = io.StringIO()
        failure = subprocess.CalledProcessError(1, ['xhost', '+SI:localuser:root'])
        with patch.object(launcher.subprocess, 'run', side_effect=[result(), failure]) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                with launcher.root_display_access(log):
                    self.fail('Installer must not run after failed grant')
        self.assertEqual(run.call_count, 2)

    def test_failed_revoke_is_logged_and_surfaced(self):
        log = io.StringIO()
        failure = subprocess.CalledProcessError(1, ['xhost', '-SI:localuser:root'])
        with patch.object(launcher.subprocess, 'run', side_effect=[result(), result(), failure]) as run:
            with self.assertRaisesRegex(ValueError, 'Run xhost -SI:localuser:root') as raised:
                with launcher.root_display_access(log):
                    pass
        self.assertIs(raised.exception.__cause__, failure)
        self.assertEqual(run.call_count, 3)
        self.assertIn('Failed to revoke temporary local-root display access', log.getvalue())


class ExistingInstallerFocusTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': 'offline-fixture'})
        environment.start()
        self.addCleanup(environment.stop)

    def test_valid_installer_address_routes_to_that_window_only(self):
        for client in ({'class': 'calamares', 'address': '0xABC123'},
                       {'class': 'zenity', 'title': 'Install nascentOS — hardware review', 'address': '0xABC123'}):
            with self.subTest(client=client):
                with patch.object(launcher.subprocess, 'run', side_effect=[
                        result(json.dumps([{'class': 'firefox', 'address': '0xdef'}, client])), result()]) as run:
                    self.assertTrue(launcher.focus_existing())
                self.assertEqual(run.call_args_list, [
                    call(['hyprctl', '-j', 'clients'], capture_output=True, text=True, check=True),
                    call(['hyprctl', 'dispatch', 'hl.dsp.focus({window="address:0xABC123"})'],
                         check=True, capture_output=True),
                ])

    def test_invalid_addresses_never_dispatch(self):
        for address in ('', '0x', '0x1"});malicious()', '0x123\n', 'address:0x123', None):
            with self.subTest(address=address):
                with patch.object(launcher.subprocess, 'run', return_value=result(json.dumps([
                        {'class': 'calamares', 'address': address}]))) as run:
                    self.assertFalse(launcher.focus_existing())
                self.assertEqual(run.call_count, 1)

    def test_unrelated_window_and_missing_compositor_do_not_focus(self):
        with patch.object(launcher.subprocess, 'run', return_value=result(json.dumps([
                {'class': 'zenity', 'title': 'Unrelated dialog', 'address': '0x123'},
                {'class': 'firefox', 'address': '0x456'}]))) as run:
            self.assertFalse(launcher.focus_existing())
            self.assertEqual(run.call_count, 1)
        with patch.dict(os.environ, {'HYPRLAND_INSTANCE_SIGNATURE': ''}):
            with patch.object(launcher.subprocess, 'run') as run:
                self.assertFalse(launcher.focus_existing())
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
