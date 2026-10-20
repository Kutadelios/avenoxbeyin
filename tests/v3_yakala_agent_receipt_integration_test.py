"""A real installed receipt is required before a synthetic agent job completes."""
from pathlib import Path
import unittest

from v3_package_helpers import clean_environ, inherited_env, install, isolated_env
from v3_yakala_ajan_test import AgentFiles, yakala


class AgentInstalledReceiptTest(AgentFiles):
    def test_bridge_result_is_finalized_through_the_real_installed_receipt_cli(self):
        environment = inherited_env(**isolated_env(Path(self.tmp.name) / 'fixture-home'))
        installed = install(self.vault, self.state, environment)
        self.assertEqual(installed.returncode, 0, installed.stderr.decode('utf-8', errors='replace'))
        previous = self.vault / 'memory/Last-Session.md'
        previous.parent.mkdir(exist_ok=True)
        previous.write_text('# Last Session\n\nSynthetic user-owned memory.\n', encoding='utf-8')
        before = previous.read_bytes()
        self.configure()
        _, job, card = self.queued(text='Synthetic camera mounting experiment',
                                   request='Kaynağa bağlı kısa bir sonuç notu yaz.')
        job['state'] = 'running'
        yakala._agent_prepare_runtime(self.vault, self.state, job)
        note = yakala._agent_tool_call(self.vault, self.state, job['id'], 'write_note',
                                      {'title': 'Sentetik sonuç', 'content': 'Kamera sabit rayda denendi.'})
        yakala._agent_tool_call(self.vault, self.state, job['id'], 'complete',
                               {'status': 'completed', 'summary': 'Sentetik deneme kaydedildi.',
                                'notes': [note['path']]})
        card_before = card['path'].read_bytes()
        with clean_environ(**environment):
            terminal, summary = yakala._agent_finalize(self.vault, self.state, job)
        self.assertEqual(terminal, 'completed')
        persisted = yakala._agent_load_job(self.vault, self.state, job['id'])
        receipt = self.vault / persisted['receipt']
        self.assertTrue(receipt.is_file())
        self.assertIn('yakala-' + job['id'], receipt.read_text(encoding='utf-8'))
        self.assertIn('Sentetik deneme', receipt.read_text(encoding='utf-8'))
        self.assertTrue((self.vault / persisted['outcome']).is_file())
        self.assertEqual(previous.read_bytes(), before)
        self.assertEqual(card['path'].read_bytes(), card_before)
        yakala._agent_end(self.vault, self.state, job, terminal, summary)
        completed = yakala.find_card(self.vault, card['id'], self.state)
        self.assertEqual(completed['meta']['durum'], 'islendi')
        self.assertEqual(completed['meta']['ajan_receipt'], persisted['receipt'])
        self.assertEqual(completed['body'], card['body'])


if __name__ == '__main__':
    unittest.main()
