import unittest
import subprocess
import os
import sys
import shutil
from pathlib import Path
from v3_package_helpers import clean_environ

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'template/.claude/scripts'
HOOK = SCRIPTS / 'beyin_v3_hook.py'
HOOK_DONE = SCRIPTS / 'beyin_v3_hook_done.py'

class HookFuzzingTest(unittest.TestCase):
    def setUp(self):
        self.vault = Path('/tmp/vault_fuzz')
        self.state = Path('/tmp/state_fuzz')
        self.vault.mkdir(parents=True, exist_ok=True)
        self.state.mkdir(parents=True, exist_ok=True)
        self.env = clean_environ()
        
    def tearDown(self):
        shutil.rmtree(self.vault, ignore_errors=True)
        shutil.rmtree(self.state, ignore_errors=True)

    def test_hook_malformed_inputs_never_crash(self):
        payloads = [
            b"",
            b"{",
            b"\xef\xbb\xbf{}",
            b'{"foo": "' + b'a'*1100000 + b'"}',
        ]
        for p in payloads:
            res = subprocess.run([
                sys.executable, str(HOOK), 
                '--vault', str(self.vault), 
                '--state', str(self.state), 
                '--harness', 'codex'
            ], input=p, capture_output=True, env=dict(os.environ))
            self.assertEqual(res.returncode, 0, f"Hook crashed with payload size {len(p)}! stderr: {res.stderr.decode('utf-8', 'replace')}")

    def test_hook_done_malformed_inputs_never_crash(self):
        res = subprocess.run([sys.executable, str(ROOT / 'template/.claude/scripts/beyin_v3_hook_done.py')], input=b"{", capture_output=True, env=dict(os.environ))
        self.assertEqual(res.returncode, 0)
        
    def test_shell_script_unquoted_dir(self):
        if sys.platform == 'win32' or not shutil.which('bash'):
            self.skipTest("POSIX bash environment required for shell hook tests")
        res = subprocess.run([
            'bash', '-c', f'CLAUDE_PROJECT_DIR="/tmp/dir with spaces" bash "{ROOT.as_posix()}/template/.claude/hooks/lib.sh"'
        ], capture_output=True, env=dict(os.environ))
        self.assertEqual(res.returncode, 0)

if __name__ == '__main__':
    unittest.main()
