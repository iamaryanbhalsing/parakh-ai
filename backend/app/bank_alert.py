import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, Optional


class BankAlertClient:
    def __init__(self, hmac_key: str = "dev-bank-alert-key-change-me", webhook_url: Optional[str] = None):
        self.hmac_key = hmac_key
        self.webhook_url = webhook_url
        self.history: list = []

    def _sign(self, payload: Dict[str, Any]) -> str:
        canonical = json.dumps(payload, sort_keys=True, default=str)
        return hmac.new(self.hmac_key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    def send_alert(self, txn_id: str, risk_level: str, risk_score: float, summary: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {
            "alert_id": str(uuid.uuid4()),
            "txn_id": txn_id,
            "event_type": "FRAUD_INTERVENTION",
            "risk_level": risk_level,
            "risk_score": round(risk_score, 2),
            "summary": summary,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        if extra:
            payload.update(extra)
        signature = self._sign(payload)
        record = {
            "sent": True,
            "mode": "simulated",
            "payload": payload,
            "signature": signature,
            "signature_valid": None,
        }
        self.history.append(record)
        return record

    def verify_signature(self, record: Dict[str, Any]) -> bool:
        payload = record.get("payload", {})
        signature = record.get("signature", "")
        return hmac.compare_digest(self._sign(payload), signature)

    def log(self) -> list:
        return self.history