from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_score_digital_arrest():
    payload = {
        "transaction": {
            "amount": 98000,
            "account_balance": 100000,
            "balance_after_tx": 2000,
            "txn_amount_30d_avg": 1500,
            "txn_amount_30d_max": 4000,
            "is_new_beneficiary": True,
            "beneficiary_previous_tx_count": 0,
            "txn_count_last_1h": 0,
        },
        "user": {"user_id": "USR-1", "age": 60},
        "call": {"call_type": "video", "call_status": "active", "screen_share_active": True, "caller_number_not_in_contacts": True},
        "device": {"device_changed": True},
        "voice": {"acoustic_clone_probability": 0.2},
        "urgency_text": "You are under digital arrest. Transfer all money NOW. Don't tell anyone. Share your PIN.",
    }
    r = client.post("/api/score", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["risk_level"] == "critical"
    assert body["risk_score"] >= 85
    assert body["decision"]["action"] in ("hold", "block", "cooling_off_wallet", "verify")
    assert body["intervention_required"] is True
    assert body["evidence_id"]
    assert body["bank_alert_id"]


def test_score_legit_low():
    payload = {
        "transaction": {
            "amount": 500,
            "account_balance": 100000,
            "balance_after_tx": 99500,
            "txn_amount_30d_avg": 600,
            "txn_amount_30d_max": 2000,
            "is_new_beneficiary": False,
            "beneficiary_added_days_ago": 300,
            "beneficiary_previous_tx_count": 20,
            "txn_count_last_1h": 0,
        },
        "user": {"user_id": "USR-2"},
        "urgency_text": "Thanks, will transfer rent later.",
    }
    r = client.post("/api/score", json=payload)
    body = r.json()
    assert body["risk_level"] == "low"
    assert body["intervention_required"] is False


def test_full_flow_proceed_and_feedback():
    payload = {
        "transaction": {
            "amount": 50000,
            "account_balance": 80000,
            "balance_after_tx": 30000,
            "txn_amount_30d_avg": 1200,
            "is_new_beneficiary": True,
            "beneficiary_added_days_ago": 1,
            "txn_count_last_1h": 1,
        },
        "user": {"user_id": "USR-3"},
        "call": {"call_type": "phone", "call_status": "active", "screen_share_active": True, "caller_number_not_in_contacts": True},
        "device": {"device_changed": True},
        "urgency_text": "Pay immediately or your account will be blocked.",
    }
    r = client.post("/api/score", json=payload)
    txn_id = r.json()["txn_id"]
    assert r.json()["intervention_required"] is True

    pr = client.post("/api/proceed", json={"txn_id": txn_id, "verification_method": "otp"})
    assert pr.status_code == 200
    assert pr.json()["status"] == "released"

    fb = client.post("/api/feedback", json={"txn_id": txn_id, "rating": 2, "label": "false_positive", "comment": "was a legit payment"})
    assert fb.status_code == 200

    ev = client.get(f"/api/evidence/{txn_id}")
    assert ev.status_code == 200
    assert len(ev.json()["entries"]) >= 3

    chain = client.get("/api/evidence/chain/verify")
    assert chain.json()["verified"] is True


def test_cancel_flow():
    payload = {
        "transaction": {"amount": 20000, "account_balance": 50000, "balance_after_tx": 30000, "txn_amount_30d_avg": 1500},
        "user": {"user_id": "USR-4"},
        "call": {"call_type": "video", "screen_share_active": True},
    }
    r = client.post("/api/score", json=payload)
    txn_id = r.json()["txn_id"]
    c = client.post("/api/cancel", json={"txn_id": txn_id})
    assert c.json()["status"] == "cancelled"


def test_override_and_stats():
    payload = {
        "transaction": {"amount": 30000, "account_balance": 60000, "balance_after_tx": 30000, "txn_amount_30d_avg": 2000},
        "user": {"user_id": "USR-5"},
    }
    r = client.post("/api/score", json=payload)
    txn_id = r.json()["txn_id"]
    ov = client.post("/api/override", json={
        "txn_id": txn_id, "override_to": "medium",
        "reason": "Known vendor, customer confirmed",
        "verified_via_otp": True,
    })
    assert ov.status_code == 200
    assert ov.json()["status"] == "overridden"

    st = client.get("/api/stats")
    assert st.status_code == 200
    assert st.json()["total"] >= 5
    assert "fp_rate" in st.json()