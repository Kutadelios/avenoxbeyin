"""Advisory memory auditor: evaluates notes for near-duplicates, staleness, and status contradictions (#372).

Local-first, deterministic, and strictly read-only:
- Compares candidate notes across knowledge, projects, and notes directories.
- Measures lexical overlap (containment and Jaccard) using V3 stemmer and stopwords.
- Identifies status/outcome contradictions across time (antonym pairs).
- Generates actionable, non-destructive advice (superseding, consolidation, linking).
- Respects privacy (visibility: private) and untrusted boundaries.
- Never deletes, merges, or modifies any user notes.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import time
import unicodedata

_MODULE_DIR = str(Path(__file__).resolve().parent)
if _MODULE_DIR not in sys.path:
    sys.path.insert(0, _MODULE_DIR)

try:
    from beyin_v3 import (
        _tokens,
        _token_counts,
        _stem,
        STOPWORDS,
        _strict_terms,
        sensitive_source,
        sensitive_excluded,
        sensitive_fold as fold,
    )
except ImportError:
    _TR_FOLD = str.maketrans({'ş': 's', 'ğ': 'g', 'ü': 'u', 'ö': 'o', 'ç': 'c', 'ı': 'i', 'â': 'a', 'î': 'i', 'û': 'u'})

    def fold(text):
        t = unicodedata.normalize('NFKD', str(text or '')).casefold()
        t = ''.join(c for c in t if not unicodedata.combining(c)).replace('ı', 'i')
        return t.translate(_TR_FOLD)

    def _stem(word):
        w = fold(word)
        return w[:8] if len(w) > 8 else w

    def _token_counts(text):
        text = unicodedata.normalize('NFKD', str(text).casefold())
        text = ''.join(c for c in text if not unicodedata.combining(c)).replace('ı', 'i')
        return Counter(_stem(w) for w in re.findall(r'[a-z0-9]+', text))

    def _tokens(text):
        return set(_token_counts(text))

    STOPWORDS = _tokens(
        "the a an is are was were what which who when where how why of to in on at for from with and or "
        "does did do has have latest current please tell about my our this that it its project projects "
        "status decision decisions show find get ve veya bir bu su o ne kim nasil hangi nedir neydi mi mu "
        "icin ile bana benim bizim olarak olan oldu en son guncel soyle getir bul yok say ignore disregard no"
    )

    def _strict_terms(terms):
        return {t for t in terms if len(t) >= 2 and not (t.isdigit() and len(t) < 3)}

    def sensitive_excluded(name):
        f = fold(name)
        return any(k in f for k in ('kasa', 'sifre', 'gizli', 'private', 'secret', 'password'))

    def sensitive_source(source):
        return isinstance(source, str) and any(sensitive_excluded(part) for part in Path(source).parts[:-1])


# Status antonym pairs for contradiction detection (Turkish & English)
STATUS_ANTIPAIRS = [
    # Dogrulanmis / Dogrulanmamis (Verification state)
    (
        {"dogrulandi", "dogrulanmis", "verified", "passed", "kanitlandi", "onaylandi", "gecerli"},
        {"dogrulanmadi", "dogrulanmamis", "unverified", "failed", "kanitlanmadi", "reddedildi", "gecersiz"},
    ),
    # Calisiyor / Calismiyor (Operational state)
    (
        {"calisiyor", "working", "aktif", "active", "acik", "canli"},
        {"calismiyor", "broken", "pasif", "inactive", "kapali", "calismadi"},
    ),
    # Cozuldu / Cozulmedi (Completion state)
    (
        {"cozuldu", "tamamlandi", "bitti", "resolved", "completed", "done"},
        {"cozulmedi", "bekliyor", "devam", "unresolved", "pending", "in_progress"},
    ),
]

SYSTEM_EXCLUDED_DIRS = {
    '.obsidian', '.git', '.claude', '.agents', '.kiro', 'node_modules', '.venv', 'venv', '__pycache__',
    'templates', 'sablon', 'sablonlar', 'archive', 'archives', 'arsiv', 'arsivler', 'raw', 'receipts', 'daily'
}

SYSTEM_EXCLUDED_FILES = {
    'claude.md', 'agents.md', 'readme.md', 'core.md', 'soul.md', 'kurallar.md', 'last-session.md',
    'threads.md', 'journal.md', 'beyin.py'
}


def parse_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Parse YAML or JSON frontmatter and return (metadata, body)."""
    if not text.startswith('---'):
        return {}, text
    lines = text.splitlines(keepends=True)
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end = i
            break
    if end is None:
        return {}, text
    header = ''.join(lines[1:end]).strip()
    body = ''.join(lines[end + 1:]).strip()
    if header.startswith('{'):
        try:
            data = json.loads(header)
            if isinstance(data, dict):
                return data, body
        except Exception:
            return {}, body
    meta = {}
    for line in header.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'^([A-Za-z0-9_-]+)\s*:\s*(.*)$', line)
        if m:
            key, raw_val = m.group(1), m.group(2).strip()
            if ' #' in raw_val:
                raw_val = raw_val.split(' #')[0].strip()
            if (raw_val.startswith('"') and raw_val.endswith('"')) or (raw_val.startswith("'") and raw_val.endswith("'")):
                val = raw_val[1:-1]
            elif raw_val.startswith('[') and raw_val.endswith(']'):
                val = [item.strip().strip('"\'') for item in raw_val[1:-1].split(',') if item.strip()]
            else:
                val = raw_val
            meta[key] = val
    return meta, body


