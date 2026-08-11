from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Optional

from .config import DEFAULT_POLICY, MESSAGES, STATIC_DIR, DATA_DIR, load_policy
from .schemas import ScoreRequest, OverrideRequest, FeedbackRequest, ProceedRequest, CancelRequest, ScoreResponse, Decision
from .risk_engine import RiskEngine
from .nlp_urgency import detect_urgency
from .voice_analysis import analyze_voice
from .evidence_store import EvidenceStore
from .bank_alert import BankAlertClient
from .transaction_store import TransactionStore
from .conversation_analysis import analyze_conversation, CallAnalysisStore
import time

app = FastAPI(title="Parakh (परख) AI — UPI Fraud Intervention Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = TransactionStore(DATA_DIR / "transactions.json")
evidence = EvidenceStore(DATA_DIR / "evidence_chain.json")
call_store = CallAnalysisStore(DATA_DIR / "call_analyses.json")
RECORDINGS_DIR = DATA_DIR / "recordings"
RECORDINGS_DIR.mkdir(exist_ok=True)
policy = load_policy(DATA_DIR / "policy.json")
engine = RiskEngine(policy)
bank = BankAlertClient(hmac_key=policy.get("alerts", {}).get("hmac_key", "dev-bank-alert-key-change-me"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _build_decision(risk_level: str, risk_score: float, txn: ScoreRequest, explanation: list, warnings: list) -> Decision:
    holds = policy.get("holds", {})
    verification_threshold = policy.get("verification_threshold", 55.0)
    cooling_off_threshold = policy.get("cooling_off_threshold", 85.0)
    hard_block_threshold = policy.get("hard_block_threshold", 95.0)

    if risk_level == "critical":
        if risk_score >= hard_block_threshold:
            action = "block"
            hold_hours = 999.0
            steps = [
                {"step": "block_payment", "description": "Payment blocked for user safety."},
                {"step": "notify_bank", "description": "Bank fraud desk notified via secure alert."},
                {"step": "contact_user", "description": "User contacted via registered channels."},
            ]
        elif risk_score >= cooling_off_threshold:
            action = "cooling_off_wallet"
            hold_hours = holds.get("critical_hours", 24.0)
            steps = [
                {"step": "cooling_off_wallet", "description": f"Funds moved to cooling-off wallet for {hold_hours:.0f} hours."},
                {"step": "notify_bank", "description": "Bank fraud desk notified via secure alert."},
                {"step": "trusted_contact_review", "description": "Trusted contact verification offered."},
            ]
        else:
            action = "hold"
            hold_hours = holds.get("critical_hours", 24.0)
            steps = [
                {"step": "hold_payment", "description": f"Payment held for {hold_hours:.0f} hours."},
                {"step": "independent_verification", "description": "OTP + trusted contact verification required."},
                {"step": "notify_bank", "description": "Bank fraud desk notified via secure alert."},
            ]
    elif risk_level == "high":
        action = "verify"
        hold_hours = holds.get("high_hours", 2.0)
        steps = [
            {"step": "hold_payment", "description": f"Payment held for {hold_hours:.0f} hours pending verification."},
            {"step": "independent_verification", "description": "OTP verification required before release."},
        ]
    else:
        action = "allow"
        hold_hours = 0.0
        if risk_score >= verification_threshold * 0.85:
            steps = [{"step": "display_warning", "description": "Warning banner displayed."}]
        else:
            steps = [{"step": "display_notice", "description": "Payment processed normally."}]

    urgent_text = txn.urgency_text or ""
    if urgent_text:
        u = detect_urgency(urgent_text)
        if u["urgency_score"] > 0.35 and action == "allow":
            action = "coach"
            steps.insert(0, {"step": "coaching_banner", "description": "Real-time coaching banner shown: verify you are not being pressured."})

    lang = "hi" if any("\u0900" <= ch <= "\u097F" for ch in (txn.urgency_text or "")) else "en"
    messages = MESSAGES.get(lang, MESSAGES["en"])
    if action == "block":
        msg_key = "block"
    elif action == "cooling_off_wallet":
        msg_key = "cooling"
    elif action == "verify":
        msg_key = "verify" if risk_level == "high" else "high"
    elif action == "coach":
        msg_key = "coach"
    elif risk_level == "medium":
        msg_key = "medium"
    else:
        msg_key = "low"

    return Decision(
        action=action,
        risk_level=risk_level,
        risk_score=round(risk_score, 2),
        hold_hours=hold_hours,
        steps=steps,
        messages=messages,
        verified=False,
    )


@app.get("/")
def root():
    return {"service": "Parakh (परख) AI — UPI Fraud Intervention Engine", "docs": "/docs", "simulator": "/static/index.html", "dashboard": "/static/dashboard.html"}


@app.post("/api/score", response_model=ScoreResponse)
def score_transaction(txn: ScoreRequest):
    result = engine.score(
        txn.transaction,
        txn.user,
        txn.call,
        txn.device,
        txn.voice,
        urgency_text=txn.urgency_text,
    )
    decision = _build_decision(result.level, result.score, txn, result.explanation, result.warnings)
    llm_opinion = None

    if txn.use_llm:
        from .llm_analysis import analyze_with_llm, llm_available, llm_settings
        if llm_available():
            turns = txn.transcript_turns
            if not turns and txn.urgency_text:
                turns = [{"speaker": "caller", "text": txn.urgency_text}]
            context = {
                "transaction": txn.transaction.model_dump(),
                "user": txn.user.model_dump(),
                "call": txn.call.model_dump(),
                "device": txn.device.model_dump(),
                "voice": txn.voice.model_dump(),
            }
            llm_opinion = analyze_with_llm(turns or [], context=context, settings=llm_settings())
            if llm_opinion and llm_opinion["verdict"] == "FRAUD" and decision.action == "allow":
                decision = _build_decision("high", max(75.0, result.score), txn, result.explanation, result.warnings)
                decision.action = "verify"
                decision.steps.insert(0, {
                    "step": "ai_agent_escalation",
                    "description": f"AI agent ({llm_opinion.get('llm_model')}) classified the conversation as FRAUD — verification enforced.",
                })
                result.warnings.append("AI agent (LLM) flagged the conversation as fraud — verification enforced")
            elif llm_opinion and llm_opinion["verdict"] == "LEGITIMATE" and decision.action in ("block", "cooling_off_wallet", "hold"):
                result.warnings.append("Note: AI agent (LLM) considers the conversation legitimate — conservative hold kept")

    txn_id = store.create(txn, {"score": result.score, "level": result.level, "decision": decision.model_dump(), "llm_opinion": llm_opinion})

    evidence_id = None
    bank_alert_id = None
    intervention_required = decision.action in ("hold", "verify", "block", "cooling_off_wallet")

    if intervention_required:
        evidence_id = evidence.append(
            "intervention",
            {
                "risk_score": result.score,
                "risk_level": result.level,
                "action": decision.action,
                "llm_opinion": llm_opinion,
                "features": [c.as_dict() for c in result.contributions],
            },
            parent_txn_id=txn_id,
        )["entry_id"]

    min_alert_level = policy.get("alerts", {}).get("min_level", "high")
    alert_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    if alert_levels.get(result.level, 0) >= alert_levels.get(min_alert_level, 2):
        alert = bank.send_alert(txn_id=txn_id, risk_level=result.level, risk_score=result.score, summary=" | ".join(result.explanation[:3]))
        bank_alert_id = alert["payload"]["alert_id"]

    return ScoreResponse(
        txn_id=txn_id,
        risk_score=result.score,
        risk_level=result.level,
        decision=decision,
        feature_breakdown=[c.as_dict() for c in result.contributions],
        explanation=result.explanation,
        warnings=result.warnings,
        hold_hours=decision.hold_hours,
        intervention_required=intervention_required,
        evidence_id=evidence_id,
        bank_alert_id=bank_alert_id,
        llm_opinion=llm_opinion,
    )


@app.post("/api/proceed")
def proceed(req: ProceedRequest):
    txn = store.get(req.txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    method = req.verification_method or "none"
    decision = txn["decision"]
    if decision["action"] in ("block",):
        store.update_decision(txn["txn_id"], decision, "blocked")
        return {"status": "blocked", "message": "Payment remains blocked. Contact your bank."}
    if method == "cooling_off_accept":
        decision["verified"] = True
        decision["action"] = "allow"
        store.update_decision(txn["txn_id"], decision, "processed")
        evidence.append("proceed", {"method": method, "outcome": "released_from_cooling_off"}, parent_txn_id=txn["txn_id"])
        return {"status": "released", "message": "Payment released from cooling-off wallet."}
    if method in ("otp", "trusted_contact", "none"):
        decision["verified"] = True
        decision["action"] = "allow"
        store.update_decision(txn["txn_id"], decision, "processed")
        evidence.append("proceed", {"method": method, "outcome": "released_after_verification"}, parent_txn_id=txn["txn_id"])
        return {"status": "released", "message": f"Payment released after verification ({method})."}
    raise HTTPException(400, "Unknown verification method")


@app.post("/api/cancel")
def cancel(req: CancelRequest):
    txn = store.get(req.txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    decision = txn["decision"]
    decision["action"] = "cancelled"
    store.update_decision(txn["txn_id"], decision, "cancelled")
    evidence.append("cancel", {"reason": "user_cancelled"}, parent_txn_id=txn["txn_id"])
    return {"status": "cancelled", "message": "Payment cancelled. No funds were moved."}


@app.post("/api/override")
def override(req: OverrideRequest):
    txn = store.get(req.txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    override_info = {
        "override_to": req.override_to,
        "reason": req.reason,
        "verified_via_otp": req.verified_via_otp,
        "verified_via_trusted_contact": req.verified_via_trusted_contact,
        "operator_id": req.operator_id,
    }
    store.set_override(txn["txn_id"], override_info)
    evidence.append("override", override_info, parent_txn_id=txn["txn_id"])
    return {"status": "overridden", "txn_id": txn["txn_id"], **override_info}


@app.post("/api/feedback")
def feedback(req: FeedbackRequest):
    txn = store.get(req.txn_id)
    if not txn:
        raise HTTPException(404, "Transaction not found")
    fb = {"rating": req.rating, "label": req.label, "comment": req.comment}
    store.set_feedback(txn["txn_id"], fb)
    evidence.append("feedback", fb, parent_txn_id=txn["txn_id"])
    return {"status": "recorded", "txn_id": txn["txn_id"], **fb}


@app.get("/api/evidence/latest")
def evidence_latest(n: int = 5):
    n = max(1, min(50, n))
    entries = evidence.chain[-n:]
    return {"entries": list(reversed(entries)), "total": len(evidence.chain)}


@app.get("/api/evidence/{txn_id}")
def get_evidence(txn_id: str):
    entries = evidence.find_txn(txn_id)
    if not entries:
        raise HTTPException(404, "No evidence for this transaction")
    return {"txn_id": txn_id, "entries": entries, "chain_status": evidence.verify_chain()}


@app.get("/api/evidence/chain/verify")
def verify_chain():
    return evidence.verify_chain()


@app.get("/api/alerts")
def alerts():
    records = bank.log()
    for record in records:
        record["signature_valid"] = bank.verify_signature(record)
    return {"alerts": records}


@app.get("/api/transactions")
def transactions():
    return {"transactions": store.all()}


@app.get("/api/stats")
def stats():
    return store.stats()


@app.get("/api/urgency")
def urgency(text: str = ""):
    return detect_urgency(text)


@app.get("/api/voice/analyze")
def voice_analyze(prob: Optional[float] = None, conf: Optional[float] = None, dur: Optional[float] = None):
    return analyze_voice(prob, conf, dur)


@app.post("/api/conversation/analyze")
def conversation_analyze(payload: dict):
    """NLP/LLM analysis of a call transcript → intent, pressure, red flags, final opinion.

    engine: "auto" (LLM when configured, else NLP) | "nlp" | "llm"
    context: optional full-situation context (transaction/call/device/voice) for the LLM.
    """
    turns = payload.get("turns")
    if turns is None:
        raise HTTPException(400, "Provide 'turns' (list of {speaker, text} / strings / raw text)")
    engine_mode = payload.get("engine", "auto")
    if engine_mode not in ("auto", "nlp", "llm"):
        raise HTTPException(400, "engine must be 'auto', 'nlp' or 'llm'")

    from .llm_analysis import analyze_with_llm, llm_available, merge_into_analysis
    use_llm = engine_mode == "llm" or (engine_mode == "auto" and llm_available())

    analysis = analyze_conversation(turns, source=payload.get("source", "api"), txn_id=payload.get("txn_id"))
    if analysis.get("analysis_id") is None:
        raise HTTPException(400, analysis.get("error", "Empty conversation"))
    analysis["engine"] = "nlp"

    if use_llm:
        llm = analyze_with_llm(turns, context=payload.get("context"))
        if llm:
            analysis = merge_into_analysis(analysis, llm)
        else:
            analysis["llm_note"] = "LLM engine requested but unavailable (set PARAKH_LLM_API_KEY) — fell back to NLP rules."

    if payload.get("persist", True):
        call_store.append_analysis(analysis)
    return analysis


@app.get("/api/conversation/recent")
def conversation_recent(n: int = 10):
    return {"analyses": call_store.recent(max(1, min(50, n)), kind="analysis"), "total": len(call_store._data)}


@app.post("/api/call/upload")
async def call_upload(file: UploadFile = File(...), transcript: Optional[str] = Form(None), txn_id: Optional[str] = Form(None), engine: str = Form("auto")):
    """Upload a call recording (wav/mp3/webm/ogg). Optionally attach a transcript —
    analysis runs on the transcript (live transcription via browser Web Speech API
    is offered on the simulator)."""
    if not file.filename:
        raise HTTPException(400, "No file provided")
    safe_name = Path(file.filename).name.replace("\\", "_").replace("/", "_")
    ext = Path(safe_name).suffix.lower() or ".audio"
    if ext not in {".wav", ".mp3", ".webm", ".ogg", ".m4a", ".aac", ".flac", ".amr"}:
        raise HTTPException(400, f"Unsupported audio format: {ext}")
    rec_path = RECORDINGS_DIR / (f"rec-{int(time.time())}-{safe_name}")
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(413, "Recording exceeds 25 MB limit")
    rec_path.write_bytes(data)

    analysis = None
    if transcript and transcript.strip():
        turns = transcript.strip().splitlines() if "\n" in transcript else [transcript.strip()]
        analysis = conversation_analyze({"turns": turns, "source": "upload", "txn_id": txn_id, "engine": engine})

    meta = {
        "filename": safe_name,
        "size_bytes": len(data),
        "format": ext,
        "stored_as": rec_path.name,
        "transcript_provided": bool(transcript and transcript.strip()),
        "analysis_id": analysis.get("analysis_id") if analysis else None,
    }
    rec_id = call_store.append_recording(meta)
    return {"recording_id": rec_id, **meta, "analysis": analysis}


@app.get("/api/call/recordings")
def call_recordings(n: int = 20):
    return {"recordings": call_store.recent(max(1, min(50, n)), kind="recording")}


@app.get("/api/llm/status")
def llm_status():
    from .llm_analysis import llm_available, llm_settings
    s = llm_settings()
    return {
        "configured": llm_available(),
        "model": s["model"] if llm_available() else None,
        "base_url": s["base_url"] if llm_available() else None,
        "note": "Set PARAKH_LLM_API_KEY / PARAKH_LLM_MODEL / PARAKH_LLM_BASE_URL to enable the AI-agent engine." if not llm_available() else None,
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "chain_verified": evidence.verify_chain()["verified"]}


@app.get("/api/policy")
def get_policy():
    return policy


@app.post("/api/policy")
def update_policy(new_policy: dict):
    global engine, policy
    for key in new_policy:
        if key not in {"thresholds", "holds", "verification_threshold", "cooling_off_threshold", "hard_block_threshold", "voice_risk_weight_cap", "urgent_critical_bonus", "pattern_bonus", "signature_bonus", "voice_pressure_bonus", "social_engineering_bonus", "alerts"}:
            raise HTTPException(400, f"Unknown policy key: {key}")
    policy.update(new_policy)
    from .config import save_policy
    save_policy(policy, DATA_DIR / "policy.json")
    engine = RiskEngine(policy)
    return {"status": "updated", "policy": policy}