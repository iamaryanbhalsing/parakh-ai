import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def gen_txn_id() -> str:
    return "TXN-" + uuid.uuid4().hex[:12].upper()


class TransactionStore:
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path("data/transactions.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.txns: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.txns = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.txns = {}

    def _save(self) -> None:
        self.path.write_text(json.dumps(self.txns, indent=2), encoding="utf-8")

    def create(self, request: Any, result: Dict[str, Any]) -> str:
        txn_id = gen_txn_id()
        self.txns[txn_id] = {
            "txn_id": txn_id,
            "request": request.model_dump(mode="json"),
            "risk_score": result["score"],
            "risk_level": result["level"],
            "decision": result["decision"],
            "status": "held" if result["decision"]["action"] in ("hold", "block", "verify") else "processed",
            "override": None,
            "feedback": None,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._save()
        return txn_id

    def get(self, txn_id: str) -> Optional[Dict[str, Any]]:
        return self.txns.get(txn_id)

    def update_decision(self, txn_id: str, decision: Dict[str, Any], status: str) -> None:
        if txn_id in self.txns:
            self.txns[txn_id]["decision"] = decision
            self.txns[txn_id]["status"] = status
            self._save()

    def set_override(self, txn_id: str, override: Dict[str, Any]) -> None:
        if txn_id in self.txns:
            self.txns[txn_id]["override"] = override
            self.txns[txn_id]["status"] = "overridden"
            self._save()

    def set_feedback(self, txn_id: str, feedback: Dict[str, Any]) -> None:
        if txn_id in self.txns:
            self.txns[txn_id]["feedback"] = feedback
            if feedback.get("label") == "false_positive":
                self.txns[txn_id]["status"] = "false_positive"
            self._save()

    def reset(self) -> None:
        self.txns = {}
        self._save()

    def all(self) -> list:
        return sorted(self.txns.values(), key=lambda t: t.get("created_at", ""), reverse=True)

    def stats(self) -> Dict[str, Any]:
        txns = self.txns.values()
        total = len(txns)
        held = sum(1 for t in txns if t["status"] == "held")
        processed = sum(1 for t in txns if t["status"] == "processed")
        overridden = sum(1 for t in txns if t.get("override"))
        false_positives = sum(1 for t in txns if (t.get("feedback") or {}).get("label") == "false_positive")
        critical = sum(1 for t in txns if t["risk_level"] == "critical")
        high = sum(1 for t in txns if t["risk_level"] == "high")
        fp_rate = false_positives / overridden if overridden else 0.0
        return {
            "total": total,
            "held": held,
            "processed": processed,
            "overridden": overridden,
            "false_positives": false_positives,
            "fp_rate": round(fp_rate, 4),
            "critical": critical,
            "high": high,
            "avg_risk_score": round(sum(t["risk_score"] for t in txns) / total, 2) if total else 0.0,
        }