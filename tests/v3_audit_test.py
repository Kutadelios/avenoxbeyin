"""Unit tests for advisory memory auditor (Issue #372 & RFC #368)."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_SCRIPTS = str(ROOT / 'template/.claude/scripts')
if _TEMPLATE_SCRIPTS not in sys.path:
    sys.path.insert(0, _TEMPLATE_SCRIPTS)
_SCRIPTS = str(ROOT / 'scripts')
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import beyin_v3_audit as audit_module
from beyin_entry import human_result
from tests.v3_package_helpers import inherited_env


class MemoryAuditorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v3-audit-')
        self.addCleanup(self.tmp.cleanup)
        self.vault = (Path(self.tmp.name) / 'vault').resolve()
        self.vault.mkdir()
        self.state = (Path(self.tmp.name) / 'state').resolve()
        self.state.mkdir()

        # Initialize mock runtime for beyin.py entry tests
        (self.vault / '.beyin-runtime.json').write_text(
            json.dumps({'state': str(self.state), 'schema': 1}), encoding='utf-8'
        )
        (self.vault / '.beyin-version').write_text('3.11.0\n', encoding='utf-8')
        shutil.copy2(ROOT / 'scripts/beyin_entry.py', self.vault / 'beyin.py')

        claude_scripts = self.vault / '.claude' / 'scripts'
        claude_scripts.mkdir(parents=True)
        shutil.copy2(ROOT / 'scripts/beyin_v3.py', claude_scripts / 'beyin_v3_cli.py')
        for f in (ROOT / 'template/.claude/scripts').glob('*.py'):
            shutil.copy2(f, claude_scripts / f.name)

        self.knowledge = self.vault / 'knowledge'
        self.knowledge.mkdir()

    def test_near_duplicate_detection(self):
        """Two notes on the same topic sharing > 85% vocabulary are flagged as near-duplicate."""
        note1 = self.knowledge / 'docker-setup.md'
        note1.write_text(
            "---\ntitle: Docker Kurulumu ve Ayarlari\ncreated: 2026-09-01\n---\n"
            "# Docker Kurulumu\nDocker engine kurulumu ubuntu linux sunucusunda basariyla tamamlandi. "
            "Compose dosyalari ile servisler ayaga kaldirildi. Port yonlendirmeleri ve network yapilandirmasi hazir.",
            encoding='utf-8'
        )

        note2 = self.knowledge / 'docker-setup-yeni.md'
        note2.write_text(
            "---\ntitle: Docker Kurulumu ve Yapilandirma\ncreated: 2026-10-01\n---\n"
            "# Docker Kurulumu\nDocker engine kurulumu ubuntu linux sunucusunda basariyla tamamlandi. "
            "Compose dosyalari ile servisler ayaga kaldirildi. Port yonlendirmeleri ve network yapilandirmasi hazir.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, threshold=0.60)
        self.assertEqual(report['notes_scanned'], 2)
        self.assertEqual(len(report['findings']), 1)
        finding = report['findings'][0]
        self.assertEqual(finding['type'], 'near_duplicate')
        self.assertGreaterEqual(finding['overlap'], 0.85)
        self.assertEqual(finding['severity'], 'warning')
        self.assertIn('Ayri not acmak yerine', finding['recommendation'])

    def test_status_contradiction_detection(self):
        """Detect temporal conflict when older note states unverified/failed and newer note states verified/active."""
        note_old = self.knowledge / 'postgres-baglanti-v1.md'
        note_old.write_text(
            "---\ntitle: PostgreSQL Baglanti Durumu\nupdated_at: 2026-09-10\nstatus: unverified\n---\n"
            "# PostgreSQL Baglanti\nVeritabani baglantisi henuz dogrulanmadi. "
            "Port 5432 erisilemiyor ve socket yanit vermiyor. Baglanti testi basarisiz oldu.",
            encoding='utf-8'
        )

        note_new = self.knowledge / 'postgres-baglanti-v2.md'
        note_new.write_text(
            "---\ntitle: PostgreSQL Baglanti Durumu\nupdated_at: 2026-10-15\nstatus: verified\n---\n"
            "# PostgreSQL Baglanti\nVeritabani baglantisi basariyla dogrulandi. "
            "Port 5432 uzerinden socket baglantisi kuruldu ve sorgular calisiyor. Baglanti testi basarili.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, threshold=0.50, min_shared=3)
        self.assertEqual(len(report['findings']), 1)
        finding = report['findings'][0]
        self.assertEqual(finding['type'], 'status_contradiction')
        self.assertEqual(finding['severity'], 'warning')
        self.assertIn('conflict', finding)
        conf = finding['conflict']
        self.assertIn(conf['older_term'], ('dogrulanmadi', 'unverified', 'basarisiz'))
        self.assertIn(conf['newer_term'], ('dogrulandi', 'verified', 'basarili'))
        self.assertIn('tarihsel', finding['recommendation'])

    def test_superseded_notes_are_not_flagged_as_open_conflicts(self):
        """When newer note explicitly includes supersedes: [older-note], no open conflict is raised."""
        note_old = self.knowledge / 'redis-cluster.md'
        note_old.write_text(
            "---\ntitle: Redis Cluster Mimarisi\nupdated_at: 2026-08-01\nstatus: calismiyor\n---\n"
            "Redis cluster dugumleri arasinda iletisim koptu, cluster calismiyor.",
            encoding='utf-8'
        )

        note_new = self.knowledge / 'redis-cluster-v2.md'
        note_new.write_text(
            "---\ntitle: Redis Cluster Mimarisi\nupdated_at: 2026-10-01\nsupersedes: [knowledge/redis-cluster.md]\nstatus: calisiyor\n---\n"
            "Redis cluster dugumleri sentinel ile yapilandirildi, cluster aktif calisiyor.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, threshold=0.50, min_shared=3)
        self.assertEqual(len(report['findings']), 0)

    def test_privacy_and_trust_boundary_excluded(self):
        """Notes with visibility: private, sensitive directory, or untrusted status are never audited."""
        # 1. Private note sharing content with public note
        private_note = self.knowledge / 'private-strategy.md'
        private_note.write_text(
            "---\ntitle: Gizli Strateji\nvisibility: private\n---\n"
            "Yapay zeka modelleri optimizasyon stratejisi ve butce planlamasi.",
            encoding='utf-8'
        )

        # 2. Sensitive directory note
        kasa_dir = self.vault / '🔐 Kasa'
        kasa_dir.mkdir()
        kasa_note = kasa_dir / 'finans.md'
        kasa_note.write_text(
            "---\ntitle: Finans\n---\n"
            "Yapay zeka modelleri optimizasyon stratejisi ve butce planlamasi.",
            encoding='utf-8'
        )

        # 3. Untrusted note
        untrusted_note = self.knowledge / 'untrusted-note.md'
        untrusted_note.write_text(
            "---\ntitle: Guvensiz Not\ntrust: untrusted\n---\n"
            "Yapay zeka modelleri optimizasyon stratejisi ve butce planlamasi.",
            encoding='utf-8'
        )

        # 4. Standard public note
        public_note = self.knowledge / 'ai-strateji.md'
        public_note.write_text(
            "---\ntitle: AI Stratejisi\nvisibility: internal\n---\n"
            "Yapay zeka modelleri optimizasyon stratejisi ve butce planlamasi.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, threshold=0.50, min_shared=3)
        # Only public_note should be scanned as candidate; cannot pair with private/sensitive/untrusted
        self.assertEqual(report['notes_scanned'], 1)
        self.assertEqual(len(report['findings']), 0)

    def test_negative_control_unrelated_notes(self):
        """Unrelated notes sharing no topical terms produce 0 findings."""
        note1 = self.knowledge / 'yemek-tarifi.md'
        note1.write_text(
            "---\ntitle: Menemen Tarifi\n---\n"
            "Domates, biber, yumurta ve tereyagi ile yapilan lezzetli bir kahvalti yemegi.",
            encoding='utf-8'
        )

        note2 = self.knowledge / 'kuantum-fizigi.md'
        note2.write_text(
            "---\ntitle: Kuantum Dolanillik\n---\n"
            "Fotonlar ve atomalti parcaciklarin dalga fonksiyonu cokmesi ve spin olcumu.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, threshold=0.50, min_shared=3)
        self.assertEqual(report['notes_scanned'], 2)
        self.assertEqual(len(report['findings']), 0)

    def test_target_file_specific_audit(self):
        """When target_file is supplied, only findings involving target are returned."""
        n1 = self.knowledge / 'target-test.md'
        n1.write_text(
            "---\ntitle: Test Mimarisi\n---\n"
            "Birim testleri, entegrasyon testleri ve uctan uca test kapsami otomasyonu.",
            encoding='utf-8'
        )

        n2 = self.knowledge / 'diger-test.md'
        n2.write_text(
            "---\ntitle: Test Kapsami\n---\n"
            "Birim testleri, entegrasyon testleri ve uctan uca test kapsami otomasyonu.",
            encoding='utf-8'
        )

        n3 = self.knowledge / 'alakasiz.md'
        n3.write_text(
            "---\ntitle: Bahce Bakimi\n---\n"
            "Cim bicme, sulama sistemleri ve gubreleme yontemleri.",
            encoding='utf-8'
        )

        report = audit_module.audit_memory(self.vault, state=self.state, target_file='knowledge/target-test.md', threshold=0.60, min_shared=3)
        self.assertEqual(report['target'], 'knowledge/target-test.md')
        self.assertEqual(len(report['findings']), 1)
        self.assertIn('knowledge/target-test.md', (report['findings'][0]['older_note'], report['findings'][0]['newer_note']))

    def test_cli_audit_json_and_human(self):
        """CLI invocation via beyin.py audit supports both --json and human-readable output."""
        note1 = self.knowledge / 'kavram-a.md'
        note1.write_text(
            "---\ntitle: Kavram A\nupdated_at: 2026-09-01\n---\n"
            "Mikroservis mimarisinde kafka event bus entegrasyonu ve mesaj kuyrugu yapilandirmasi.",
            encoding='utf-8'
        )

        note2 = self.knowledge / 'kavram-b.md'
        note2.write_text(
            "---\ntitle: Kavram B\nupdated_at: 2026-10-01\n---\n"
            "Mikroservis mimarisinde kafka event bus entegrasyonu ve mesaj kuyrugu yapilandirmasi.",
            encoding='utf-8'
        )

        # 1. Test CLI with --json
        cmd_json = [
            sys.executable,
            str(self.vault / '.claude/scripts/beyin_v3_cli.py'),
            '--vault', str(self.vault),
            '--state', str(self.state),
            'audit',
            '--threshold', '0.50',
            '--min-shared', '3'
        ]
        res_json = subprocess.run(cmd_json, capture_output=True, text=True, env=inherited_env())
        self.assertEqual(res_json.returncode, 0, res_json.stderr)
        data = json.loads(res_json.stdout)
        self.assertEqual(data['schema'], 1)
        self.assertEqual(len(data['findings']), 1)

        # 2. Test entrypoint with human output
        cmd_human = [
            sys.executable,
            str(self.vault / 'beyin.py'),
            'audit',
            '--threshold', '0.50',
            '--min-shared', '3',
            '--human'
        ]
        res_human = subprocess.run(cmd_human, capture_output=True, text=True, env=inherited_env())
        self.assertEqual(res_human.returncode, 0, res_human.stderr)
        self.assertIn("Ikinci Beyin Hafiza Denetim Raporu", res_human.stdout)
        self.assertIn("Yuksek Tekrar ve Ortusme", res_human.stdout)
        self.assertIn("Denetci Siniri", res_human.stdout)


if __name__ == '__main__':
    unittest.main()