def parse_date_to_timestamp(val: str | None) -> float | None:
    if not val or not isinstance(val, str):
        return None
    val_str = val.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(val_str[:19].replace('T', ' '), fmt[:len(val_str[:19].replace('T', ' '))])
            return dt.replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return None


def _index_excluded_predicate(state: Path | None, vault: Path):
    if state is None:
        return lambda name: False
    try:
        from beyin_v3_index import dir_key, exclusions
        keys = exclusions(state, vault)[0]
    except Exception:
        keys = frozenset()
    if not keys:
        return lambda name: False
    return lambda name: dir_key(name) in keys


def scan_audit_candidates(vault: Path, state: Path | None = None) -> list[dict]:
    """Scan auditable markdown notes from the vault while enforcing safety and boundary rules."""
    vault = Path(vault).resolve()
    candidates = []
    is_index_excluded = _index_excluded_predicate(state, vault)

    for root_str, dirs, files in os.walk(vault):
        root_path = Path(root_str)
        # Prune system/excluded directories
        pruned_dirs = []
        for d in dirs:
            dfold = fold(d)
            if d.startswith('.') or dfold in SYSTEM_EXCLUDED_DIRS or sensitive_excluded(d) or is_index_excluded(d):
                pruned_dirs.append(d)
        for d in pruned_dirs:
            dirs.remove(d)

        for f in files:
            if not f.endswith('.md'):
                continue
            if fold(f) in SYSTEM_EXCLUDED_FILES:
                continue

            full_path = root_path / f
            try:
                rel_path = full_path.relative_to(vault).as_posix()
            except ValueError:
                rel_path = full_path.as_posix()

            if sensitive_source(rel_path):
                continue

            try:
                content = full_path.read_text(encoding='utf-8', errors='replace')
            except OSError:
                continue

            meta, body = parse_frontmatter_and_body(content)

            # Enforce privacy boundary: private notes are not candidates for overlap/leak reporting
            if str(meta.get('visibility', '')).lower() == 'private':
                continue

            # Enforce trust boundary: untrusted sources are skipped
            if (
                str(meta.get('trust', '')).lower() == 'untrusted'
                or meta.get('trusted') is False
                or str(meta.get('status', '')).lower() == 'untrusted'
                or str(meta.get('kind', '')).lower() == 'untrusted'
            ):
                continue

            # Extract title
            title = str(meta.get('title') or '').strip()
            if not title:
                for line in body.splitlines():
                    if line.startswith('# '):
                        title = line[2:].strip()
                        break
            if not title:
                title = full_path.stem

            # Extract timestamps
            created_val = meta.get('created') or meta.get('created_at') or meta.get('date')
            created_ts = parse_date_to_timestamp(created_val)
            modified_val = meta.get('modified') or meta.get('updated_at') or meta.get('modified_at')
            updated_ts = parse_date_to_timestamp(modified_val)
            if updated_ts is None:
                try:
                    updated_ts = full_path.stat().st_mtime
                except OSError:
                    updated_ts = 0.0
            if created_ts is None:
                created_ts = updated_ts

            # Extract tokens
            body_tokens = _strict_terms(_tokens(body) - STOPWORDS)
            title_tokens = _strict_terms(_tokens(title) - STOPWORDS)
            all_tokens = body_tokens | title_tokens

            # Word count
            words_count = len(re.findall(r'\w+', body))

            # Supersedes references
            supersedes = meta.get('supersedes', [])
            if isinstance(supersedes, str):
                supersedes = [supersedes]
            elif not isinstance(supersedes, list):
                supersedes = []

            candidates.append({
                'path': rel_path,
                'full_path': full_path,
                'title': title,
                'tokens': all_tokens,
                'status': str(meta.get('status', '')).lower().strip(),
                'created_ts': created_ts,
                'updated_ts': updated_ts,
                'words_count': words_count,
                'supersedes': [str(s).strip() for s in supersedes if s],
            })

    return candidates


