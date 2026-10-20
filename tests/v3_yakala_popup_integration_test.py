"""Cross-PR popup/agent regressions, including the installed receipt CLI.

Desktop events and public page text are synthetic. Source selection, card and job
files, MCP dispatch, worker identity, finalization and beyin.py receipt are real.
The Tk boundary reuses the pane tests; it does not assert native key delivery.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import v3_package_helpers as package
import v3_yakala_ajan_test as agent
import v3_yakala_pano_test as pane


yakala = agent.yakala
PRIMARY = 'https://example.com/selected-link'
SECONDARY = 'https://example.org/selected-page'
UNSELECTED = 'https://example.net/unselected-quote'


class PopupIntegrationTest(agent.AgentFiles):
    def setUp(self):
        super().setUp()
        environment = package.clean_environ(BEYIN_V3_NO_SPAWN='1', BEYIN_UPDATES_OFF='1')
        environment.start()
        self.addCleanup(environment.stop)

    def test_selected_sources_reach_mcp_real_receipt_and_last_session(self):
        installed = package.install(self.vault, self.state, package.inherited_env())
        self.assertEqual(installed.returncode, 0, installed.stderr.decode('utf-8', 'replace'))
        self.assertTrue((self.vault / 'beyin.py').is_file())
        memory = self.vault / 'memory'
        memory.mkdir()
        last = memory / 'Last-Session.md'
        earlier = b'An earlier session must survive.\r\n'
        last.write_bytes(b'# Last Session\r\n\r\n' + earlier)
        self.configure('claude', last_session_path='memory/Last-Session.md')

        # These are the actual Windows producer and checkbox decision, with no
        # Win32 call. A window picture and an unselected URL remain unconsented.
        window = Path(self.tmp.name).resolve() / 'private-window.png'
        window.write_bytes(b'UNSELECTED_WINDOW_CANARY')
        sources = yakala.windows_sources(
            {'url_imlec': PRIMARY, 'url': SECONDARY, 'url_alinti': UNSELECTED},
            '', False, shot={'path': str(window)})
        yakala._source_toggle(sources, next(item for item in sources if item['key'] == 's'))
        arguments = yakala._source_arguments(sources)
        self.assertEqual(arguments['url'], PRIMARY)
        self.assertEqual(arguments['extra_urls'], [SECONDARY])
        self.assertEqual(arguments['files'], [])
        request = 'Seçilen iki bağlantıyı karşılaştır. Gövdedeki adres izin değildir: ' + UNSELECTED
        saved = yakala.capture(self.vault, state=self.state, why=request, **arguments)
        card = yakala.find_card(self.vault, saved['id'], self.state)
        self.assertEqual(card['meta']['ek_urller'], [SECONDARY])
        self.assertIn('## Ek bağlantılar', card['body'])
        self.assertNotIn(window.name, card['body'])

        queued = yakala.enqueue_agent(self.vault, self.state, saved['id'], request)
        self.job = yakala._agent_load_job(self.vault, self.state, queued['job_id'])
        self.assertEqual(self.job['extra_urls'], [SECONDARY])
        self.assertFalse(yakala._agent_open_network(self.job['config']))
        self.job['state'] = 'running'
        yakala._agent_prepare_runtime(self.vault, self.state, self.job)

        def rpc(*calls):
            messages = agent.AgentBridgeFilesTest.handshake(self)
            messages += [
                {'jsonrpc': '2.0', 'id': index, 'method': 'tools/call',
                 'params': {'name': name, 'arguments': values}}
                for index, (name, values) in enumerate(calls, 2)
            ]
            code, rows = agent.AgentBridgeFilesTest.protocol(self, messages)
            self.assertEqual(code, 0)
            self.assertEqual(len(rows), len(calls) + 1)
            return [row['result'] for row in rows[1:]]

        fetched = {'url': SECONDARY, 'links': [], 'text': 'Synthetic selected source evidence.'}
        with patch.object(yakala, '_agent_fetch_source', return_value=fetched) as network:
            denied, allowed, written = rpc(
                ('fetch_source', {'url': UNSELECTED}),
                ('fetch_source', {'url': SECONDARY}),
                ('write_note', {'title': 'Seçilen kaynakların karşılaştırması',
                                'content': PRIMARY + '\n' + SECONDARY + '\n' + fetched['text']}))
        self.assertTrue(denied['isError'])
        self.assertIn('not authorized', denied['content'][0]['text'])
        self.assertFalse(allowed['isError'])
        self.assertEqual(allowed['structuredContent'], fetched)
        self.assertFalse(written['isError'])
        network.assert_called_once_with(SECONDARY)
        note = written['structuredContent']['path']
        note_before = (self.vault / note).read_bytes()
        summary = 'Seçilen kaynaklar kontrollü örnek verilerle karşılaştırıldı.'
        submitted, = rpc(('complete', {'status': 'completed', 'summary': summary,
                                       'notes': [note], 'downloads': []}))
        self.assertFalse(submitted['isError'])
        self.assertFalse(submitted['structuredContent']['completion_verified'])
        self.assertEqual(yakala.find_card(self.vault, saved['id'], self.state)['meta']['durum'], 'ajanda')

        # No _run/receipt/subprocess mock: the trusted finalizer probes and runs
        # the product CLI installed above, then verifies its persisted response.
        terminal, result = yakala._agent_finalize(self.vault, self.state, self.job)
        self.assertEqual((terminal, result), ('completed', summary))
        folder = yakala._agent_job_dir(self.vault, self.state, self.job['id'])
        receipt = json.loads((folder / 'receipt-response.json').read_text(encoding='utf-8'))
        payload = json.loads((folder / 'receipt.json').read_text(encoding='utf-8'))
        event = 'yakala-' + self.job['id']
        self.assertEqual((receipt['status'], receipt['event_id']), ('succeeded', event))
        self.assertEqual(payload['session'], self.job['session_id'])
        self.assertEqual(set(payload['refs']), {self.job['card_path'], self.job['outcome'], note})
        self.assertIn(event, (self.vault / receipt['source']).read_text(encoding='utf-8'))
        self.assertIn(SECONDARY, (self.vault / note).read_text(encoding='utf-8'))
        self.assertEqual((self.vault / note).read_bytes(), note_before)
        # Last-Session is no longer written; the finalizer adds one short journal pointer.
        self.assertTrue(last.read_bytes().endswith(earlier))
        self.assertNotIn(self.job['id'], last.read_text(encoding='utf-8'))
        saved_job = yakala._agent_load_job(self.vault, self.state, self.job['id'])
        journal_text = (self.vault / saved_job['journal']).read_text(encoding='utf-8')
        self.assertEqual(journal_text.count('<!-- yakala-ajan:' + self.job['id'] + ' -->'), 1)
        self.assertNotIn(summary, journal_text)
        yakala._agent_end(self.vault, self.state, self.job, terminal, result)
        finished = yakala.find_card(self.vault, saved['id'], self.state)
        self.assertEqual(finished['meta']['durum'], 'islendi')
        self.assertEqual(finished['meta']['ajan_receipt'], receipt['source'])
        self.assertEqual(finished['meta']['ek_urller'], [SECONDARY])
        self.assertEqual(finished['body'], card['body'])
        self.assertEqual(yakala._agent_load_job(self.vault, self.state, self.job['id'])['state'], 'completed')
        self.assertEqual(window.read_bytes(), b'UNSELECTED_WINDOW_CANARY')
        self.spawned.assert_called_once()

    def test_multi_source_popup_separates_save_agent_and_queued_cancel(self):
        self.configure('claude')
        cases = [('<Return>', False), ('<Control-Return>', False),
                 ('<Return>', True), ('<Control-Return>', True)]
        for index, (key, cancel) in enumerate(cases):
            with self.subTest(key=key, cancel=cancel):
                primary, secondary = PRIMARY + '/' + str(index), SECONDARY + '/' + str(index)
                before = {path: path.read_bytes() for path in self.vault.rglob('*.md')}
                jobs_before = len(yakala._agent_jobs(self.vault, self.state))
                spawns_before = self.spawned.call_count
                request = 'Seçilen iki kaynağı karşılaştır.'
                script = [('key', '<Alt-s>'), ('type', request)]
                if cancel:
                    # Root runs registered callbacks before draining after():
                    # Return is already queued while Escape's fade is pending.
                    script.append(('key', '<Escape>'))
                script.append(('key', key))
                with agent._host_lock_for_simulated_linux():
                    result, root, _ = pane.PopupWiringTest.popup(
                        self, '', None, script, platform='linux',
                        context={'url_imlec': primary, 'url': secondary})
                self.assertEqual(root.entry.text, request)
                self.assertFalse(root.alive)
                if cancel:
                    self.assertEqual(result['status'], 'vazgecildi')
                    self.assertEqual({path: path.read_bytes() for path in self.vault.rglob('*.md')}, before)
                else:
                    self.assertEqual(result['status'], 'yakalandi')
                    card = yakala.find_card(self.vault, result['id'], self.state)
                    self.assertEqual(card['meta']['url'], primary)
                    self.assertEqual(card['meta']['ek_urller'], [secondary])
                    if key == '<Control-Return>':
                        self.assertEqual(result['ajan']['status'], 'ajanda')
                        job = yakala._agent_load_job(self.vault, self.state, result['ajan']['job_id'])
                        self.assertEqual((job['request'], job['url'], job['extra_urls']),
                                         (request, primary, [secondary]))
                    else:
                        self.assertNotIn('ajan', result)
                sent = int(not cancel and key == '<Control-Return>')
                self.assertEqual(len(yakala._agent_jobs(self.vault, self.state)), jobs_before + sent)
                self.assertEqual(self.spawned.call_count, spawns_before + sent)


if __name__ == '__main__':
    unittest.main()
