import re
from typing import Dict, List

URGENT_TERMS_EN: List[str] = [
    "immediately", "right now", "now", "urgent", "asap", "fast", "quickly",
    "pin", "otp", "upi pin", "net banking", "share your pin", "tell me the otp",
    "arrest", "police", "digital arrest", "court", "case filed", "warrant",
    "bank employee", "fraud alert", "account will be blocked", "account frozen",
    "suspect", "money laundering", "cyber cell", "narcotics", "parcel contains drugs",
    "transfer", "send money", "pay fine", "pay bail", "pay now", "rupees",
    "don't tell anyone", "don't share this", "keep it secret", "trust me",
    "customer care", "refund", "cashback", "kbc", "lottery", "prize",
]

URGENT_TERMS_HI: List[str] = [
    "तुरंत", "अभी", "जल्दी", "तुरन्त", "तत्काल", "अत्यावश्यक", "अर्जेंट",
    "ओटीपी", "पिन", "यूपीआई पिन", "बैंक कर्मचारी", "नेट बैंकिंग",
    "पुलिस", "गिरफ्तारी", "डिजिटल अरेस्ट", "कोर्ट", "केस", "वारंट",
    "खाता ब्लॉक", "खाता फ्रीज", "राशि", "पैसे", "भेजो", "ट्रांसफर",
    "जमानत", "जुर्माना", "पैसे दो", "किसी को मत बताना", "गुप्त रखो",
    "भरोसा करो", "रिफंड", "कैशबैक", "लॉटरी", "इनाम", "पुरस्कार",
    "डॉक्टर का बिल", "जमा करना है", "अस्पताल",
]

HI_SUBWORD = [
    "अरेस्ट", "पुलिस", "ओटीपी", "पिन", "ब्लॉक", "जमानत", "जुर्माना",
    "भेजो", "पैसे", "राशि",
]

URGENT_PHRASES = [
    "don't tell anyone", "do not tell anyone", "don't tell your family", "don't tell your bank",
    "keep it secret", "keep this secret", "digital arrest", "share your pin",
    "tell me the otp", "share the otp", "account will be blocked", "money laundering",
    "parcel contains drugs", "pay fine now", "pay fine", "pay bail", "urgent payment",
    "last warning", "you are under arrest", "under digital arrest", "case has been filed",
    "avoid arrest", "to avoid arrest", "police will come", "expires in",
    "will be arrested", "arrest warrant", "transfer all money", "transfer the money",
    "send money right now", "pay right now", "pay now or", "verify right now",
    "final call", "keep this confidential", "this is confidential", "in 30 minutes",
]

EMOJI_PANIC = ["❗", "‼", "⚠️", "🚨", "🔴", "🔥"]


def detect_urgency(text: str, language: str = "auto") -> Dict:
    text_norm = " " + text.lower().strip() + " "
    urgency = 0.0
    matched: List[str] = []
    lang_code = language

    if language == "auto":
        lang_code = "hi" if re.search(r"[\u0900-\u097F]", text) else "en"

    if lang_code == "hi":
        term_list = URGENT_TERMS_HI
        for term in term_list:
            if term.lower() in text_norm:
                matched.append(term)
                urgency += 0.18
        for sub in HI_SUBWORD:
            count = len(re.findall(sub, text, flags=re.IGNORECASE))
            if count > 1:
                matched.append(sub)
                urgency += 0.12 * (count - 1)
    else:
        for term in URGENT_TERMS_EN:
            if term.lower() in text_norm:
                matched.append(term)
                urgency += 0.15
        word_count = len(re.findall(r"[A-Za-z]+", text_norm))
        if word_count >= 30:
            matched.append("long pressured monologue")
            urgency += 0.08
        if len(re.findall(r"[A-Z]", text)) >= 6 and word_count >= 15:
            matched.append("shouting/all-caps")
            urgency += 0.15

    for phrase in URGENT_PHRASES:
        if phrase in text_norm:
            matched.append(phrase)
            urgency += 0.25

    for emoji in EMOJI_PANIC:
        if emoji in text:
            matched.append(emoji)
            urgency += 0.05

    urgency = min(1.0, urgency)
    return {
        "urgency_score": round(urgency, 4),
        "language": lang_code,
        "matched_terms": list(dict.fromkeys(matched)),
        "verdict": "critical_pressure" if urgency >= 0.6 else "high_pressure" if urgency >= 0.35 else "pressured" if urgency >= 0.15 else "normal",
    }