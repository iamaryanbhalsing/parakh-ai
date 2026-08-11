import random
from typing import Dict, List

URGENT_TEXTS_EN = [
    "You have a digital arrest warrant. Transfer ₹50,000 immediately to avoid arrest.",
    "I am from bank customer care. Share your UPI PIN now to stop the account freeze.",
    "Your parcel contains drugs. Pay the fine right now or police will come.",
    "You won a lottery. Send money for processing fees urgently.",
    "This is your last warning. Pay the bail amount immediately.",
    "Tell me the OTP you received. Don't tell anyone about this call.",
    "Your account will be blocked. Transfer all funds to this account now.",
    "Please share the PIN to verify. Keep it secret.",
]

LEGIT_TEXTS_EN = [
    "Hello, I will transfer the rent amount to you later this evening.",
    "Please send the groceries bill amount when you are free.",
    "Confirmed, I received the payment. Thank you for sending it.",
    "Home delivery is at the gate. Please pay the delivery guy.",
]

URGENT_TEXTS_HI = [
    "आपके खाते पर डिजिटल अरेस्ट है। तुरंत ₹50,000 ट्रांसफर करें।",
    "मैं बैंक कर्मचारी हूं। खाता ब्लॉक होने से बचने के लिए ओटीपी बताएं।",
    "पुलिस केस हुआ है। जमानत के लिए तुरंत पैसे भेजो।",
    "किसी को मत बताना, गुप्त रखो। अभी पिन साझा करो।",
]

LEGIT_TEXTS_HI = [
    "रात को मिलकर खाना खाएंगे। घर के लिए कुछ सामान ले आओ।",
    "किराया कल भेज दूंगा। धन्यवाद।",
]

SCAM_PRESETS = ["digital_arrest", "bank_impersonation", "courier_drugs", "lottery_fraud", "relative_emergency"]
LEGIT_PRESETS = ["rent_payment", "bill_payment", "merchant_payment", "family_transfer"]


def generate_scenario(preset: str, rng: random.Random) -> Dict:
    base = {
        "preset": preset,
        "user_id": f"USR-{rng.randint(1000, 9999)}",
        "age": rng.randint(24, 75),
        "account_balance": rng.uniform(5000, 250000),
        "txn_amount_30d_avg": rng.uniform(500, 8000),
        "txn_amount_30d_max": rng.uniform(2000, 20000),
        "beneficiary_previous_tx_count": rng.randint(0, 50),
        "txn_count_last_1h": rng.randint(0, 5),
        "frequency_30d": rng.randint(1, 40),
        "unusual_hour": rng.random() < 0.2,
    }

    if preset in SCAM_PRESETS:
        if preset == "digital_arrest":
            base.update({
                "amount": base["account_balance"] * rng.uniform(0.9, 1.0),
                "is_new_beneficiary": True,
                "beneficiary_added_days_ago": 0,
                "call_type": "video",
                "call_status": "active",
                "screen_share": True,
                "caller_not_contacts": True,
                "device_changed": rng.random() < 0.5,
                "urgency_text": rng.choice(URGENT_TEXTS_EN),
                "voice_prob": 0.15,
                "voice_conf": 0.85,
                "label": "fraud",
            })
        elif preset == "bank_impersonation":
            base.update({
                "amount": base["account_balance"] * rng.uniform(0.7, 0.95),
                "is_new_beneficiary": True,
                "beneficiary_added_days_ago": rng.uniform(0, 1),
                "call_type": "phone",
                "call_status": "active",
                "screen_share": False,
                "caller_not_contacts": True,
                "urgency_text": rng.choice(URGENT_TEXTS_EN),
                "voice_prob": rng.uniform(0.2, 0.6),
                "voice_conf": rng.uniform(0.7, 0.95),
                "label": "fraud",
            })
        elif preset == "courier_drugs":
            base.update({
                "amount": base["account_balance"] * rng.uniform(0.5, 0.9),
                "is_new_beneficiary": True,
                "beneficiary_added_days_ago": 0,
                "call_type": "phone",
                "call_status": "active",
                "screen_share": rng.random() < 0.4,
                "caller_not_contacts": True,
                "urgency_text": rng.choice(URGENT_TEXTS_EN),
                "voice_prob": 0.2,
                "voice_conf": 0.9,
                "label": "fraud",
            })
        elif preset == "lottery_fraud":
            base.update({
                "amount": base["txn_amount_30d_max"] * rng.uniform(2, 4),
                "is_new_beneficiary": True,
                "beneficiary_added_days_ago": rng.uniform(0, 2),
                "call_type": "phone",
                "call_status": "ended_within_60s",
                "screen_share": False,
                "caller_not_contacts": True,
                "urgency_text": "You won a lottery. Send money for processing fees urgently.",
                "voice_prob": rng.uniform(0.5, 0.9),
                "voice_conf": rng.uniform(0.7, 0.95),
                "label": "fraud",
            })
        elif preset == "relative_emergency":
            base.update({
                "amount": base["account_balance"] * rng.uniform(0.3, 0.7),
                "is_new_beneficiary": False,
                "beneficiary_added_days_ago": rng.uniform(5, 30),
                "beneficiary_previous_tx_count": rng.randint(1, 5),
                "call_type": "phone",
                "call_status": "active",
                "screen_share": False,
                "caller_not_contacts": False,
                "urgency_text": "तुरंत कुछ पैसे भेजो। डॉक्टर का बिल जमा करना है। किसी को मत बताना।",
                "voice_prob": rng.uniform(0.7, 0.95),
                "voice_conf": rng.uniform(0.7, 0.95),
                "label": "fraud",
            })
    else:
        base.update({
            "amount": base["txn_amount_30d_avg"] * rng.uniform(0.4, 1.5),
            "is_new_beneficiary": False,
            "beneficiary_added_days_ago": rng.uniform(60, 800),
            "call_type": "none",
            "call_status": "none",
            "screen_share": False,
            "caller_not_contacts": False,
            "urgency_text": rng.choice(LEGIT_TEXTS_EN) if rng.random() < 0.7 else None,
            "voice_prob": rng.uniform(0.0, 0.15),
            "voice_conf": rng.uniform(0.5, 0.9),
            "label": "legit" if preset != "bill_payment" else "legit_unusual",
        })
        if preset == "bill_payment":
            base["txn_count_last_1h"] = rng.randint(3, 6)
            base["beneficiary_previous_tx_count"] = rng.randint(2, 20)

    return base


def generate_dataset(n: int = 250, seed: int = 42) -> List[Dict]:
    rng = random.Random(seed)
    scenarios = []
    half = n // 2
    for _ in range(half):
        preset = rng.choice(SCAM_PRESETS)
        scenarios.append(generate_scenario(preset, rng))
    for _ in range(n - half):
        preset = rng.choice(LEGIT_PRESETS)
        scenarios.append(generate_scenario(preset, rng))
    rng.shuffle(scenarios)
    return scenarios