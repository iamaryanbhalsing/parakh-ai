import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any


class EvidenceStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("data/evidence_chain.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.chain: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.chain = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.chain = []

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.chain, indent=2), encoding="utf-8")

    def _hash_entry(self, entry: Dict[str, Any]) -> str:
        payload = entry.copy()
        payload.pop("hash", None)
        payload.pop("prev_hash", None)
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append(self, entry_type: str, payload: Dict[str, Any], parent_txn_id: Optional[str] = None) -> Dict[str, Any]:
        prev_hash = self.chain[-1]["hash"] if self.chain else ("0" * 64)
        entry = {
            "entry_id": str(uuid.uuid4()),
            "entry_type": entry_type,
            "txn_id": parent_txn_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "payload": payload,
            "prev_hash": prev_hash,
        }
        entry["hash"] = self._hash_entry(entry)
        self.chain.append(entry)
        self._save()
        return entry

    def verify_chain(self) -> Dict[str, Any]:
        verified = True
        first_error = None
        for i, entry in enumerate(self.chain):
            expected = entry["hash"]
            actual = self._hash_entry(entry)
            if actual != expected:
                verified = False
                first_error = {"index": i, "entry_id": entry.get("entry_id"), "reason": "hash mismatch"}
                break
            if i > 0:
                if entry["prev_hash"] != self.chain[i - 1]["hash"]:
                    verified = False
                    first_error = {"index": i, "entry_id": entry.get("entry_id"), "reason": "chain link broken"}
                    break
        return {"verified": verified, "entries": len(self.chain), "first_error": first_error}

    def find_txn(self, txn_id: str) -> List[Dict[str, Any]]:
        return [e for e in self.chain if e.get("txn_id") == txn_id]