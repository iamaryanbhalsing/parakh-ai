from app.conversation_analysis import analyze_conversation, parse_transcript, extract_entities

DIGITAL_ARREST = [
    {"speaker": "s", "text": "This is Cyber Crime cell. You are under DIGITAL ARREST."},
    {"speaker": "s", "text": "A case has been filed against your Aadhaar for money laundering."},
    {"speaker": "s", "text": "Transfer all money to this account RIGHT NOW or police will come."},
    {"speaker": "s", "text": "Don't tell anyone about this call. Share your UPI PIN."},
    {"speaker": "u", "text": "But how do I know this is real? I'm scared."},
    {"speaker": "s", "text": "You will be arrested in 30 minutes. Pay now, immediately!"},
]

LEGIT_RENT = [
    {"speaker": "s", "text": "Hi, the rent for this month. Will send the receipt shortly."},
    {"speaker": "u", "text": "Got it, paying now. Thanks!"},
]


def test_digital_arrest_verdict_fraud():
    a = analyze_conversation(DIGITAL_ARREST)
    assert a["opinion"]["verdict"] == "FRAUD"
    assert a["opinion"]["confidence"] >= 0.85
    assert a["intent"]["label"] == "authority_impersonation"
    assert a["fraud_score"] >= 0.6


def test_legit_conversation_verdict_legitimate():
    a = analyze_conversation(LEGIT_RENT)
    assert a["opinion"]["verdict"] == "LEGITIMATE"
    assert a["red_flags"][0].startswith("No high-severity")


def test_short_digital_arrest_coercion_is_fraud():
    """Short coercive call with no secrecy/pressure cues must still be caught:
    confident authority-impersonation intent + authority/payment demand must
    lift the score over the FRAUD bar (regression: scored 0.347 → LEGITIMATE)."""
    a = analyze_conversation([
        {"speaker": "s", "text": "I am from the cyber cell"},
        {"speaker": "u", "text": "What?"},
        {"speaker": "s", "text": "You have a digital arrest warrant. Transfer all money or be arrested."},
    ])
    assert a["intent"]["label"] == "authority_impersonation"
    assert a["intent"]["confidence"] >= 0.6
    assert a["fraud_score"] >= 0.5
    assert a["opinion"]["verdict"] == "FRAUD"
    assert "coercive authority money demand" in a["active_patterns"]


def test_relative_emergency_hindi():
    a = analyze_conversation([
        {"speaker": "s", "text": "भाई... मैं अनजलि बोल रही हूं। मुझे अस्पताल में एडमिट कराया है।"},
        {"speaker": "s", "text": "डॉक्टर का बिल जमा करना है। तुरंत कुछ पैसे भेजो।"},
        {"speaker": "s", "text": "किसी को मत बताना। अभी भेजो, 30,000 चाहिए।"},
    ])
    assert a["language"] == "hi"
    assert a["opinion"]["verdict"] == "FRAUD"
    assert a["intent"]["label"] == "relative_emergency_fraud"
    assert 30000 in a["entities"]["amounts"]


def test_lottery_fraud_intent():
    a = analyze_conversation([
        {"speaker": "s", "text": "Congratulations! You've won the KBC grand prize of ₹25 lakh!"},
        {"speaker": "s", "text": "To release your winnings, pay the processing fee."},
        {"speaker": "s", "text": "The offer expires in 10 minutes. Send ₹12,000 right now."},
        {"speaker": "u", "text": "Wow! But why do I need to pay to receive money?"},
    ])
    assert a["opinion"]["verdict"] == "FRAUD"
    assert a["intent"]["label"] == "lottery_reward_fraud"
    assert 12000 in a["entities"]["amounts"]
    assert 2500000 in a["entities"]["amounts"]


def test_credential_request_flagged():
    a = analyze_conversation([
        {"speaker": "s", "text": "This is your bank's fraud department. Tell me the OTP you received on your phone."},
        {"speaker": "s", "text": "Your OTP is 482913. Confirm it with me right now."},
    ])
    assert a["opinion"]["verdict"] == "FRAUD"
    assert any("OTP" in f or "credentials" in f for f in a["red_flags"])


def test_short_transcript_inconclusive():
    a = analyze_conversation([{"speaker": "u", "text": "Ok thanks, will send tonight."}])
    assert a["opinion"]["verdict"] == "INCONCLUSIVE"


def test_parse_raw_lines_with_speaker_prefixes():
    turns = parse_transcript([
        "Caller: This is the police, you are under arrest.",
        "Victim: What? I didn't do anything!",
    ])
    assert [t["speaker"] for t in turns] == ["caller", "victim"]


def test_parse_single_monologue_splits():
    turns = parse_transcript("Pay now or the case will be filed. Don't tell anyone. Hurry up!")
    assert len(turns) >= 2
    assert turns[0]["speaker"] in ("caller", "victim")


def test_entity_extraction():
    e = extract_entities("Send ₹50,000 to account now. My phone is 9876543210 and OTP 452198 came.", "en")
    assert 50000 in e["amounts"]
    assert "452198" in e["otps"]
    assert any("9876543210" in p for p in e["phones"])


def test_empty_input_returns_error():
    a = analyze_conversation([])
    assert a.get("error")