def _detect_status_conflict(older: dict, newer: dict) -> dict | None:
    """Detect status or outcome contradiction between an older note and a newer note."""
    older_tokens = older['tokens'] | _tokens(older.get('status', ''))
    newer_tokens = newer['tokens'] | _tokens(newer.get('status', ''))

    for group_pos, group_neg in STATUS_ANTIPAIRS:
        # Check: older had positive, newer has negative
        pos_in_older = older_tokens & group_pos
        neg_in_newer = newer_tokens & group_neg
        if pos_in_older and neg_in_newer:
            return {
                'older_term': sorted(pos_in_older)[0],
                'newer_term': sorted(neg_in_newer)[0],
                'direction': 'positive_to_negative',
            }

        # Check: older had negative, newer has positive
        neg_in_older = older_tokens & group_neg
        pos_in_newer = newer_tokens & group_pos
        if neg_in_older and pos_in_newer:
            return {
                'older_term': sorted(neg_in_older)[0],
                'newer_term': sorted(pos_in_newer)[0],
                'direction': 'negative_to_positive',
            }

    return None


def _evaluate_pair(a: dict, b: dict, threshold: float, min_shared: int) -> dict | None:
    """Evaluate two candidate notes for lexical overlap, status contradiction, and context bloat."""
    tokens_a = a['tokens']
    tokens_b = b['tokens']
    if not tokens_a or not tokens_b:
        return None

    shared = tokens_a & tokens_b
    shared_count = len(shared)
    if shared_count < min_shared:
        return None

    min_vocab = min(len(tokens_a), len(tokens_b))
    if min_vocab == 0:
        return None

    overlap = shared_count / min_vocab
    if overlap < threshold:
        return None

    union_count = len(tokens_a | tokens_b)
    jaccard = (shared_count / union_count) if union_count else 0.0

    # Determine temporal order
    time_a = a.get('updated_ts') or a.get('created_ts') or 0.0
    time_b = b.get('updated_ts') or b.get('created_ts') or 0.0
    if time_a < time_b:
        older, newer = a, b
    elif time_b < time_a:
        older, newer = b, a
    else:
        # Tie-break deterministically by path
        if a['path'] <= b['path']:
            older, newer = a, b
        else:
            older, newer = b, a

    # If newer note explicitly supersedes older note, it is already resolved
    older_stem = Path(older['path']).stem
    if any(ref in (older['path'], older_stem) for ref in newer.get('supersedes', [])):
        return None

    conflict = _detect_status_conflict(older, newer)
    novel_newer = sorted(newer['tokens'] - older['tokens'])
    novel_sample = novel_newer[:6]

    # Context bloat heuristic
    context_bloat = older['words_count'] >= 500 and newer['words_count'] >= 500 and overlap >= 0.70

    if conflict:
        finding_type = 'status_contradiction'
        severity = 'warning'
        recom = (
            f"Eski kayittaki durum ('{conflict['older_term']}') yeni kayitta ('{conflict['newer_term']}') "
            f"olarak degismis gorunuyor. Eski kaydi tarihsel (supersedes veya status: archived) olarak "
            f"isaretlemeyi ya da guncel durumu tek kaynakta toplamayi degerlendir."
        )
    elif overlap >= 0.80:
        finding_type = 'near_duplicate'
        severity = 'warning' if overlap >= 0.85 else 'info'
        pct = int(round(overlap * 100))
        recom = (
            f"Iki kayit buyuk olcude ortusuyor (%{pct}). Ayri not acmak yerine '{older['path']}' "
            f"kaydini guncellemek veya yeni bulgulari mevcut nota eklemek baglam yukunu azaltabilir."
        )
    else:
        finding_type = 'substantial_overlap'
        severity = 'info'
        pct = int(round(overlap * 100))
        novel_str = ', '.join(f"'{w}'" for w in novel_sample[:4]) if novel_sample else 'ek kavramlar'
        recom = (
            f"Notlar ortak bir konuyu paylasiyor (%{pct} ortusme). Yeni not {novel_str} gibi ek kavramlar "
            f"iceriyor; bagimsiz bir dogrulama veya ayri bir deneme amaci tasimiyorsa iki notu birbirine "
            f"baglamayi ([[link]]) veya tek kaynakta birlestirmeyi degerlendir."
        )

    finding = {
        'type': finding_type,
        'severity': severity,
        'older_note': older['path'],
        'newer_note': newer['path'],
        'overlap': round(overlap, 3),
        'jaccard': round(jaccard, 3),
        'shared_terms_count': shared_count,
        'shared_terms_sample': sorted(shared)[:8],
        'novel_terms_newer_sample': novel_sample,
        'words_older': older['words_count'],
        'words_newer': newer['words_count'],
        'recommendation': recom,
    }
    if conflict:
        finding['conflict'] = conflict
    if context_bloat:
        finding['context_bloat'] = True

    return finding


