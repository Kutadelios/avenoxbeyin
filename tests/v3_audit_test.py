import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../template/.claude/scripts')))
from beyin_v3_audit import MemoryAuditor

class TestMemoryAuditor(unittest.TestCase):
    def test_jaccard_similarity(self):
        auditor = MemoryAuditor()
        # "quick brown fox" vs "quick brown fox" (Jaccard = 1.0)
        auditor.add_document("doc1", "The quick brown fox")
        auditor.add_document("doc2", "The quick brown fox")
        # "quick brown cat" vs "quick brown fox" (Jaccard = 3/4 = 0.75)
        auditor.add_document("doc3", "The quick brown cat")

        results = auditor.audit(jaccard_threshold=0.8)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['doc1'], "doc1")
        self.assertEqual(results[0]['doc2'], "doc2")
        self.assertEqual(results[0]['type'], "near_duplicate")

    def test_redos_oom_prevention_on_large_files(self):
        auditor = MemoryAuditor()
        # 1 million "A"s followed by a space
        large_text = "A" * 1000000 + " " + "B" * 1000000
        # This shouldn't hang or cause OOM due to ReDoS
        auditor.add_document("large1", large_text)
        auditor.add_document("large2", large_text)

        results = auditor.audit(jaccard_threshold=0.9)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['jaccard'], 1.0)

    def test_unicode_tokenization(self):
        auditor = MemoryAuditor()
        auditor.add_document("tr1", "Ağaç kütüğü ve ışık")
        auditor.add_document("tr2", "Ağaç kütüğü ve ışık")

        results = auditor.audit(jaccard_threshold=0.9)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['jaccard'], 1.0)

        # Verify tokens
        tokens = auditor.documents["tr1"]["tokens"]
        self.assertIn("ağaç", tokens)
        self.assertIn("kütüğü", tokens)
        self.assertIn("ışık", tokens)

    def test_status_antipairs(self):
        auditor = MemoryAuditor()
        auditor.add_document("doc1", "Fix the login bug", status="active")
        auditor.add_document("doc2", "Fix the login bug", status="done")
        auditor.add_document("doc3", "Fix the login bug", status="waiting")
        auditor.add_document("doc4", "Fix the login bug", status="cancelled")

        results = auditor.audit(jaccard_threshold=0.8)

        contradictions = [r for r in results if r['type'] == 'contradiction']
        self.assertTrue(len(contradictions) > 0)

        # active/done, active/cancelled, waiting/done, waiting/cancelled are contradictions
        # Let's count them. Pairs: (doc1,doc2)=active/done, (doc1,doc4)=active/cancelled, (doc3,doc2)=waiting/done, (doc3,doc4)=waiting/cancelled
        self.assertEqual(len(contradictions), 4)

    def test_supersedes_exclusion(self):
        auditor = MemoryAuditor()
        auditor.add_document("v1", "Complete feature X", status="active")
        auditor.add_document("v2", "Complete feature X with Y", status="done", supersedes=["v1"])

        # v1 is superseded, so it should not be included in the index and thus no conflict
        results = auditor.audit(jaccard_threshold=0.5)
        self.assertEqual(len(results), 0)

if __name__ == '__main__':
    unittest.main()
