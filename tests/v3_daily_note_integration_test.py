"""Cross-PR contract: flat receipt projections remain managed note sources."""
from datetime import timezone
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'template/.claude/scripts'))
import beyin_v3_preferences as preferences
import beyin_v3_projections as projections
from beyin_v3_sync import SyncEngine, parse, render


class DailyNoteIntegrationTest(unittest.TestCase):
    def test_flat_view_without_frontmatter_is_rejected_before_note_write(self):
        with tempfile.TemporaryDirectory(prefix='v3-daily-note-') as directory:
            root = Path(directory).resolve()
            vault = root / 'vault'
            (vault / 'notes').mkdir(parents=True)
            (vault / 'notes/source.md').write_bytes(b'# Human source\n')
            preferences.save_daily_layout(vault, 'flat')
            (vault / 'receipts').mkdir()
            event = 'flat-view-note-contract'
            receipt = vault / 'receipts' / (hashlib.sha256(event.encode()).hexdigest() + '.md')
            receipt.write_bytes(render(
                {'kind': 'receipt', 'event_id': event, 'harness': 'codex',
                 'refs': ['notes/source.md'], 'visibility': 'internal',
                 'created_at': '2026-10-19T12:00:00+00:00'}, 'Recorded result.\n').encode())
            engine = SyncEngine(vault, root / 'state')
            self.addCleanup(engine.store.close)
            with patch.object(projections, '_local_zone', return_value=timezone.utc):
                self.assertEqual(engine.sync()['status'], 'succeeded')
                source = 'daily/2026-10-19.md'
                path = vault / source
                metadata, body = parse(path.read_text(encoding='utf-8'))
                self.assertIs(metadata['generated'], True)
                self.assertEqual(metadata['kind'], 'receipt-index')
                with engine.store._connect() as db:
                    self.assertIsNotNone(db.execute('SELECT 1 FROM receipt_views WHERE path=?',
                                                   (source,)).fetchone())
                # An external editor removed only the managed frontmatter.
                raw = body.encode('utf-8')
                path.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'managed source'):
                    engine.note_read(source)
                with self.assertRaisesRegex(ValueError, 'managed source'):
                    engine.note_edit({'source': source, 'expected_sha256': hashlib.sha256(raw).hexdigest(),
                                      'edits': [{'old': 'Recorded result.', 'new': 'Attempted edit.'}]})
                self.assertEqual(path.read_bytes(), raw)
                self.assertFalse((vault / '.beyin-note-write/backups').exists())
                # The real flat layout must still permit an ordinary human day.
                human = 'daily/2026-10-20.md'
                created = engine.note_edit({'source': human, 'expected_sha256': None,
                                           'content': '# Human journal\n'})
                self.assertEqual(created['status'], 'written')
                self.assertEqual(engine.note_read(human)['content'], '# Human journal\n')
                self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
