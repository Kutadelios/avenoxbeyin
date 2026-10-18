"""V3 Learning Candidate Ledger (RFC #368 P0-A/Package 2).

Maintains lightweight, source-linked learning candidates before knowledge distillation.
Persisted in state/learning-state.jsonl; zero network, zero external dependencies.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

LEARNING_STATE_FILE = "learning-state.jsonl"


def _atomic_append(file_path: Path, record: dict) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())


def stage_candidate(state: Path, session: str, candidate: str, source: str = "", scope: str = "global") -> dict:
    """Stage a learning candidate into learning-state.jsonl."""
    state = Path(state)
    record_id = hashlib.sha256(f"{session}:{time.time()}:{candidate}".encode("utf-8")).hexdigest()[:16]
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": record_id,
        "created_at": now,
        "session": session[:24] if session else "unknown",
        "candidate": str(candidate).strip(),
        "source": str(source).strip(),
        "scope": str(scope).strip() or "global",
        "status": "candidate"
    }
    ledger = state / LEARNING_STATE_FILE
    _atomic_append(ledger, record)
    return record


def list_candidates(state: Path, session: str | None = None, status: str = "candidate") -> list[dict]:
    """Read learning candidates matching session and status."""
    ledger = Path(state) / LEARNING_STATE_FILE
    if not ledger.is_file():
        return []
    results = []
    try:
        with open(ledger, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if session and item.get("session") != session[:24]:
                        continue
                    if status and item.get("status") != status:
                        continue
                    results.append(item)
                except Exception:
                    continue
    except OSError:
        return []
    return results


def has_candidates(state: Path, session: str | None = None) -> bool:
    """True if active candidates exist for this session (or overall)."""
    return len(list_candidates(state, session=session, status="candidate")) > 0


def resolve_candidates(state: Path, session: str, target_status: str = "distilled") -> int:
    """Mark all candidates of a session as distilled or discarded."""
    ledger = Path(state) / LEARNING_STATE_FILE
    if not ledger.is_file():
        return 0
    records = []
    count = 0
    target_session = session[:24] if session else "unknown"
    try:
        with open(ledger, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                    if item.get("session") == target_session and item.get("status") == "candidate":
                        item["status"] = target_status
                        item["resolved_at"] = datetime.now(timezone.utc).isoformat()
                        count += 1
                    records.append(item)
                except Exception:
                    continue
        # Atomic rewrite
        temp = ledger.parent / (ledger.name + ".tmp")
        with open(temp, "w", encoding="utf-8") as out:
            for rec in records:
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, ledger)
    except OSError:
        return 0
    return count