def audit_memory(
    vault: Path | str,
    state: Path | str | None = None,
    target_file: str | Path | None = None,
    threshold: float = 0.60,
    min_shared: int = 5,
    limit: int = 20,
) -> dict:
    """Audit vault memory for near-duplicates, staleness, and contradictions."""
    vault = Path(vault).resolve()
    state = Path(state).resolve() if state else None

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    if min_shared < 1:
        raise ValueError("min_shared must be at least 1")

    candidates = scan_audit_candidates(vault, state=state)
    target_rel = None
    target_candidate = None

    if target_file:
        target_path = Path(target_file)
        if not target_path.is_absolute():
            target_path = (vault / target_path).resolve()
        else:
            target_path = target_path.resolve()

        if not target_path.is_file():
            raise FileNotFoundError(f"Target file not found: {target_file}")

        try:
            target_rel = target_path.relative_to(vault).as_posix()
        except ValueError:
            target_rel = target_path.as_posix()

        # Find or construct target candidate
        for c in candidates:
            if c['path'] == target_rel:
                target_candidate = c
                break

        if target_candidate is None:
            # File may be outside regular candidate directories; load directly
            try:
                content = target_path.read_text(encoding='utf-8', errors='replace')
                meta, body = parse_frontmatter_and_body(content)
                title = str(meta.get('title') or '').strip() or target_path.stem
                body_tokens = _strict_terms(_tokens(body) - STOPWORDS)
                title_tokens = _strict_terms(_tokens(title) - STOPWORDS)
                all_tokens = body_tokens | title_tokens
                created_ts = parse_date_to_timestamp(meta.get('created') or meta.get('date'))
                updated_ts = parse_date_to_timestamp(meta.get('modified') or meta.get('updated_at'))
                if updated_ts is None:
                    updated_ts = target_path.stat().st_mtime
                if created_ts is None:
                    created_ts = updated_ts
                target_candidate = {
                    'path': target_rel,
                    'full_path': target_path,
                    'title': title,
                    'tokens': all_tokens,
                    'status': str(meta.get('status', '')).lower().strip(),
                    'created_ts': created_ts,
                    'updated_ts': updated_ts,
                    'words_count': len(re.findall(r'\w+', body)),
                    'supersedes': meta.get('supersedes', []),
                }
            except OSError as exc:
                raise RuntimeError(f"Could not read target file: {exc}")

    findings = []
    pairs_compared = 0

    if target_candidate:
        for c in candidates:
            if c['path'] == target_candidate['path']:
                continue
            pairs_compared += 1
            f = _evaluate_pair(target_candidate, c, threshold=threshold, min_shared=min_shared)
            if f:
                findings.append(f)
    else:
        # Inverted index for fast candidate selection
        token_to_cand = {}
        for idx, c in enumerate(candidates):
            for t in c['tokens']:
                token_to_cand.setdefault(t, []).append(idx)

        evaluated_pairs = set()
        for i, c in enumerate(candidates):
            shared_with = Counter()
            for t in c['tokens']:
                for j in token_to_cand.get(t, []):
                    if j > i:
                        shared_with[j] += 1
            for j, count in shared_with.items():
                if count >= min_shared:
                    pair_key = (i, j)
                    if pair_key not in evaluated_pairs:
                        evaluated_pairs.add(pair_key)
                        pairs_compared += 1
                        f = _evaluate_pair(candidates[i], candidates[j], threshold=threshold, min_shared=min_shared)
                        if f:
                            findings.append(f)

    # Sort findings: status contradictions first, then highest overlap
    type_priority = {'status_contradiction': 0, 'near_duplicate': 1, 'substantial_overlap': 2}
    findings.sort(key=lambda item: (type_priority.get(item['type'], 3), -item['overlap']))
    findings = findings[:limit]

    return {
        'schema': 1,
        'vault': str(vault),
        'target': target_rel,
        'notes_scanned': len(candidates),
        'pairs_compared': pairs_compared,
        'threshold': threshold,
        'min_shared': min_shared,
        'findings': findings,
    }


