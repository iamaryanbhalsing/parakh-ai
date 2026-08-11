"""
Optional real-time LLM ("AI agent") integration for Parakh (परख) AI.

Speaks the OpenAI-compatible chat-completions protocol, so it works with any
provider: OpenAI, DeepSeek, Groq, OpenRouter, Azure OpenAI, Ollama, LM Studio, ...

Configuration (environment variables):
    PARAKH_LLM_BASE_URL  default https://api.openai.com/v1
    PARAKH_LLM_API_KEY   empty by default -> engine falls back to the NLP rules
    PARAKH_LLM_MODEL     default gpt-4o-mini
    PARAKH_LLM_TIMEOUT   default 15 (seconds)

The LLM is asked to act as a fraud analyst and return STRICT JSON covering the
whole situation (call conversation + transaction + device + voice context).
Output is normalized into the same shape the NLP engine produces, then merged
with the rule-based signals for a final, more precise opinion.

Failures are never fatal: any error/timeout/key-missing degrades gracefully to
the built-in NLP engine.
"""
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

import httpx

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT = 15.0

SYSTEM_PROMPT = """You are Parakh (परख), a senior UPI fraud-intervention analyst embedded inside a
bank's real-time payment engine. You are analysing a transaction that is about to be
authorised, together with the live call conversation the user had, device and voice signals.

Rules of your analysis:
1. You are a defence model, not a detector sales tool: never over-claim. Only call something
   FRAUD when there is genuine, coherent evidence (authority impersonation, credential
   harvesting, secrecy pressure, money-before-trust patterns, relative emergencies, prizes
   requiring fees, parcel/drug stories, etc.).
2. Weigh the WHOLE situation: conversation, transaction amount vs. user's history, account
   drain, call/screen-share context, device anomalies, voice-clone probability.
3. Consider that legitimate conversations exist: rent, bills, family transfers, merchants.
4. Output STRICT JSON only (no markdown, no commentary). Use exactly this schema:
{
  "fraud_score": 0.0-1.0,
  "risk_level": "low|medium|high|critical",
  "verdict": "FRAUD|SUSPICIOUS|LEGITIMATE|INCONCLUSIVE",
  "confidence": 0.0-1.0,
  "intent": "authority_impersonation|bank_impersonation|lottery_reward_fraud|relative_emergency_fraud|courier_parcel_fraud|legitimate|other",
  "intent_confidence": 0.0-1.0,
  "summary": "one or two sentences in plain English",
  "suggested_action": "block|verify|allow",
  "red_flags": ["short flag descriptions"],
  "entities": {"amounts": [numbers], "otps": ["codes"], "phones": ["numbers"], "institutions": ["names"]},
  "pattern_match": "short name of the strongest scam pattern, or null"
}"""


