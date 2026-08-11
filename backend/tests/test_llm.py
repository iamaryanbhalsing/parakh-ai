import json

import httpx
from fastapi.testclient import TestClient

from app import llm_analysis
from app.main import app

client = TestClient(app)

CANNED_LLM = {
    "fraud_score": 0.93,
    "risk_level": "critical",
    "verdict": "FRAUD",
    "confidence": 0.91,
    "intent": "authority_impersonation",
    "intent_confidence": 0.9,
    "summary": "Caller impersonates cyber crime police and demands a transfer, ordering secrecy.",
    "suggested_action": "block",
    "red_flags": ["police impersonation", "demands transfer", "orders secrecy"],
    "entities": {"amounts": [50000], "otps": [], "phones": ["9876543210"], "institutions": ["Cyber Cell"]},
    "pattern_match": "digital-arrest impersonation",
}


def fake_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(CANNED_LLM)}}]})

    return httpx.MockTransport(handler)


def settings_with_key():
    return {
        "base_url": "https://api.mock.test/v1",
        "api_key": "sk-test-key",
        "model": "mock-model",
        "timeout": 5.0,
    }


def test_llm_unavailable_without_key():
    assert llm_analysis.llm_available({"base_url": "https://x/v1", "api_key": "", "model": "m", "timeout": 5}) is False
    assert llm_analysis.analyze_with_llm([{"speaker": "caller", "text": "hi"}], settings=settings_with_key() if False else {"base_url": "https://x/v1", "api_key": "", "model": "m", "timeout": 5}) is None


def test_llm_call_normalized():
    s = settings_with_key()
    out = llm_analysis.analyze_with_llm(
        [{"speaker": "caller", "text": "You are under arrest, transfer now"}],
        context={"transaction": {"amount": 50000}},
        settings=s,
        transport=fake_transport(),
    )
    assert out is not None
    assert out["verdict"] == "FRAUD"
    assert out["fraud_score"] == 0.93
    assert out["llm_model"] == "mock-model"
    assert out["llm_latency_ms"] >= 0
    assert out["entities"]["phones"] == ["9876543210"]


def test_json_extraction_with_fence_and_junk():
    content = 'Sure! Here is my analysis:\n```json\n{"fraud_score": 0.8, "verdict": "FRAUD"}\n```\nHope it helps!'
    assert llm_analysis._extract_json(content)["verdict"] == "FRAUD"
    assert llm_analysis._extract_json("not json at all") == {}


def test_normalize_clamps_bad_values():
    raw = {"fraud_score": 99, "confidence": -5, "verdict": "fraud", "intent": "weird", "suggested_action": "nuke"}
    out = llm_analysis.normalize_llm_output(raw)
    assert out["fraud_score"] == 1.0
    assert out["confidence"] == 0.0
    assert out["verdict"] == "FRAUD"
    assert out["intent"] == "other"
    assert out["suggested_action"] == "block"


def test_merge_agreement_boosts_confidence():
    nlp = {"opinion": {"verdict": "FRAUD", "confidence": 0.9, "summary": "s"}, "red_flags": ["a"], "fraud_score": 0.8, "intent": {"scores": {}}}
    llm = {**CANNED_LLM, "confidence": 0.8}
    merged = llm_analysis.merge_into_analysis(nlp, llm)
    assert merged["opinion"]["verdict"] == "FRAUD"
    assert merged["opinion"]["confidence"] > 0.8
    assert merged["engine"] == "llm"


def test_merge_disagreement_lowers_confidence():
    nlp = {"opinion": {"verdict": "FRAUD", "confidence": 0.9, "summary": "s"}, "red_flags": ["a"], "fraud_score": 0.8, "intent": {"scores": {}}}
    llm = {**CANNED_LLM, "verdict": "LEGITIMATE", "confidence": 0.9}
    merged = llm_analysis.merge_into_analysis(nlp, llm)
    assert merged["opinion"]["verdict"] == "LEGITIMATE"
    assert merged["opinion"]["confidence"] < 0.9
    assert "disagreed" in merged["opinion"]["summary"]


def test_llm_status_endpoint():
    r = client.get("/api/llm/status")
    assert r.status_code == 200
    assert "configured" in r.json()


def test_conversation_analyze_auto_falls_back_to_nlp(monkeypatch):
    monkeypatch.setenv("PARAKH_LLM_API_KEY", "")
    r = client.post("/api/conversation/analyze", json={
        "turns": [{"speaker": "s", "text": "Pay now or you will be arrested. Don't tell anyone."}],
        "engine": "auto", "persist": False,
    })
    body = r.json()
    assert r.status_code == 200
    assert body["engine"] == "nlp"
    assert body["opinion"]["verdict"] == "FRAUD"


def test_conversation_analyze_llm_engine(monkeypatch):
    monkeypatch.setenv("PARAKH_LLM_API_KEY", "sk-test")
    canned = dict(CANNED_LLM, llm_model="mock-model", llm_latency_ms=842)
    monkeypatch.setattr(llm_analysis, "analyze_with_llm",
                        lambda turns, context=None, settings=None, transport=None: canned)
    r = client.post("/api/conversation/analyze", json={
        "turns": [{"speaker": "s", "text": "Transfer all money to this account right now"}],
        "engine": "llm", "persist": False,
    })
    body = r.json()
    assert body["engine"] == "llm"
    assert body["opinion"]["verdict"] == "FRAUD"
    assert body["opinion"]["llm_model"] == "mock-model"


def test_score_use_llm_escalates_allow_to_verify(monkeypatch):
    monkeypatch.setenv("PARAKH_LLM_API_KEY", "sk-test")
    monkeypatch.setattr(llm_analysis, "analyze_with_llm",
                        lambda turns, context=None, settings=None, transport=None: dict(CANNED_LLM))
    payload = {
        "transaction": {"amount": 8000, "account_balance": 50000, "balance_after_tx": 42000,
                        "txn_amount_30d_avg": 7500, "txn_amount_30d_max": 9000,
                        "is_new_beneficiary": False, "beneficiary_added_days_ago": 200,
                        "beneficiary_previous_tx_count": 10, "txn_count_last_1h": 0},
        "user": {"user_id": "USR-LLM-1"},
        "urgency_text": "I will transfer the rent amount later this evening.",
        "transcript_turns": [{"speaker": "s", "text": "Transfer all money to this account right now"}],
        "use_llm": True,
    }
    r = client.post("/api/score", json=payload)
    body = r.json()
    assert r.status_code == 200
    assert body["decision"]["action"] == "verify"
    assert body["llm_opinion"]["verdict"] == "FRAUD"
    assert any("AI agent" in w for w in body["warnings"])


def test_score_use_llm_without_key_safe(monkeypatch):
    monkeypatch.setenv("PARAKH_LLM_API_KEY", "")
    payload = {
        "transaction": {"amount": 12000, "account_balance": 100000, "balance_after_tx": 88000,
                        "txn_amount_30d_avg": 11500, "is_new_beneficiary": False,
                        "beneficiary_added_days_ago": 300, "beneficiary_previous_tx_count": 20,
                        "txn_count_last_1h": 0},
        "user": {"user_id": "USR-LLM-2"},
        "use_llm": True,
    }
    r = client.post("/api/score", json=payload)
    body = r.json()
    assert body["risk_level"] == "low"
    assert body["llm_opinion"] is None
    assert body["intervention_required"] is False
