import json
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
STATIC_DIR = Path(__file__).resolve().parent / "static"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

DEFAULT_POLICY: Dict[str, Any] = {
    "thresholds": {
        "low": 30.0,
        "medium": 55.0,
        "high": 75.0,
        "critical": 85.0,
    },
    "holds": {
        "high_hours": 2.0,
        "critical_hours": 24.0,
    },
    "verification_threshold": 55.0,
    "cooling_off_threshold": 85.0,
    "hard_block_threshold": 95.0,
    "voice_risk_weight_cap": 0.25,
    "urgent_critical_bonus": 15.0,
    "pattern_bonus": 10.0,
    "signature_bonus": 5.0,
    "voice_pressure_bonus": 8.0,
    "social_engineering_bonus": 12.0,
    "alerts": {
        "min_level": "high",
        "hmac_key": "dev-bank-alert-key-change-me",
    },
}

POLICY_KEYS = {"thresholds", "holds", "verification_threshold", "cooling_off_threshold", "hard_block_threshold", "voice_risk_weight_cap", "urgent_critical_bonus", "pattern_bonus", "signature_bonus", "voice_pressure_bonus", "social_engineering_bonus", "alerts"}

MESSAGES = {
    "en": {
        "low": "This payment looks normal. You can proceed safely.",
        "medium": "This payment has some unusual signals. Please review before continuing.",
        "high": "High risk detected. Please verify this payment with your bank before proceeding.",
        "critical": "Critical risk detected. This payment has been held. Verify with a trusted contact before release.",
        "coach": "Unusual activity detected. Confirm you are not sharing your screen or following caller instructions.",
        "verify": "Please complete independent verification (OTP sent to your registered mobile).",
        "cooling": "Your payment has been moved to a cooling-off wallet. It will be released after review.",
        "block": "This payment is blocked for your safety. Contact your bank immediately.",
    },
    "hi": {
        "low": "यह भुगतान सामान्य लग रहा है। आप सुरक्षित रूप से आगे बढ़ सकते हैं।",
        "medium": "इस भुगतान में कुछ असामान्य संकेत हैं। जारी रखने से पहले समीक्षा करें।",
        "high": "उच्च जोखिम पाया गया। जारी रखने से पहले अपने बैंक से सत्यापित करें।",
        "critical": "गंभीर जोखिम पाया गया। यह भुगतान रोक दिया गया है। जारी होने से पहले किसी विश्वसनीय व्यक्ति से सत्यापित करें।",
        "coach": "असामान्य गतिविधि मिली। सुनिश्चित करें कि आप अपनी स्क्रीन साझा नहीं कर रहे हैं।",
        "verify": "कृपया स्वतंत्र सत्यापन पूरा करें (आपके पंजीकृत मोबाइल पर भेजा गया OTP)।",
        "cooling": "आपका भुगतान कूलिंग-ऑफ वॉलेट में स्थानांतरित कर दिया गया है। समीक्षा के बाद जारी किया जाएगा।",
        "block": "आपकी सुरक्षा के लिए यह भुगतान ब्लॉक कर दिया गया है। तुरंत बैंक से संपर्क करें।",
    },
    "mr": {
        "low": "हे पेमेंट सामान्य दिसत आहे. तुम्ही सुरक्षितपणे पुढे जाऊ शकता.",
        "medium": "या पेमेंटमध्ये काही असामान्य संकेत आहेत. पुढे जाण्यापूर्वी पुनरावलोकन करा.",
        "high": "उच्च धोका आढळला. पुढे जाण्यापूर्वी तुमच्या बँकेशी सत्यापित करा.",
        "critical": "गंभीर धोका आढळला. हे पेमेंट रोखले गेले आहे. प्रकाशित होण्यापूर्वी विश्वासू व्यक्तीशी सत्यापित करा.",
        "coach": "असामान्य क्रियाकलाप आढळला. तुम्ही स्क्रीन शेअर करत नाही याची खात्री करा.",
        "verify": "कृपया स्वतंत्र सत्यापन पूर्ण करा (तुमच्या नोंदणीकृत मोबाईलवर पाठवलेला OTP).",
        "cooling": "तुमचे पेमेंट कूलिंग-ऑफ वॉलेटमध्ये हलवले गेले आहे. पुनरावलोकनानंतर प्रकाशित केले जाईल.",
        "block": "तुमच्या सुरक्षिततेसाठी हे पेमेंट ब्लॉक केले गेले आहे. त्वरित बँकेशी संपर्क साधा.",
    },
}


def load_policy(path: Path | None = None) -> Dict[str, Any]:
    if path and path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            policy = dict(DEFAULT_POLICY)
            for key in POLICY_KEYS:
                if key in loaded:
                    policy[key] = loaded[key]
            return policy
        except Exception:
            pass
    return dict(DEFAULT_POLICY)


def save_policy(policy: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(policy, indent=2), encoding="utf-8")