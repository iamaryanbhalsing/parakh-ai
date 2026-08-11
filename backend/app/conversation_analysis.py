"""
AI call-conversation analysis.

Runs lightweight NLP over a call transcript (English / Hindi):
  - turn-level cue detection (pressure, secrecy, authority, credential requests,
    payment demands, rewards, courier/parcel, relative emergencies)
  - entity extraction (amounts, OTP/PIN codes, phone numbers, institutions)
  - per-speaker sentiment
  - scam-intent classification
  - final opinion: FRAUD / SUSPICIOUS / LEGITIMATE / INCONCLUSIVE + confidence

Designed to run fully offline and in <1 ms per turn.
"""
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------- cue lexicons

CUE_LEXICONS: Dict[str, Dict[str, List[str]]] = {
    "en": {
        "pressure": [
            "immediately", "right now", "right away", "urgent", "urgently", "asap",
            "hurry", "hurry up", "quickly", "fast", "no time", "now or", "before it's too late",
            "last warning", "final call", "do it now", "act now", "at once", "right this second",
            "in 10 minutes", "in 5 minutes", "expires", "deadline", "final warning",
        ],
        "secrecy": [
            "don't tell anyone", "do not tell anyone", "don't tell", "tell no one",
            "keep it secret", "keep this secret", "don't share this", "do not share",
            "stay confidential", "confidential", "between us", "secret", "don't inform",
            "don't call the police", "don't call your bank", "don't involve", "don't contact",
            "किसी को मत बताना", "गुप्त रखो", "बताना मत", "किसी को मत बताओ",
        ],
        "authority": [
            "police", "court", "warrant", "arrest", "jail", "prison", "rbi", "cyber cell",
            "cyber crime", "narcotics", "customs", "agency", "case filed", "investigation",
            "enforcement directorate", "income tax", "cbi", "ed", "judge", "magistrate",
            "legal action", "supreme court", "high court", "sessions court", "criminal case",
            "money laundering", "account freeze order", "seizure", "attachment order",
        ],
        "credential": [
            "otp", "one time password", "upi pin", "pin number", "net banking", "password",
            "mpin", "atm pin", "card number", "cvv", "expiry date", "share your pin",
            "tell me the otp", "verify your pin", "confirm your pin", "enter the otp",
        ],
        "payment_demand": [
            "transfer", "send money", "send the money", "pay now", "pay the", "pay fine",
            "pay bail", "processing fee", "deposit", "payment", "amount", "rupees",
            "bank account", "account number", "upi id", "wallet", "pay up", "pay immediately",
            "funds", "cash", "payment first", "settle", "pay the amount", "pay this",
            "transfer all", "transfer the money", "pay me", "pay us", "send the amount",
        ],
        "reward": [
            "lottery", "prize", "won", "congratulations", "cashback", "refund", "kbc",
            "gift", "reward", "jackpot", "claim your", "processing fees", "gst and processing",
            "release your winnings", "winning", "selected", "grand prize", "bonus",
        ],
        "relative": [
            "hospital", "doctor", "accident", "emergency", "admitted", "relative",
            "uncle", "aunt", "son", "daughter", "brother", "sister", "friend", "mom",
            "mother", "dad", "father", "नाते", "रिश्तेदार", "अस्पताल", "डॉक्टर",
            "बेटा", "बेटी", "भाई", "बहन", "दुर्घटना",
        ],
        "courier": [
            "parcel", "package", "shipment", "courier", "dhl", "fedex", "drugs",
            "narcotics", "illegal goods", "customs", "delivery", "contained", "seized",
        ],
        "fear": [
            "arrested", "will be arrested", "jail", "prison", "blocked", "frozen",
            "lose everything", "legal action", "case", "sue", "identity theft", "fraud charge",
            "criminal", "under arrest", "charge sheet", "account will be closed", "terminated",
            "penalty", "fine", "blacklisted", "will come to your home", "police will come",
            "charged", "charges", "seized", "dropped",
        ],
        "reassurance": [
            "no hurry", "whenever", "no pressure", "take your time", "you don't have to",
            "if you want", "optional", "at your convenience", "no rush", "when you are free",
            "later", "whenever you can", "no need", "don't worry about it",
        ],
        "confirmation": [
            "thanks", "thank you", "confirmed", "received", "got it", "done", "okay", "ok",
            "sure", "sounds good", "agreed", "धन्यवाद", "ठीक है", "हो गया",
        ],
    },
    "hi": {
        "pressure": [
            "तुरंत", "अभी", "जल्दी", "तुरन्त", "तत्काल", "अर्जेंट", "अभी भेजो", "जल्दी करो",
            "देर मत करो", "अभी करो", "अब करो", "समय नहीं है", "आखिरी चेतावनी",
        ],
        "authority": [
            "पुलिस", "कोर्ट", "अदालत", "वारंट", "गिरफ्तारी", "अरेस्ट", "डिजिटल अरेस्ट",
            "जेल", "साइबर सेल", "साइबर क्राइम", "नार्कोटिक्स", "कस्टम्स", "केस", "मनी लॉन्ड्रिंग",
            "आरोप", "न्यायाधीश", "जांच", "अटैचमेंट", "खाता फ्रीज", "खाता ब्लॉक",
        ],
        "credential": [
            "ओटीपी", "पिन", "यूपीआई पिन", "नेट बैंकिंग", "पासवर्ड", "कार्ड नंबर", "सीवीवी",
        ],
        "payment_demand": [
            "पैसे भेजो", "पैसे दो", "ट्रांसफर", "राशि", "पैसे", "भेजो", "जमा करो",
            "अकाउंट नंबर", "बैंक अकाउंट", "यूपीआई आईडी", "पेमेंट", "रुपये", "जुर्माना", "जमानत",
            "फीस", "प्रोसेसिंग फीस", "भुगतान",
        ],
        "reward": [
            "लॉटरी", "इनाम", "पुरस्कार", "जीत", "कैशबैक", "रिफंड", "केबीसी", "गिफ्ट", "बोनस",
        ],
        "relative": [
            "अस्पताल", "डॉक्टर", "दुर्घटना", "एडमिट", "बीमार", "भाई", "बहन", "बेटा", "बेटी",
            "मां", "पिता", "रिश्तेदार", "दोस्त", "इलाज",
        ],
        "courier": [
            "पार्सल", "पैकेज", "कूरियर", "ड्रग्स", "नशीला", "कस्टम्स", "शिपमेंट",
        ],
        "fear": [
            "गिरफ्तार", "जेल", "ब्लॉक", "फ्रीज", "केस", "सजा", "खतरा", "पुलिस आएगी",
            "सब कुछ खो दोगे", "कानूनी कार्रवाई",
        ],
        "reassurance": [
            "जल्दी नहीं", "जब चाहे", "कोई जल्दी नहीं", "आराम से", "फिर कभी", "कोई बात नहीं",
        ],
        "confirmation": [
            "धन्यवाद", "ठीक है", "हो गया", "मिल गया", "पक्का", "हाँ", "सही है",
        ],
    },
}