def llm_settings() -> Dict[str, Any]:
    return {
        "base_url": os.environ.get("PARAKH_LLM_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/") or DEFAULT_BASE_URL,
        "api_key": os.environ.get("PARAKH_LLM_API_KEY", "").strip(),
        "model": os.environ.get("PARAKH_LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        "timeout": float(os.environ.get("PARAKH_LLM_TIMEOUT", str(DEFAULT_TIMEOUT))),
    }


def llm_available(settings: Optional[Dict[str, Any]] = None) -> bool:
    s = settings or llm_settings()
    return bool(s["api_key"]) and s["base_url"].startswith(("http://", "https://"))


def build_user_prompt(turns: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None) -> str:
    lines = []
    if context:
        txn = context.get("transaction") or {}
        call = context.get("call") or {}
        device = context.get("device") or {}
        voice = context.get("voice") or {}
        user = context.get("user") or {}
        lines.append(
            "TRANSACTION CONTEXT: "
            f"amount=₹{txn.get('amount', '?')}, account_balance=₹{txn.get('account_balance', '?')}, "
            f"30d_avg=₹{txn.get('txn_amount_30d_avg', '?')}, new_beneficiary={txn.get('is_new_beneficiary', '?')}, "
            f"beneficiary_added_days_ago={txn.get('beneficiary_added_days_ago', '?')}, "
            f"txn_count_last_1h={txn.get('txn_count_last_1h', '?')}, user_age={user.get('age', '?')}, "
            f"flagged_vulnerable={user.get('flagged_vulnerable', '?')}"
        )
        lines.append(
            "CALL/DEVICE/VOICE CONTEXT: "
            f"call_type={call.get('call_type', 'none')}, screen_share={call.get('screen_share_active', False)}, "
            f"caller_unknown={call.get('caller_number_not_in_contacts', False)}, "
            f"device_changed={device.get('device_changed', False)}, "
            f"voice_clone_prob={voice.get('acoustic_clone_probability')}, "
            f"voice_model_conf={voice.get('model_confidence')}"
        )
    lines.append("CALL TRANSCRIPT (speaker: text):")
    for t in (turns or []):
        sp = "Caller" if str(t.get("speaker", "")).lower() in ("caller", "s") else "Victim"
        text = str(t.get("text", "")).strip()
        if text:
            lines.append(f"{sp}: {text[:600]}")
    return "\n".join(lines)


def _extract_json(content: str) -> Dict[str, Any]:
    """Extract the first balanced {...} JSON object from a model response."""
    if not content:
        return {}
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        if start < 0:
            return {}
        depth = 0
        for i in range(start, len(content)):
            ch = content[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[start:i + 1])
                    except json.JSONDecodeError:
                        return {}
    return {}


def normalize_llm_output(raw: Dict[str, Any]) -> Dict[str, Any]:
    def clamp(v, lo=0.0, hi=1.0, dflt=0.5):
        try:
            return max(lo, min(hi, float(v)))
        except (TypeError, ValueError):
            return dflt

    def strlist(v) -> List[str]:
        if isinstance(v, list):
            out = []
            for item in v:
                if isinstance(item, str):
                    out.append(item)
                elif isinstance(item, dict) and item.get("flag"):
                    out.append(str(item["flag"]))
            return out[:6]
        return []

    verdict = str(raw.get("verdict", "")).upper().strip()
    if verdict not in ("FRAUD", "SUSPICIOUS", "LEGITIMATE", "INCONCLUSIVE"):
        verdict = "INCONCLUSIVE"
    intent = str(raw.get("intent", "other")).lower().strip()
    valid_intents = {"authority_impersonation", "bank_impersonation", "lottery_reward_fraud",
                     "relative_emergency_fraud", "courier_parcel_fraud", "legitimate", "other"}
    if intent not in valid_intents:
        intent = "other"
    risk_level = str(raw.get("risk_level", "")).lower().strip()
    if risk_level not in ("low", "medium", "high", "critical"):
        risk_level = {"FRAUD": "critical", "SUSPICIOUS": "high", "LEGITIMATE": "low"}.get(verdict, "medium")
    suggested = str(raw.get("suggested_action", "")).lower().strip()
    if suggested not in ("block", "verify", "allow"):
        suggested = {"FRAUD": "block", "SUSPICIOUS": "verify", "LEGITIMATE": "allow"}.get(verdict, "review")

    entities = raw.get("entities") or {}
    amounts = [float(a) for a in entities.get("amounts", []) if isinstance(a, (int, float))]
    otps = [str(o) for o in entities.get("otps", [])][:6]
    phones = [str(p) for p in entities.get("phones", [])][:6]
    institutions = [str(i) for i in entities.get("institutions", [])][:6]

    return {
        "fraud_score": round(clamp(raw.get("fraud_score")), 4),
        "risk_level": risk_level,
        "verdict": verdict,
        "confidence": round(clamp(raw.get("confidence")), 4),
        "intent": intent,
        "intent_confidence": round(clamp(raw.get("intent_confidence")), 4),
        "summary": str(raw.get("summary", "")).strip()[:400] or "LLM provided no summary.",
        "suggested_action": suggested,
        "red_flags": strlist(raw.get("red_flags")),
        "entities": {
            "amounts": [round(a, 2) for a in amounts[:8]],
            "otps": otps,
            "phones": phones,
            "institutions": institutions,
        },
        "pattern_match": raw.get("pattern_match") or None,
    }


def analyze_with_llm(turns: List[Dict[str, str]], context: Optional[Dict[str, Any]] = None,
                     settings: Optional[Dict[str, Any]] = None,
                     transport: Optional[httpx.BaseTransport] = None,
                     ) -> Optional[Dict[str, Any]]:
    """Call the configured LLM. Returns normalized output or None on any failure."""
    s = settings or llm_settings()
    if not llm_available(s):
        return None
    user_prompt = build_user_prompt(turns, context)
    if not user_prompt.strip():
        return None
    payload: Dict[str, Any] = {
        "model": s["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 900,
    }
    host = s["base_url"]
    if any(k in host for k in ("openai.com", "azure.com", "groq.com", "deepseek", "openrouter", "together.xyz", "api.together")):
        payload["response_format"] = {"type": "json_object"}

    started = time.monotonic()
    try:
        with httpx.Client(base_url=s["base_url"], timeout=s["timeout"], transport=transport) as client:
            resp = client.post(
                "/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {s['api_key']}", "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None
    latency_ms = round((time.monotonic() - started) * 1000)
    raw = _extract_json(content)
    if not raw:
        return None
    norm = normalize_llm_output(raw)
    norm["llm_model"] = s["model"]
    norm["llm_latency_ms"] = latency_ms
    return norm


INTENT_DISPLAY = {
    "authority_impersonation": "Authority impersonation (police / court / digital arrest)",
    "bank_impersonation": "Bank / customer-care impersonation",
    "lottery_reward_fraud": "Lottery / prize / reward fraud",
    "relative_emergency_fraud": "Relative-emergency (voice-clone) fraud",
    "courier_parcel_fraud": "Courier / parcel / drug-seizure fraud",
    "legitimate": "Legitimate conversation",
    "other": "Unclear pattern",
}


def merge_into_analysis(nlp: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
    """Blend the NLP rule results with the LLM opinion into one analysis object.

    The LLM verdict drives the final opinion; agreement boosts confidence,
    disagreement is surfaced honestly in the summary/red flags.
    """
    out = dict(nlp)
    out["engine"] = "llm"
    out["llm_model"] = llm.get("llm_model")
    out["llm_latency_ms"] = llm.get("llm_latency_ms")

    nlp_v = nlp["opinion"]["verdict"]
    llm_v = llm["verdict"]
    agree = nlp_v == llm_v
    confidence = llm.get("confidence", 0.5)
    if agree:
        confidence = min(0.97, confidence + 0.08)
    else:
        confidence = max(0.35, confidence - 0.12)

    blended_score = round(0.65 * llm.get("fraud_score", 0.5) + 0.35 * nlp.get("fraud_score", 0.0), 4)
    verdict = llm_v if not agree else llm_v

    intent_label = llm.get("intent", "other")
    red_flags = llm.get("red_flags") or []
    nlp_flags = nlp.get("red_flags") or []
    for f in nlp_flags:
        if f not in red_flags and len(red_flags) < 6:
            red_flags.append(f)

    summary = llm.get("summary") or nlp["opinion"].get("summary", "")
    if not agree:
        summary += " (Rule engine and LLM disagreed — confidence lowered; verify with an operator.)"

    out["fraud_score"] = blended_score
    out["intent"] = {
        "label": intent_label,
        "display": INTENT_DISPLAY.get(intent_label, "Unclear pattern"),
        "confidence": llm.get("intent_confidence", 0.5),
        "scores": nlp.get("intent", {}).get("scores", {}),
    }
    out["red_flags"] = red_flags[:6]
    out["opinion"] = {
        "verdict": verdict,
        "confidence": round(max(0.35, min(0.97, confidence)), 4),
        "summary": summary,
        "suggested_action": llm.get("suggested_action", "review"),
        "reasons": red_flags[:4],
        "engine": "llm",
        "llm_model": llm.get("llm_model"),
        "llm_latency_ms": llm.get("llm_latency_ms"),
    }
    if llm.get("pattern_match"):
        out["active_patterns"] = [str(llm["pattern_match"])]
    return out
