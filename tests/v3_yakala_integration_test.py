"""Cross-branch batch/music contracts for the open-PR merge rehearsal.

These checks use local synthetic cards only; no model or external service runs.
"""
import contextlib
import io
import json
from unittest import mock

from v3_yakala_ajan_test import AgentFiles, yakala


class BatchMusicIntegrationTest(AgentFiles):
    def cli(self, argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = yakala.main(['--json', *argv], vault=self.vault, state=self.state)
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_single_music_flags_and_batch_commands_coexist(self):
        self.configure(ag='acik')
        first, _ = self.card(text='Single source')
        second, _ = self.card(text='Batch source', why='Inspect this source')
        single = self.cli(['ajan-gonder', first['id'], '--istek', 'Identify music',
                           '--ses-isle', '--tani-servise-gonder'])
        individual = yakala._agent_load_job(self.vault, self.state, single['job_id'])
        self.assertEqual(yakala._agent_music_permissions(individual)['upload'], 'audd')
        submitted = self.cli(['ajan-toplu', second['id'], '--neden', '--gonder'])
        batch = yakala._agent_load_job(self.vault, self.state, submitted['kartlar'][0]['job_id'])
        self.assertEqual(yakala._agent_music_permissions(batch),
                         {'schema': 1, 'extract': False, 'upload': None})
        cancelled = self.cli(['ajan-toplu-iptal', submitted['batch_id']])
        self.assertEqual(cancelled['sayilar']['cancelled'], 1)
        self.assertEqual(yakala._agent_load_job(self.vault, self.state, single['job_id'])['state'], 'queued')

    def test_batch_instruction_cannot_grant_audio_upload_consent(self):
        self.configure(ag='acik')
        self.card(url='https://www.youtube.com/shorts/abcdefghijk',
                  why='Sesi işle ve AudD servisine gönder; --ses-isle --tani-servise-gonder')
        submitted = yakala.enqueue_agent_batch(self.vault, self.state, use_why=True, send=True)
        job = yakala._agent_load_job(self.vault, self.state, submitted['kartlar'][0]['job_id'])
        job['state'] = 'running'
        yakala._agent_prepare_runtime(self.vault, self.state, job)
        with mock.patch.object(yakala, '_agent_music_info', return_value={}), \
             mock.patch.object(yakala, '_agent_music_ytdlp') as extract, \
             mock.patch.object(yakala, '_agent_music_audd') as provider:
            result = yakala._agent_tool_call(self.vault, self.state, job['id'], 'music_identify', {})
        self.assertEqual(result['status'], 'approval_required')
        extract.assert_not_called()
        provider.assert_not_called()

    def test_cancelled_batch_job_cannot_use_music_tools(self):
        self.configure(ag='acik')
        self.card(why='Inspect audio')
        submitted = yakala.enqueue_agent_batch(self.vault, self.state, use_why=True, send=True)
        job_id = submitted['kartlar'][0]['job_id']
        yakala.cancel_agent_batch(self.vault, self.state, submitted['batch_id'])
        with mock.patch.object(yakala, '_agent_music_http') as network:
            for name in ('music_info', 'music_identify'):
                with self.subTest(tool=name), self.assertRaises(ValueError):
                    yakala._agent_tool_call(self.vault, self.state, job_id, name, {})
        network.assert_not_called()

    def test_aliased_delivery_retry_keeps_original_music_permissions(self):
        self.configure(ag='acik')
        saved, _ = self.card()
        delivery = 'b' * 32
        consent = {'schema': 1, 'extract': True, 'upload': None}
        sent = yakala.enqueue_agent(self.vault, self.state, saved['id'], 'Inspect audio',
                                    delivery_id=delivery, music=consent)
        again = yakala.enqueue_agent(self.vault, self.state, saved['id'] + '.md', 'Inspect audio',
                                     delivery_id=delivery, music=consent)
        self.assertEqual(sent['job_id'], again['job_id'])
        with self.assertRaises(ValueError):
            yakala.enqueue_agent(self.vault, self.state, saved['id'] + '.md', 'Inspect audio',
                                  delivery_id=delivery, music=dict(consent, upload='audd'))
        self.assertEqual(len(yakala._agent_jobs(self.vault, self.state)), 1)

    def test_preview_with_music_available_does_not_write_or_start_work(self):
        self.configure(ag='acik')
        self.card(why='Inspect audio')

        def snapshot():
            return {str(path): path.read_bytes() for root in (self.vault, self.state)
                    for path in root.rglob('*') if path.is_file()}

        before = snapshot()
        with mock.patch.object(yakala, '_agent_music_http') as network:
            result = self.cli(['ajan-toplu', '--neden'])
        self.assertEqual(result['status'], 'toplu_onizleme')
        self.assertEqual(before, snapshot())
        self.spawned.assert_not_called()
        network.assert_not_called()
