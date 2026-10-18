import re
from collections import defaultdict

STATUS_ANTIPAIRS = {
    frozenset(['active', 'done']),
    frozenset(['active', 'cancelled']),
    frozenset(['waiting', 'done']),
    frozenset(['waiting', 'cancelled']),
}

class MemoryAuditor:
    def __init__(self):
        # Safe O(N) tokenization avoiding ReDoS, capturing Unicode diacritics
        self.tokenizer = re.compile(r'\w+', re.UNICODE)
        self.documents = {}
        self.inverted_index = defaultdict(set)

    def add_document(self, doc_id, text, status=None, supersedes=None):
        if supersedes is None:
            supersedes = []
        elif isinstance(supersedes, str):
            supersedes = [supersedes]

        # O(N) token extraction
        tokens = set(t.lower() for t in self.tokenizer.findall(text))

        self.documents[doc_id] = {
            'id': doc_id,
            'tokens': tokens,
            'status': status,
            'supersedes': supersedes
        }

    def _build_index(self):
        superseded_ids = set()
        for doc in self.documents.values():
            for sid in doc['supersedes']:
                superseded_ids.add(sid)

        valid_docs = {k: v for k, v in self.documents.items() if k not in superseded_ids}

        self.inverted_index.clear()
        for doc_id, doc in valid_docs.items():
            for token in doc['tokens']:
                self.inverted_index[token].add(doc_id)

        return valid_docs

    def audit(self, jaccard_threshold=0.8):
        valid_docs = self._build_index()
        results = []

        for doc_id, doc in valid_docs.items():
            tokens = doc['tokens']
            if not tokens:
                continue

            candidate_counts = defaultdict(int)
            for token in tokens:
                for candidate_id in self.inverted_index[token]:
                    if candidate_id != doc_id:
                        candidate_counts[candidate_id] += 1

            for candidate_id, intersection in candidate_counts.items():
                if candidate_id <= doc_id:
                    continue

                candidate_doc = valid_docs[candidate_id]
                candidate_tokens = candidate_doc['tokens']
                union_len = len(tokens) + len(candidate_tokens) - intersection

                jaccard = intersection / union_len if union_len > 0 else 0.0

                if jaccard >= jaccard_threshold:
                    issue = {
                        'type': 'near_duplicate',
                        'doc1': doc_id,
                        'doc2': candidate_id,
                        'jaccard': jaccard
                    }

                    status1 = doc['status']
                    status2 = candidate_doc['status']

                    if status1 and status2 and status1 != status2:
                        status_pair = frozenset([status1, status2])
                        if status_pair in STATUS_ANTIPAIRS:
                            issue['type'] = 'contradiction'
                            issue['statuses'] = (status1, status2)

                    results.append(issue)

        return results
