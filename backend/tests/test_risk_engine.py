import math

from app.risk_engine import RiskEngine
from app.config import DEFAULT_POLICY
from app.schemas import TransactionContext, UserContext, CallContext, DeviceContext, VoiceRisk

engine = RiskEngine(DEFAULT_POLICY)


def make_txn(**kw):
    defaults = dict(
        amount=1000,
        account_balance=100000,
        balance_after_tx=99000,
        txn_amount_30d_avg=800,
        beneficiary_previous_tx_count=5,
        beneficiary_added_days_ago=200,
        txn_count_last_1h=0,
    )
    defaults.update(kw)
    return TransactionContext(**defaults)


def test_legit_low_risk():
    result = engine.score(
        make_txn(),
        UserContext(user_id="U1"),
        CallContext(),
        DeviceContext(),
        VoiceRisk(),
    )
    assert result.level == "low"
    assert result.score < 30


def test_digital_arrest_critical():
    result = engine.score(
        make_txn(amount=98000, balance_after_tx=2000, is_new_beneficiary=True, beneficiary_added_days_ago=None, beneficiary_previous_tx_count=0),
        UserContext(user_id="U1"),
        CallContext(call_type="video", call_status="active", screen_share_active=True, caller_number_not_in_contacts=True),
        DeviceContext(device_changed=True),
        VoiceRisk(),
        urgency_text="You have a digital arrest warrant. Transfer all money right now or police will come. Share your PIN.",
    )
    assert result.level == "critical"
    assert result.score >= 85


def test_balance_drain_flag():
    result = engine.score(
        make_txn(amount=95000, balance_after_tx=5000),
        UserContext(user_id="U1"),
        CallContext(),
        DeviceContext(),
        VoiceRisk(),
    )
    assert any(w == "This payment would drain most of your balance" for w in result.warnings)


def test_new_beneficiary_weight():
    low = engine.score(make_txn(beneficiary_added_days_ago=300), UserContext(user_id="U1"), CallContext(), DeviceContext(), VoiceRisk())
    high = engine.score(make_txn(beneficiary_added_days_ago=0, is_new_beneficiary=True), UserContext(user_id="U1"), CallContext(), DeviceContext(), VoiceRisk())
    assert high.score > low.score


def test_voice_risk_contributes():
    none = engine.score(make_txn(), UserContext(user_id="U1"), CallContext(), DeviceContext(), VoiceRisk(acoustic_clone_probability=None))
    cloned = engine.score(make_txn(), UserContext(user_id="U1"), CallContext(call_type="phone", call_status="active"), DeviceContext(), VoiceRisk(acoustic_clone_probability=0.9, model_confidence=0.95))
    assert cloned.score > none.score


def test_score_bounds():
    for _ in range(20):
        result = engine.score(
            make_txn(amount=50000 * (_ + 1), is_new_beneficiary=True, beneficiary_added_days_ago=None, beneficiary_previous_tx_count=0),
            UserContext(user_id="U1", flagged_vulnerable=True),
            CallContext(call_type="video", screen_share_active=True),
            DeviceContext(device_changed=True),
            VoiceRisk(acoustic_clone_probability=0.9, model_confidence=0.9),
            urgency_text="Urgent! Transfer immediately! Pay now! Tell me the OTP.",
        )
        assert 0 <= result.score <= 100
        assert result.level in ("low", "medium", "high", "critical")


def test_explainability():
    result = engine.score(
        make_txn(is_new_beneficiary=True, beneficiary_added_days_ago=None, beneficiary_previous_tx_count=0),
        UserContext(user_id="U1"),
        CallContext(call_type="phone", call_status="active", screen_share_active=True),
        DeviceContext(),
        VoiceRisk(),
    )
    assert len(result.explanation) >= 8
    assert len(result.contributions) == 8
    total = sum(c.contribution for c in result.contributions)
    assert result.score >= total * engine.SENSITIVITY_PENALTY - 1
    assert result.score <= total + 30
    assert any("pattern" in e.lower() or "pressure" in e.lower() for e in result.explanation)