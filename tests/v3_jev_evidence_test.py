"""Synthetic evidence regressions."""
from v3_evidence_helpers import EvidenceFixture, rt, client, jev, os, patch


class JevEvidenceTest(EvidenceFixture):
    def test_loose_tail_is_judged_and_the_same_passage_is_delivered(self):
        marker = 'Rollback uses the amber switch.'
        self.note('guide', '# Overview\n\n' + ('Unrelated background material. ' * 90) + '\n\n## Recovery\n\n' + marker)
        query = 'explain rollback restoration mechanism'
        local = self.local(query)
        self.assertFalse(local['records'])
        result = self.judge(query, local, marker)
        text, _ = rt.render_context(result, 5000)
        self.assertIn(marker, text)
        self.assertIn('Recovery', self.calls[0]['state']['notes']['k0']['excerpt'])

    def test_strict_long_block_card_centres_on_query_evidence(self):
        marker = 'Quartz rollback uses the amber switch.'
        self.note('guide', 'Background context. ' * 36 + marker)
        query = 'explain quartz rollback switch'
        local = self.local(query)
        self.assertTrue(any(marker in r['text'] for r in local['records']))
        result = self.judge(query, local, marker)
        self.assertIn(marker, rt.render_context(result, 5000)[0])

    def test_newly_selected_sensitive_tail_is_still_rejected_before_transport(self):
        secret = 'sk-' + 'x' * 40
        self.note('guide', 'Background. ' * 100 + '\n\nRollback access token: ' + secret)
        query = 'explain rollback restoration mechanism'
        local = self.local(query)
        client.set_mode(self.store.state_dir, 'on', enable=['auto_context'])
        with patch.dict(os.environ, {'TYPESAFE_API_KEY': 'synthetic'}, clear=True), \
                patch.object(client, '_transport', side_effect=AssertionError('sensitive input left the machine')):
            result = jev.auto_context(self.store, 'claude', query, local, budget_chars=5000)
        self.assertIs(result, local)

    def test_second_strict_passage_is_represented_on_card(self):
        marker = 'Quartz rollback switch is amber.'
        self.note('guide', '# Guide\n\nQuartz rollback instructions.\n\n## Switch\n\n' + marker)
        query = 'quartz rollback instructions switch'
        local = self.local(query)
        self.assertTrue(local.wider)
        result = self.judge(query, local, marker)
        self.assertIn('Quartz rollback instructions.', self.calls[0]['state']['notes']['k0']['excerpt'])
        self.assertIn(marker, rt.render_context(result, 5000)[0])