def format_audit_human(report: dict) -> str:
    """Format auditor report as clean ASCII Turkish terminal output."""
    lines = ['=== Ikinci Beyin Hafiza Denetim Raporu (Auditor) ===\n']
    target = report.get('target')
    notes_scanned = report.get('notes_scanned', 0)
    pairs_compared = report.get('pairs_compared', 0)
    findings = report.get('findings', [])

    if target:
        lines.append(f"Hedef Not: {target}")
        lines.append(f"Karsilastirilan Not: {notes_scanned} | Bulgu: {len(findings)}\n")
    else:
        lines.append(f"Taranan Not: {notes_scanned} | Aday Karsilastirma: {pairs_compared} | Bulgu: {len(findings)}\n")

    if not findings:
        lines.append("Belirgin bir tekrar, celiski veya guncellik sorunu tespit edilmedi; hafiza durumu dengeli.")
        return '\n'.join(lines)

    contradictions = [f for f in findings if f.get('type') == 'status_contradiction']
    duplicates = [f for f in findings if f.get('type') == 'near_duplicate']
    overlaps = [f for f in findings if f.get('type') == 'substantial_overlap']

    if contradictions:
        lines.append("[Celiski ve Guncellik Sinyalleri]")
        for c in contradictions:
            lines.append(f"  - {c['older_note']} <-> {c['newer_note']}")
            pct = int(round(c.get('overlap', 0) * 100))
            lines.append(f"    Ortusme: %{pct} ({c.get('shared_terms_count', 0)} ortak terim)")
            conf = c.get('conflict', {})
            if conf:
                lines.append(f"    Eski durum: \"{conf.get('older_term')}\" -> Yeni durum: \"{conf.get('newer_term')}\"")
            lines.append(f"    Tavsiye: {c.get('recommendation', '')}")
            lines.append("")

    if duplicates:
        lines.append("[Yuksek Tekrar ve Ortusme]")
        for d in duplicates:
            lines.append(f"  - {d['older_note']} <-> {d['newer_note']}")
            pct = int(round(d.get('overlap', 0) * 100))
            lines.append(f"    Ortusme: %{pct} ({d.get('shared_terms_count', 0)} ortak terim)")
            nov = d.get('novel_terms_newer_sample', [])
            if nov:
                lines.append(f"    Yeni terimler: {', '.join(nov[:5])}")
            if d.get('context_bloat'):
                lines.append(f"    Baglam boyutu: {d.get('words_older', 0)} ve {d.get('words_newer', 0)} kelime")
            lines.append(f"    Tavsiye: {d.get('recommendation', '')}")
            lines.append("")

    if overlaps:
        lines.append("[Kismi Ortusme ve Iliskilendirme]")
        for o in overlaps:
            lines.append(f"  - {o['older_note']} <-> {o['newer_note']}")
            pct = int(round(o.get('overlap', 0) * 100))
            lines.append(f"    Ortusme: %{pct} ({o.get('shared_terms_count', 0)} ortak terim)")
            nov = o.get('novel_terms_newer_sample', [])
            if nov:
                lines.append(f"    Ek kavramlar: {', '.join(nov[:5])}")
            lines.append(f"    Tavsiye: {o.get('recommendation', '')}")
            lines.append("")

    lines.append("[Denetci Siniri]")
    lines.append("  Benzerlik tek basina gereksizlik degildir; bagimsiz dogrulamalar ve kanitlar")
    lines.append("  korunmaya deger olabilir. Denetci yalniz tavsiye verir; hicbir notu silmez.")
    return '\n'.join(lines)
