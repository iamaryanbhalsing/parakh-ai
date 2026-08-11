from app.nlp_urgency import detect_urgency
from app.voice_analysis import analyze_voice
from app.evidence_store import EvidenceStore
from app.bank_alert import BankAlertClient
import tempfile
from pathlib import Path


def test_urgency_english():
    r = detect_urgency("Share your UPI PIN immediately or your account will be blocked. Don't tell anyone!")
    assert r["urgency_score"] >= 0.5
    assert len(r["matched_terms"]) > 0


def test_urgency_hindi():
    r = detect_urgency("तुरंत पिन बताओ, खाता ब्लॉक हो जाएगा। किसी को मत बताना।")
    assert r["language"] == "hi"
    assert r["urgency_score"] > 0.3


def test_urgency_normal():
    r = detect_urgency("Hi, I will send the rent later tonight. Thanks!")
    assert r["urgency_score"] < 0.3


def test_voice_confidence_bands():
    high = analyze_voice(0.92, 0.9, 40)
    low = analyze_voice(0.1, 0.8, 10)
    no_data = analyze_voice(None)
    assert high["band"] == "high"
    assert low["band"] == "low"
    assert no_data["verdict"] == "unavailable"


def test_voice_not_overclaiming():
    result = analyze_voice(0.55, 0.55, 3)
    assert result["verdict"] == "inconclusive"


def test_evidence_chain_integrity():
    with tempfile.TemporaryDirectory() as tmp:
        store = EvidenceStore(Path(tmp) / "chain.json")
        e1 = store.append("intervention", {"score": 90}, "TXN-1")
        e2 = store.append("override", {"reason": "test"}, "TXN-1")
        assert store.verify_chain()["verified"] is True
        assert e2["prev_hash"] == e1["hash"]
        store.chain[0]["payload"]["score"] = 10
        assert store.verify_chain()["verified"] is False


def test_bank_alert_signature():
    client = BankAlertClient(hmac_key="test-key")
    record = client.send_alert("TXN-1", "critical", 95.0, "Digital arrest scam")
    assert client.verify_signature(record) is True
    record["payload"]["risk_score"] = 1.0
    assert client.verify_signature(record) is False