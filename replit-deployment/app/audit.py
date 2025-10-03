# app/audit.py
"""
Tamper-evident audit log for Jimini.

- Appends line-delimited JSON AuditRecord entries to logs/audit.jsonl
- Each record links to the previous via a SHA3-256 chain hash
- verify_chain() replays and validates the entire chain
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from typing import Iterator, Optional, Dict, Any, List

from pydantic import ValidationError
from app.models import AuditRecord

# ---------- Paths & constants ----------
AUDIT_FILE: Path = Path(os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl"))
AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

# 64 hex chars (fits sha256/sha3_256)
GENESIS_PREV: str = "0" * 64


# ---------- Helpers ----------
def _canonical_json(obj: Dict[str, Any]) -> str:
    """Stable JSON (no spaces) for deterministic hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _sha3_256_hex(s: str) -> str:
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()


def iter_audits() -> Iterator[AuditRecord]:
    """
    Yield AuditRecord items from the log (skip malformed or invalid lines).
    """
    if not AUDIT_FILE.exists():
        return
    with AUDIT_FILE.open("r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            try:
                data: Dict[str, Any] = json.loads(line)
                yield AuditRecord(**data)
            except (json.JSONDecodeError, TypeError, ValueError, ValidationError):
                # Skip malformed or invalid record lines
                continue


def _last_hash() -> Optional[str]:
    """Return the last chain_hash in the file (or None if empty)."""
    last: Optional[AuditRecord] = None
    for rec in iter_audits():
        last = rec
    return getattr(last, "chain_hash", None) if last else None


# ---------- Public API ----------
def append_audit(rec: AuditRecord) -> None:
    """
    Append an AuditRecord with hash chaining.

    chain_hash = SHA3-256(prev_hash + canonical_json(payload_without_hashes))
    """
    prev: str = _last_hash() or GENESIS_PREV

    # Build payload excluding hashes for canonicalization
    payload: Dict[str, Any] = {
        "timestamp": rec.timestamp,
        "request_id": rec.request_id,
        "action": rec.action,
        "direction": rec.direction,
        "endpoint": rec.endpoint,
        "rule_ids": rec.rule_ids,
        "text_excerpt": rec.text_excerpt,
    }
    payload_json: str = _canonical_json(payload)
    chain: str = _sha3_256_hex(prev + payload_json)

    # Only assign fields that exist on AuditRecord
    rec.previous_hash = prev
    rec.text_hash = chain

    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(rec.model_dump_json() + "\n")


def verify_chain() -> Dict[str, Any]:
    """
    Recompute the chain from the beginning.
    Returns: {"valid": bool, "break_index": Optional[int], "count": int}
    break_index points to first broken record (0-based).
    """
    prev: str = GENESIS_PREV
    count: int = 0

    for idx, rec in enumerate(iter_audits()):
        # Skip validation for records without proper hashes (legacy records)
        if not rec.previous_hash or not rec.text_hash:
            return {"valid": False, "break_index": idx, "count": idx}

        # Reconstruct payload as when written
        payload: Dict[str, Any] = {
            "timestamp": rec.timestamp,
            "request_id": rec.request_id,
            "action": rec.action,
            "direction": rec.direction,
            "endpoint": rec.endpoint,
            "rule_ids": rec.rule_ids,
            "text_excerpt": rec.text_excerpt,
        }
        expected: str = _sha3_256_hex(prev + _canonical_json(payload))

        if rec.previous_hash != prev or rec.text_hash != expected:
            return {"valid": False, "break_index": idx, "count": idx}

        # Type is now narrowed to str (not Optional) thanks to the None check above
        prev = rec.text_hash
        count += 1

    return {"valid": True, "break_index": None, "count": count}


def get_records_by_date_prefix(date_prefix: Optional[str] = None) -> List[AuditRecord]:
    """
    Get audit records filtered by date prefix.
    If date_prefix is None, returns all records.
    Date prefix should be in format like "2023-09-30" to match timestamps.
    """
    records = []
    for record in iter_audits():
        if date_prefix is None or record.timestamp.startswith(date_prefix):
            records.append(record)
    return records