ENTITY_INSTITUTIONS: Dict[str, str] = {
    "rbi": "RBI",
    "reserve bank": "RBI",
    "police": "Police",
    "court": "Court",
    "cyber cell": "Cyber Cell",
    "cyber crime": "Cyber Crime Cell",
    "cbi": "CBI",
    "narcotics": "Narcotics Bureau",
    "customs": "Customs",
    "enforcement directorate": "Enforcement Directorate",
    "income tax": "Income Tax",
    "kbc": "KBC",
    "bank": "Bank",
    "केंद्रीय बैंक": "Central Bank",
    "पुलिस": "Police",
    "अदालत": "Court",
    "साइबर सेल": "Cyber Cell",
}

# ------------------------------------------------------------- small lexicons

POSITIVE_WORDS = {
    "thanks", "thank", "ok", "okay", "fine", "great", "good", "confirmed", "received",
    "glad", "happy", "love", "sure", "perfect", "done", "welcome", "appreciate",
    "nice", "beautiful", "सही", "ठीक", "बढ़िया", "धन्यवाद", "हो गया", "खुश",
}
NEGATIVE_WORDS = {
    "scared", "fear", "afraid", "worried", "scam", "fraud", "arrest", "blocked",
    "panic", "terrified", "angry", "shocked", "upset", "stop", "wait", "why",
    "suspicious", "don't", "refuse", "nervous", "threat", "cry", "afraid",
    "डर", "डरा", "घबरा", "रुको", "क्यों", "धोखा", "शक",
}

