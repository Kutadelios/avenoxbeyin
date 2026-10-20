"""Windows Codex policy contracts, runnable on Linux with synthetic state.

These tests check argv, version gates and policy discovery. They do not claim
native MXC enforcement; use v3_yakala_codex_boundary_test on a supported Windows
host with an explicitly supplied official Codex executable for that gate.
"""
import contextlib
import ctypes
import json
from pathlib import Path
import tomllib
import types
import unittest
from unittest.mock import Mock, patch

from tests import v3_yakala_ajan_codex_review_test as review
from tests.v3_yakala_ajan_test import AgentFiles, yakala


class CodexWindowsBoundaryTest(AgentFiles):
    @contextlib.contextmanager
    def windows(self):
        # Replacing only the module alias leaves pathlib and host file I/O native.
        system = types.SimpleNamespace(**{**vars(yakala.os), 'name': 'nt'})
        runtime = types.SimpleNamespace(**{**vars(yakala.sys), 'platform': 'win32'})
        with patch.object(yakala, 'os', system), patch.object(yakala, 'sys', runtime):
            yield

    def test_windows_requires_mxc_not_legacy_read_only(self):
        with self.windows():
            argv = yakala._agent_codex_permissions()
        self.assertIn('windows.sandbox="mxc"', argv)
        self.assertNotIn('-s', argv)
        self.assertNotIn('--sandbox', argv)
        self.assertFalse(any('prefer_mxc' in arg for arg in argv))
        document = tomllib.loads('\n'.join(argv[index + 1]
                                         for index, value in enumerate(argv) if value == '-c'))
        selected = document['default_permissions']
        self.assertRegex(selected, r'^beyin_yakala_[0-9a-f]{32}$')
        self.assertEqual(document['permissions'], {selected: {'filesystem': {':root': 'deny'}}})
        self.assertEqual(document['windows'], {'sandbox': 'mxc'})

    def test_each_windows_run_uses_a_fresh_profile(self):
        with self.windows():
            first = yakala._agent_codex_permissions()
            second = yakala._agent_codex_permissions()
        selected = lambda argv: next(arg for arg in argv if arg.startswith('default_permissions='))
        self.assertNotEqual(selected(first), selected(second))

    def test_windows_older_stable_cli_is_refused_before_feature_inventory(self):
        for version in ('0.155.1', '0.160.0', '0.162.0'):
            with self.subTest(version=version), self.windows():
                with self.assertRaisesRegex(ValueError, 'Codex 0.163.0.*MXC'):
                    review.CodexFeatureReviewTest.preflight(self, version='codex-cli ' + version)
                self.assertFalse(any('features' in call[0] for call in self.calls))

    def test_windows_reviewed_cli_retains_existing_feature_and_mcp_gates(self):
        with self.windows():
            self.assertEqual(review.CodexFeatureReviewTest.preflight(
                self, version='codex-cli 0.163.0', mcp_enabled=True), ('local_mcp',))
        self.assertEqual(sum('features' in call[0] for call in self.calls), 2)
        self.assertEqual(sum('mcp' in call[0] for call in self.calls), 2)

    def test_windows_prerelease_is_not_mistaken_for_reviewed_stable(self):
        with self.windows(), self.assertRaisesRegex(ValueError, '0.163.0'):
            review.CodexFeatureReviewTest.preflight(self, version='codex-cli 0.164.0-alpha.1')

    def test_windows_managed_profile_cannot_silently_replace_root_deny(self):
        home = self.codex_home.return_value
        home.mkdir()
        managed = home / 'requirements.toml'
        managed.write_text('default_permissions = ":read-only"\n'
                           '[allowed_permission_profiles]\n":read-only" = true\n', encoding='utf-8')
        self.codex_config_files.return_value = ((managed, True),)
        with self.windows(), self.assertRaisesRegex(ValueError, 'ajan baslatilmadi'):
            review.CodexFeatureReviewTest.preflight(self)
        self.assertFalse(any('features' in call[0] for call in self.calls))

    def test_windows_cloud_managed_bundle_is_not_guessed(self):
        home = self.codex_home.return_value
        home.mkdir()
        (home / 'cloud-config-bundle-cache.json').write_text(
            json.dumps({'synthetic': 'managed policy exists'}), encoding='utf-8')
        with self.windows(), self.assertRaisesRegex(ValueError, 'bulut.*ajan baslatilmadi'):
            yakala._agent_codex_profile_preflight(self.vault)

    def test_windows_unreadable_config_is_refused(self):
        home = self.codex_home.return_value
        self.codex_config_files.return_value = ((home / 'requirements.toml', True),)
        with self.windows(), patch.object(yakala.Path, 'open', side_effect=PermissionError('synthetic')):
            with self.assertRaisesRegex(ValueError, 'okunamadi.*ajan baslatilmadi'):
                yakala._agent_codex_profile_preflight(self.vault)

    def test_windows_system_policy_uses_known_folder_namespace(self):
        system = Path(self.tmp.name) / 'Synthetic ProgramData' / 'OpenAI' / 'Codex'
        with self.windows(), patch.object(yakala, '_agent_codex_system_dir', return_value=system), \
                patch.object(yakala.os, 'scandir') as scan:
            scan.return_value.__enter__.return_value = ()
            paths = review.CONFIG_FILES(self.vault)
        self.assertIn((system / 'config.toml', False), paths)
        self.assertIn((system / 'requirements.toml', True), paths)
        self.assertIn((system / 'managed_config.toml', True), paths)
        self.assertFalse(any(str(path).startswith('/etc/codex/') for path, _ in paths))

    def test_windows_failed_known_folder_lookup_is_closed_without_env_fallback(self):
        with self.windows(), patch.object(ctypes, 'WinDLL', side_effect=OSError('synthetic'), create=True), \
                patch.dict(yakala.os.environ, {'PROGRAMDATA': str(self.vault)}):
            with self.assertRaisesRegex(ValueError, 'sistem config.*ajan baslatilmadi'):
                yakala._agent_codex_system_dir()

    def test_windows_known_folder_buffer_is_freed_on_success(self):
        directory = Path(self.tmp.name) / 'Synthetic ProgramData'
        shell, ole = Mock(), Mock()

        def lookup(folder, flags, token, result):
            self.assertEqual(flags, 0)
            self.assertIsNone(token)
            result._obj.value = str(directory)
            return 0

        shell.SHGetKnownFolderPath.side_effect = lookup
        with self.windows(), patch.object(ctypes, 'WinDLL', side_effect=[shell, ole], create=True):
            self.assertEqual(yakala._agent_codex_system_dir(), directory / 'OpenAI' / 'Codex')
        ole.CoTaskMemFree.assert_called_once()

    def test_windows_known_folder_hresult_failure_is_closed(self):
        shell, ole = Mock(), Mock()
        shell.SHGetKnownFolderPath.return_value = -1
        with self.windows(), patch.object(ctypes, 'WinDLL', side_effect=[shell, ole], create=True):
            with self.assertRaisesRegex(ValueError, 'sistem config.*ajan baslatilmadi'):
                yakala._agent_codex_system_dir()
        ole.CoTaskMemFree.assert_not_called()


if __name__ == '__main__':
    unittest.main()
