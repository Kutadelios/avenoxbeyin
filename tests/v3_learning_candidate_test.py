import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'template/.claude/scripts'))
import beyin_v3_learning as learning
import beyin_v3_hook as hook
from beyin_v3_sync import SyncEngine


class LearningCandidateLedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        (self.vault / 'notes').mkdir(parents=True, exist_ok=True)
        (self.vault / 'notes' / 'task.md').write_text('# task\n', encoding='utf-8')
        (self.vault / 'notes' / 'doc.md').write_text('# doc\n', encoding='utf-8')
        self.state = self.root / 'state'
        self.state.mkdir()
        self.engine = SyncEngine(self.vault, self.state)
        self.env = dict(os.environ, PYTHONIOENCODING='utf-8')

    def test_stage_and_list_candidates(self):
        session = "session-1234567890abcdef"
        rec = learning.stage_candidate(self.state, session, "WAL timeout must be at least 5s",
                                       source="notes/task.md", scope="database")
        self.assertEqual(rec["candidate"], "WAL timeout must be at least 5s")
        self.assertEqual(rec["source"], "notes/task.md")
        self.assertEqual(rec["scope"], "database")
        self.assertEqual(rec["status"], "candidate")

        # Verify persistence in state/learning-state.jsonl
        ledger = self.state / "learning-state.jsonl"
        self.assertTrue(ledger.is_file())

        # List candidates
        active = learning.list_candidates(self.state, session=session)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["id"], rec["id"])

        self.assertTrue(learning.has_candidates(self.state, session=session))
        self.assertFalse(learning.has_candidates(self.state, session="different-session"))

    def test_resolve_candidates(self):
        session = "session-resolve-abc"
        learning.stage_candidate(self.state, session, "Learning 1")
        learning.stage_candidate(self.state, session, "Learning 2")
        self.assertEqual(len(learning.list_candidates(self.state, session=session)), 2)

        count = learning.resolve_candidates(self.state, session, target_status="distilled")
        self.assertEqual(count, 2)

        # Now active candidates should be empty
        self.assertFalse(learning.has_candidates(self.state, session=session))
        # But distilled ones are preserved
        distilled = learning.list_candidates(self.state, session=session, status="distilled")
        self.assertEqual(len(distilled), 2)

    def test_cli_learn_command(self):
        res = subprocess.run([
            sys.executable, str(ROOT / 'scripts/beyin_v3.py'),
            '--vault', str(self.vault), '--state', str(self.state),
            'learn', '--candidate', 'CLI staged learning', '--source', 'notes/doc.md', '--scope', 'infra',
            '--session', 'cli-sess'
        ], capture_output=True, text=True, check=True, env=self.env, timeout=30)
        output = json.loads(res.stdout)
        self.assertEqual(output["candidate"], "CLI staged learning")
        self.assertEqual(output["scope"], "infra")

        # List via CLI
        list_res = subprocess.run([
            sys.executable, str(ROOT / 'scripts/beyin_v3.py'),
            '--vault', str(self.vault), '--state', str(self.state),
            'learn', '--list'
        ], capture_output=True, text=True, check=True, env=self.env, timeout=30)
        list_output = json.loads(list_res.stdout)
        self.assertIn("candidates", list_output)
        self.assertEqual(len(list_output["candidates"]), 1)
        self.assertEqual(list_output["candidates"][0]["candidate"], "CLI staged learning")

    def test_stop_hook_challenges_explicit_no_learning_after_edits(self):
        session_id = 'test-no-learning-bypass'
        session_hash = hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:24]

        # Simulate edit
        payload_edit = {'session_id': session_id, 'hook_event_name': 'PostToolUse'}
        hook.receipt_reminder(payload_edit, self.state, 'claude', 'PostToolUse', vault=self.vault)

        # Agent writes receipt claiming 'Öğrenilen: yok'
        time.sleep(0.02)
        self.engine.receipt('no-learning-1', 'Refactored auth module.\nÖğrenilen: yok',
                            ['notes/task.md'], 'claude', session=session_hash)

        # Stop hook must block once challenging the 'Öğrenilen: yok' claim!
        payload_stop = {'session_id': session_id, 'hook_event_name': 'Stop'}
        res = hook.receipt_reminder(payload_stop, self.state, 'claude', 'Stop', vault=self.vault)
        self.assertIsNotNone(res)
        self.assertEqual(res.get('decision'), 'block')
        self.assertIn("Öğrenilen: yok", res.get('reason', ''))

        # Subsequent Stop passes open (agent answered challenge or routine edit)
        res2 = hook.receipt_reminder(payload_stop, self.state, 'claude', 'Stop', vault=self.vault)
        self.assertIsNone(res2)

    def test_staged_candidate_satisfies_learning_contract(self):
        session_id = 'test-staged-candidate'
        session_hash = hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:24]

        # Simulate edit
        payload_edit = {'session_id': session_id, 'hook_event_name': 'PostToolUse'}
        hook.receipt_reminder(payload_edit, self.state, 'claude', 'PostToolUse', vault=self.vault)

        # Stage candidate in ledger
        learning.stage_candidate(self.state, session_hash, "Staged learning before receipt", source="auth.py")

        # Agent writes receipt declaring the learning
        time.sleep(0.02)
        self.engine.receipt('staged-1', 'Refactored auth module.\nÖğrenilen: Staged learning before receipt',
                            ['notes/task.md'], 'claude', session=session_hash)

        # Stop hook passes because candidate was already safely staged!
        payload_stop = {'session_id': session_id, 'hook_event_name': 'Stop'}
        res = hook.receipt_reminder(payload_stop, self.state, 'claude', 'Stop', vault=self.vault)
        self.assertIsNone(res)

    def test_cli_to_stop_hook_integration(self):
        session_id = 'test-cli-hook-int'
        session_hash = hashlib.sha256(session_id.encode('utf-8')).hexdigest()[:24]

        # 1. Edit a file
        payload_edit = {'session_id': session_id, 'hook_event_name': 'PostToolUse'}
        hook.receipt_reminder(payload_edit, self.state, 'claude', 'PostToolUse', vault=self.vault)

        # 2. Write receipt with 'Öğrenilen: yok'
        time.sleep(0.02)
        self.engine.receipt('cli-int-1', 'Fixed edge case.\nÖğrenilen: yok',
                            ['notes/task.md'], 'claude', session=session_hash)

        # 3. Stop hook blocks because no candidate is staged yet
        payload_stop = {'session_id': session_id, 'hook_event_name': 'Stop'}
        res = hook.receipt_reminder(payload_stop, self.state, 'claude', 'Stop', vault=self.vault)
        self.assertIsNotNone(res)
        self.assertEqual(res.get('decision'), 'block')

        # 4. Stage candidate via CLI without --session flag
        res_cli = subprocess.run([
            sys.executable, str(ROOT / 'scripts/beyin_v3.py'),
            '--vault', str(self.vault), '--state', str(self.state),
            'learn', '--candidate', 'Connection pooling must handle timeouts gracefully'
        ], capture_output=True, text=True, check=True, env=self.env, timeout=30)
        self.assertEqual(res_cli.returncode, 0)

        # 5. Stop hook now passes because CLI candidate was detected
        res2 = hook.receipt_reminder(payload_stop, self.state, 'claude', 'Stop', vault=self.vault)
        self.assertIsNone(res2)

    def test_secret_redaction_in_candidate(self):
        secret_token = "sk-" + "a" * 30
        rec = learning.stage_candidate(self.state, "sess-sec", f"Use API token {secret_token} for auth")
        self.assertNotIn(secret_token, rec["candidate"])
        self.assertIn("[REDACTED]", rec["candidate"])

    def test_untrusted_or_private_source_rejected(self):
        from contextlib import closing
        import sqlite3
        db_path = self.state / "memory.sqlite3"
        with closing(sqlite3.connect(db_path)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            db.execute("INSERT OR REPLACE INTO records VALUES (?, ?)",
                       ("private-doc", json.dumps({"id": "private-doc", "visibility": "private"})))
            db.execute("INSERT OR REPLACE INTO records VALUES (?, ?)",
                       ("untrusted-doc", json.dumps({"id": "untrusted-doc", "trust": "untrusted"})))
            db.commit()

        with self.assertRaises(ValueError):
            learning.stage_candidate(self.state, "sess-priv", "Discovered private leak", source="private-doc")

        with self.assertRaises(ValueError):
            learning.stage_candidate(self.state, "sess-untr", "Discovered untrusted leak", source="untrusted-doc")

    def test_scope_isolation(self):
        learning.stage_candidate(self.state, "sess-1", "Global learning", scope="global")
        learning.stage_candidate(self.state, "sess-2", "Project A learning", scope="projectA")
        learning.stage_candidate(self.state, "sess-3", "Project B learning", scope="projectB")

        # Listing for Project A returns Project A + global, but NOT Project B
        cands_a = learning.list_candidates(self.state, scope="projectA")
        texts_a = [c["candidate"] for c in cands_a]
        self.assertIn("Global learning", texts_a)
        self.assertIn("Project A learning", texts_a)
        self.assertNotIn("Project B learning", texts_a)

        # Listing for Project B returns Project B + global, but NOT Project A
        cands_b = learning.list_candidates(self.state, scope="projectB")
        texts_b = [c["candidate"] for c in cands_b]
        self.assertIn("Global learning", texts_b)
        self.assertIn("Project B learning", texts_b)
        self.assertNotIn("Project A learning", texts_b)


if __name__ == '__main__':
    unittest.main()
