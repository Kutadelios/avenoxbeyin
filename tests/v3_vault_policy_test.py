"""Fork vault policy: behaviour this vault keeps on top of upstream."""
import unittest

from v3_evidence_helpers import EvidenceFixture, rt


class VaultPolicyTest(EvidenceFixture):
    def test_completed_task_remains_strong_historical_passage_evidence(self):
        marker = 'Quartz rollback deployment uses the copper switch.'
        self.note('finished', marker, kind='task', status='done')
        for index in range(7):
            self.note('background' + str(index), 'Quartz rollback deployment background. ' +
                      'Unrelated furniture records. ' * 20)
        context = self.store.context_for('claude', 'quartz rollback deployment copper switch',
                                         strict=True, limit=1, budget_chars=5000)
        self.assertEqual([r['id'] for r in context['records']], ['finished'])
        self.assertIn(marker, rt.render_context(context, 4700)[0])

    def test_open_task_wins_an_exact_tie_with_a_completed_task(self):
        text = 'Quartz rollback deployment uses the copper switch.'
        self.note('closed', text, kind='task', status='done')
        self.note('open', text, kind='task', status='active')
        context = self.store.context_for('claude', 'quartz rollback deployment copper switch',
                                         strict=True, limit=1, budget_chars=5000)
        self.assertEqual([r['id'] for r in context['records']], ['open'])


if __name__ == '__main__':
    unittest.main()