HI_SEGMENTS = ["तुरंत", "पुलिस", "पिन", "ओटीपी", "भेजो", "पैसे", "ब्लॉक", "अरेस्ट", "कोर्ट", "जमानत", "जुर्माना", "लॉटरी", "इनाम", "डॉक्टर", "अस्पताल", "गुप्त"]

AMOUNT_RE = re.compile(
    r"(?:₹|rs\.?|inr|rupees|रुपये|रु\.?)\s*([\d,]+(?:\.\d+)?)"
    r"|(?:pay|send|transfer|deposit|fine|bail|fee|fees|amount|processing|कुछ पैसे|राशि|जुर्माना|जमानत|फीस)[\s\S]{0,40}?\b([\d]{2,3}(?:,\d{3})+|\d{4,6}(?:\.\d+)?)\b",
    re.IGNORECASE,
)
INDIAN_AMOUNT_RE = re.compile(r"\b[\d]{1,3}(?:,\d{3})+\b")
OTP_RE = re.compile(r"\b(?:otp|पिन|pin)\b[\s:]*(\d{4,6})", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?[6-9]\d{9}|(?:\+91[\s-]?)?[6-9]\d{2}[\s-]\d{3}[\s-]\d{4}")
LAKH_CRORE_RE = re.compile(r"([\d,]+(?:\.\d+)?)\s*(lakh|crore|लाख|करोड़|हज़ार|हजार)", re.IGNORECASE)

SPEAKER_MAP = {
    "s": "caller", "caller": "caller", "fraudster": "caller", "scammer": "caller",
    "agent": "caller", "attacker": "caller", "them": "caller", "other": "caller",
    "b": "caller", "bank": "caller", "scam": "caller", "stranger": "caller",
    "u": "victim", "user": "victim", "victim": "victim", "you": "victim",
    "me": "victim", "customer": "victim", "target": "victim", "a": "victim",
    "person": "victim", "target_user": "victim",
}

INTENT_LABELS = {
    "authority_impersonation": "Authority impersonation (police / court / digital arrest)",
    "bank_impersonation": "Bank / customer-care impersonation",
    "lottery_reward_fraud": "Lottery / prize / reward fraud",
    "relative_emergency_fraud": "Relative-emergency (voice-clone) fraud",
    "courier_parcel_fraud": "Courier / parcel / drug-seizure fraud",
    "legitimate": "Legitimate conversation",
}

# ------------------------------------------------------------------ parsing


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def parse_transcript(turns: Any) -> List[Dict[str, str]]:
    """Normalize any transcript shape into [{speaker: caller|victim, text}]."""
    parsed: List[Dict[str, str]] = []

    def push(speaker: str, text: str) -> None:
        text = text.strip()
        if text:
            parsed.append({"speaker": speaker, "text": text})

    if isinstance(turns, str):
        turns = [turns]
    if not isinstance(turns, list):
        return parsed

    for item in turns:
        if isinstance(item, str):
            m = re.match(r"^\s*([A-Za-z_\- ]+?)\s*[:：]\s*(.+)$", item)
            if m and (m.group(1).strip().lower() in SPEAKER_MAP or len(m.group(1).strip()) <= 20):
                push(SPEAKER_MAP.get(m.group(1).strip().lower(), "caller"), m.group(2))
            else:
                push("caller", item)
        elif isinstance(item, dict) and item.get("text"):
            sp = str(item.get("speaker") or item.get("who") or "caller").strip().lower()
            push(SPEAKER_MAP.get(sp, "caller"), str(item["text"]))

    if len(parsed) == 1 and re.search(r"[.!?]\s*[A-Z]|[।\n]", parsed[0]["text"]):
        sentences = re.split(r"(?<=[.!?।])\s+", parsed[0]["text"])
        if len(sentences) > 2:
            parsed = [{"speaker": "caller" if i % 2 == 0 else "victim", "text": s} for i, s in enumerate(sentences) if s.strip()]
    return parsed


# --------------------------------------------------------------- per-turn scan


def _scan_cues(text: str, lang: str) -> Dict[str, List[str]]:
    norm = _norm(text)
    hi = lang == "hi"
    lex = CUE_LEXICONS["hi" if hi else "en"]
    found: Dict[str, List[str]] = {}
    for cat, terms in lex.items():
        hits: List[str] = []
        if hi:
            for term in terms:
                if len(term) == 1:
                    continue
                if term.lower() in norm:
                    hits.append(term)
        else:
            for term in terms:
                if term.lower() in norm:
                    hits.append(term)
        if hits:
            found[cat] = list(dict.fromkeys(hits))
    if not hi:
        for term in CUE_LEXICONS["hi"].get("secrecy", []):
            if term in norm:
                found.setdefault("secrecy", []).append(term)
        for term in CUE_LEXICONS["hi"].get("relative", []):
            if term in norm:
                found.setdefault("relative", []).append(term)
    return found


def _sentiment(text: str, lang: str) -> float:
    words = re.findall(r"[a-z\u0900-\u097F]+", _norm(text))
    pos = sum(1 for w in words if w in POSITIVE_WORDS)
    neg = sum(1 for w in words if w in NEGATIVE_WORDS)
    if pos + neg == 0:
        return 0.0
    return round((pos - neg) / (pos + neg), 3)


def extract_entities(text: str, lang: str) -> Dict[str, List[Any]]:
    norm_orig = text
    norm = _norm(text)
    entities: Dict[str, List[Any]] = {"amounts": [], "otps": [], "phones": [], "institutions": []}

    for m in AMOUNT_RE.finditer(norm):
        raw = m.group(1) or m.group(2)
        if raw:
            try:
                val = float(raw.replace(",", ""))
                tail = norm[m.end():m.end() + 18]
                if re.match(r"\s*(lakh|crore|लाख|करोड़|हज़ार|हजार)\b", tail):
                    continue
                entities["amounts"].append(val)
            except ValueError:
                pass
    for m in INDIAN_AMOUNT_RE.finditer(norm):
        try:
            entities["amounts"].append(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    for m in LAKH_CRORE_RE.finditer(norm):
        try:
            val = float(m.group(1).replace(",", "")) * (100000 if m.group(2).lower().startswith(("l", "ल")) else 1000)
            entities["amounts"].append(val)
        except ValueError:
            pass
    for m in OTP_RE.finditer(norm_orig):
        entities["otps"].append(m.group(1))
    for m in PHONE_RE.finditer(norm_orig):
        entities["phones"].append(m.group(0).strip())

    low = norm
    for key, label in ENTITY_INSTITUTIONS.items():
        if key.lower() in low:
            entities["institutions"].append(label)

    for key in ("amounts", "phones", "otps"):
        seen: List[Any] = []
        for v in entities[key]:
            if v not in seen:
                seen.append(v)
        entities[key] = seen[:6]
    entities["institutions"] = list(dict.fromkeys(entities["institutions"]))[:6]
    return entities


def _detect_lang(text: str) -> str:
    return "hi" if re.search(r"[\u0900-\u097F]", text) else "en"


# ------------------------------------------------------------- intent & opinion

CUES_TO_INTENT = {
    "authority_impersonation": {"authority": 1.5, "fear": 0.6, "pressure": 0.3},
    "bank_impersonation": {"credential": 1.6, "authority": 0.4, "payment_demand": 0.3, "fear": 0.3},
    "lottery_reward_fraud": {"reward": 1.6, "payment_demand": 0.7, "pressure": 0.3},
    "relative_emergency_fraud": {"relative": 1.6, "payment_demand": 0.6, "pressure": 0.4, "secrecy": 0.4},
    "courier_parcel_fraud": {"courier": 1.7, "authority": 0.4, "payment_demand": 0.5, "fear": 0.4},
    "legitimate": {"reassurance": 1.2, "confirmation": 0.8},
}

FRAUD_WEIGHTS = {
    "pressure": 0.22,
    "secrecy": 0.18,
    "authority": 0.16,
    "credential": 0.26,
    "payment_demand": 0.20,
    "reward": 0.16,
    "relative": 0.16,
    "courier": 0.16,
    "fear": 0.14,
    "reassurance": -0.28,
}

# Multi-signal scam patterns: when several cues co-occur they compound.
INTERACTION_BONUS = 0.15
INTERACTIONS = [
    (("reward", "payment_demand"), "advance-fee prize pattern"),
    (("courier", "payment_demand"), "parcel-fine pattern"),
    (("relative", "payment_demand", "pressure"), "emergency money-demand pattern"),
    (("authority", "credential"), "impersonation asking for credentials"),
    (("authority", "payment_demand", "pressure"), "coercive authority money demand"),
    (("authority", "payment_demand"), "coercive authority money demand"),
]

# A confidently-classified fraud intent corroborates the cue score.
INTENT_FRAUD_BONUS = 0.12
FRAUD_INTENTS = {
    "authority_impersonation", "bank_impersonation", "lottery_reward_fraud",
    "relative_emergency_fraud", "courier_parcel_fraud",
}

# Asking the victim to hand over an OTP/PIN is itself a definitive fraud marker.
REQUESTIVE_CREDENTIALS = {
    "tell me the otp", "share the otp", "share your pin", "confirm your pin",
    "verify your pin", "enter the otp", "otp", "upi pin", "net banking",
    "ओटीपी", "पिन", "यूपीआई पिन", "ओटीपी बताओ", "पिन बताओ",
}
CREDENTIAL_REQUEST_BONUS = 0.25

VERDICT_ORDER = ["FRAUD", "SUSPICIOUS", "LEGITIMATE", "INCONCLUSIVE"]


def _rate_cues(cues: Dict[str, List[str]]) -> Dict[str, float]:
    """Normalize cue counts to 0..1 per category."""
    rated: Dict[str, float] = {}
    for cat, hits in cues.items():
        n = len(hits)
        if n == 0:
            rated[cat] = 0.0
        elif n == 1:
            rated[cat] = 0.45
        elif n == 2:
            rated[cat] = 0.7
        else:
            rated[cat] = 0.9
    return rated


def analyze_conversation(turns: Any, source: str = "api", txn_id: Optional[str] = None) -> Dict[str, Any]:
    parsed = parse_transcript(turns)
    if not parsed:
        return {
            "analysis_id": None, "timestamp": None, "source": source, "txn_id": txn_id,
            "error": "No transcribable conversation text provided.",
        }

    langs = [_detect_lang(t["text"]) for t in parsed]
    main_lang = "hi" if langs.count("hi") > len(langs) / 2 else "en"

    turn_rows = []
    agg: Dict[str, List[str]] = {}
    entities_all: Dict[str, List[Any]] = {"amounts": [], "otps": [], "phones": [], "institutions": []}
    sentiments = {"caller": [], "victim": []}

    for i, t in enumerate(parsed):
        lang = _detect_lang(t["text"])
        cues = _scan_cues(t["text"], lang)
        for cat, hits in cues.items():
            agg.setdefault(cat, []).extend(hits)
        sent = _sentiment(t["text"], lang)
        sentiments.setdefault(t["speaker"], []).append(sent)
        ents = extract_entities(t["text"], lang)
        for k, v in ents.items():
            entities_all[k].extend(v)
        turn_rows.append({
            "index": i,
            "speaker": t["speaker"],
            "text": t["text"],
            "language": lang,
            "cues": cues,
            "sentiment": sent,
        })

    for k, v in entities_all.items():
        if k == "institutions":
            entities_all[k] = list(dict.fromkeys(v))[:8]
        else:
            seen = []
            for x in v:
                if x not in seen:
                    seen.append(x)
            entities_all[k] = seen[:8]

    rated = _rate_cues(agg)
    fraud_score = 0.0
    for cat, w in FRAUD_WEIGHTS.items():
        fraud_score += rated.get(cat, 0.0) * w
    active_patterns = []
    for cats, name in INTERACTIONS:
        if all(rated.get(c, 0.0) >= 0.45 for c in cats):
            fraud_score += INTERACTION_BONUS
            active_patterns.append(name)
    credential_hits = agg.get("credential", [])
    if any(h in REQUESTIVE_CREDENTIALS for h in credential_hits):
        fraud_score += CREDENTIAL_REQUEST_BONUS
        active_patterns.append("direct request for OTP/PIN")
    fraud_score = round(max(0.0, min(1.0, fraud_score)), 4)

    intent_scores = {}
    for label, weights in CUES_TO_INTENT.items():
        s = sum(rated.get(cat, 0.0) * w for cat, w in weights.items())
        intent_scores[label] = round(s, 4)
    best_intent = max(intent_scores, key=intent_scores.get)
    runner_up = sorted(intent_scores, key=intent_scores.get, reverse=True)[1]
    margin = intent_scores[best_intent] - intent_scores[runner_up]
    intent_conf = round(max(0.35, min(0.97, 0.45 + margin * 1.6 + intent_scores[best_intent] * 0.25)), 4)
    if best_intent == "legitimate" and intent_scores[best_intent] < 0.3:
        best_intent = "inconclusive"
        intent_conf = 0.4
    if best_intent in FRAUD_INTENTS and intent_conf >= 0.6 and intent_scores[best_intent] >= 0.8:
        fraud_score = round(min(1.0, fraud_score + INTENT_FRAUD_BONUS), 4)

    total_chars = sum(len(t["text"]) for t in parsed)
    if total_chars < 30:
        verdict = "INCONCLUSIVE"
    elif fraud_score >= 0.5:
        verdict = "FRAUD"
    elif fraud_score >= 0.35:
        verdict = "SUSPICIOUS"
    else:
        verdict = "LEGITIMATE"

    coverage = sum(1 for t in turn_rows if t["cues"]) / max(1, len(turn_rows))
    margin_frac = abs(fraud_score - 0.35) / 0.65
    confidence = round(max(0.35, min(0.97, 0.5 + 0.4 * margin_frac + 0.25 * coverage)), 4)
    if verdict == "INCONCLUSIVE":
        confidence = 0.45

    red_flags = _build_red_flags(rated, agg, entities_all, verdict)

    op_sent_caller = _avg(sentiments.get("caller", []))
    op_sent_victim = _avg(sentiments.get("victim", []))
    op_sentiment = _avg(sentiments.get("caller", []) + sentiments.get("victim", []))

    suggested = "block" if verdict == "FRAUD" else "verify" if verdict == "SUSPICIOUS" else "allow" if verdict == "LEGITIMATE" else "review"
    summary = _build_summary(verdict, best_intent, rated, entities_all, main_lang)

    return {
        "analysis_id": uuid.uuid4().hex[:12],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": source,
        "txn_id": txn_id,
        "language": main_lang,
        "turn_count": len(turn_rows),
        "turns": turn_rows,
        "entities": entities_all,
        "cue_scores": {k: round(v, 4) for k, v in rated.items()},
        "fraud_score": fraud_score,
        "active_patterns": active_patterns,
        "intent": {
            "label": "legitimate" if best_intent == "inconclusive" and verdict in ("FRAUD", "SUSPICIOUS") else best_intent,
            "display": INTENT_LABELS.get(best_intent, "Unclear"),
            "confidence": intent_conf,
            "scores": intent_scores,
        },
        "sentiment": {
            "caller": op_sent_caller,
            "victim": op_sent_victim,
            "overall": op_sentiment,
        },
        "red_flags": red_flags,
        "opinion": {
            "verdict": verdict,
            "confidence": confidence,
            "summary": summary,
            "suggested_action": suggested,
            "reasons": red_flags[:4],
        },
    }


def _avg(vals: List[float]) -> float:
    return round(sum(vals) / len(vals), 3) if vals else 0.0


def _build_red_flags(rated: Dict[str, float], agg: Dict[str, List[str]], entities: Dict[str, List[Any]], verdict: str) -> List[str]:
    flags = []
    if rated.get("authority", 0) >= 0.45:
        flags.append("Caller invokes police/court/agency authority")
    if rated.get("credential", 0) >= 0.45:
        flags.append("Caller requests OTP / PIN / banking credentials")
    if rated.get("secrecy", 0) >= 0.45:
        flags.append("Caller instructs secrecy — 'don't tell anyone'")
    if rated.get("payment_demand", 0) >= 0.45:
        flag = "Demand for money/transfer"
        if entities["amounts"]:
            flag += f" (₹{max(entities['amounts']):,.0f} detected)"
        flags.append(flag)
    if rated.get("pressure", 0) >= 0.45:
        flags.append("High-pressure / time-limited demands")
    if rated.get("fear", 0) >= 0.45:
        flags.append("Fear-inducing threats (arrest / blocking / legal action)")
    if rated.get("reward", 0) >= 0.45:
        flags.append("Unexpected prize/reward offered for payment")
    if rated.get("relative", 0) >= 0.45:
        flags.append("Claims of a relative emergency")
    if rated.get("courier", 0) >= 0.45:
        flags.append("Parcel/drugs story to justify payment")
    if entities["otps"]:
        flags.append("OTP codes referenced in conversation")
    if not flags:
        flags.append("No high-severity fraud cues detected")
    return flags[:6]


def _build_summary(verdict: str, intent: str, rated: Dict[str, float], entities: Dict[str, List[Any]], lang: str) -> str:
    if verdict == "INCONCLUSIVE":
        return "Conversation too short or unclear for a confident opinion."
    intent_display = INTENT_LABELS.get(intent, "unclear pattern")
    if verdict == "FRAUD":
        return (f"High-confidence fraud pattern: {intent_display.lower()}. "
                f"Caller applied social pressure and requested money"
                + (f" (₹{max(entities['amounts']):,.0f})" if entities["amounts"] else "") + ".")
    if verdict == "SUSPICIOUS":
        return f"Mixed signals: {intent_display.lower()} with pressure cues; recommend verification."
    return "No fraud indicators found; conversation appears routine and legitimate."


# ------------------------------------------------------------------- storage


class CallAnalysisStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(exist_ok=True)
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = []
        else:
            self._data = []

    def append_analysis(self, analysis: Dict[str, Any]) -> str:
        analysis["id"] = analysis.get("analysis_id") or uuid.uuid4().hex[:12]
        self._data.append({"kind": "analysis", **analysis})
        self._save()
        return analysis["id"]

    def append_recording(self, meta: Dict[str, Any]) -> str:
        rec_id = uuid.uuid4().hex[:12]
        self._data.append({"kind": "recording", "recording_id": rec_id, **meta})
        self._save()
        return rec_id

    def recent(self, n: int = 10, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        items = self._data if kind is None else [d for d in self._data if d.get("kind") == kind]
        return list(reversed(items))[-n:]

    def get(self, rec_id: str) -> Optional[Dict[str, Any]]:
        for d in self._data:
            if d.get("recording_id") == rec_id or d.get("id") == rec_id:
                return d
        return None

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=1, ensure_ascii=False), encoding="utf-8")
