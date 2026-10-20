import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tests'))
from v3_package_helpers import inherited_env, install


class CliJsonModeTest(unittest.TestCase):
    """Issue #417: CLI exits with structured JSON errors instead of plain text when --json is passed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v3-cli-json-test-')
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / 'vault'
        self.vault.mkdir()
        self.cli = ROOT / 'scripts/beyin_v3.py'
        self.env = inherited_env(BEYIN_V3_NO_SPAWN='1', BEYIN_UPDATES_OFF='1')

    def test_missing_command_in_cli_json_mode_fails_open_with_json_error(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault), '--json'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('command', error['message'])

    def test_missing_command_in_cli_human_mode_exits_with_argparse_stderr(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault)],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout.strip(), b'')
        self.assertIn('the following arguments are required', result.stderr.decode())

    def test_invalid_command_in_cli_json_mode_fails_open_with_json_error(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault), '--json', 'invalid-command'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('invalid choice', error['message'])

    def test_help_in_cli_json_mode_exits_zero_with_stdout_usage(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault), '--json', '--help'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'usage:', result.stdout)
        self.assertEqual(result.stderr.strip(), b'')

    def test_subcommand_invalid_flag_in_cli_json_mode_fails_with_json_error(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault), '--json', 'sync', '--nonexistent-flag'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('unrecognized arguments', error['message'])

    def test_receipt_flag_conflict_in_cli_json_mode_fails_with_json_error(self):
        result = subprocess.run(
            [sys.executable, str(self.cli), '--vault', str(self.vault), '--json', 'receipt',
             '--file', 'test.json', '--event-id', 'ev-1'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('--file cannot be combined with receipt flags', error['message'])


class InstalledEntryJsonModeTest(unittest.TestCase):
    """Issue #417: The installed entrypoint beyin.py formats argument errors as JSON when --json is passed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v3-installed-entry-test-')
        self.addCleanup(self.tmp.cleanup)
        self.vault = Path(self.tmp.name) / 'vault'
        self.vault.mkdir()
        self.state = Path(self.tmp.name) / 'state'
        self.env = inherited_env(BEYIN_V3_NO_SPAWN='1', BEYIN_UPDATES_OFF='1')
        res = install(self.vault, self.state, self.env)
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_installed_entry_json_mode_invalid_command_returns_json(self):
        result = subprocess.run(
            [sys.executable, str(self.vault / 'beyin.py'), '--json', 'invalid-command'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('invalid choice', error['message'])

    def test_installed_entry_json_mode_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(self.vault / 'beyin.py'), '--json', '--help'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'usage:', result.stdout)
        self.assertEqual(result.stderr.strip(), b'')

    def test_installed_entry_json_mode_update_invalid_flag_returns_json(self):
        result = subprocess.run(
            [sys.executable, str(self.vault / 'beyin.py'), '--json', 'update', '--nonexistent-flag'],
            capture_output=True,
            env=self.env
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.strip(), b'')
        error = json.loads(result.stderr.decode().strip())
        self.assertEqual(error['error'], 'SystemExit')
        self.assertIn('unrecognized arguments', error['message'])


if __name__ == '__main__':
    unittest.main()
