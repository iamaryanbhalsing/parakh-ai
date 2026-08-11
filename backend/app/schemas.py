from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class CallType(str, Enum):
    phone = "phone"
    video = "video"
    none = "none"


class CallStatus(str, Enum):
    active = "active"
    ended_60s = "ended_within_60s"
    none = "none"


class DeviceContext(BaseModel):
    device_changed: bool = Field(default=False, description="New device used in last 24h")
    rooted_or_emulator: bool = Field(default=False)
    app_session_count_24h: Optional[int] = Field(default=None, ge=0)
    location_change_km: Optional[float] = Field(default=0.0, ge=0.0)


class CallContext(BaseModel):
    call_type: CallType = CallType.none
    call_status: CallStatus = CallStatus.none
    screen_share_active: bool = False
    caller_number_not_in_contacts: bool = False
    call_duration_sec: Optional[float] = Field(default=None, ge=0.0)


class VoiceRisk(BaseModel):
    acoustic_clone_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    model_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    sample_duration_sec: Optional[float] = Field(default=None, ge=0.0)


class TransactionContext(BaseModel):
    amount: float = Field(..., gt=0)
    amount_confidence: float = Field(1.0, ge=0.0, le=1.0)
    beneficiary_added_days_ago: Optional[float] = Field(default=None, ge=0.0)
    is_new_beneficiary: bool = False
    beneficiary_previous_tx_count: int = Field(0, ge=0)
    balance_after_tx: float = Field(0.0, ge=0.0)
    account_balance: float = Field(0.0, ge=0.0)
    txn_amount_30d_avg: Optional[float] = Field(default=None, gt=0)
    txn_amount_30d_max: Optional[float] = Field(default=None, gt=0)
    txn_count_last_1h: int = Field(0, ge=0)
    unusual_hour: bool = False
    app_in_foreground: bool = True


class UserContext(BaseModel):
    user_id: str
    age: Optional[int] = Field(default=None, ge=18, le=120)
    flagged_vulnerable: bool = False
    history_payment_fail_30d: int = Field(0, ge=0)


class ScoreRequest(BaseModel):
    transaction: TransactionContext
    user: UserContext
    call: CallContext = CallContext()
    device: DeviceContext = DeviceContext()
    voice: VoiceRisk = VoiceRisk()
    urgency_text: Optional[str] = Field(default=None, max_length=2000)
    transcript_turns: Optional[List[Any]] = Field(default=None, description="Call transcript turns for the AI-agent (LLM) analysis")
    use_llm: bool = Field(default=False, description="Ask the configured AI agent (LLM) to review the whole situation")
    policy: Optional[Dict[str, Any]] = None


class OverrideRequest(BaseModel):
    txn_id: str
    override_to: str = Field(..., pattern="^(low|medium|high|critical)$")
    reason: str = Field(..., min_length=5, max_length=500)
    verified_via_otp: bool = False
    verified_via_trusted_contact: bool = False
    operator_id: Optional[str] = None


class FeedbackRequest(BaseModel):
    txn_id: str
    rating: int = Field(..., ge=1, le=5)
    label: Optional[str] = Field(default=None, pattern="^(fraud|false_positive|unclear)$")
    comment: Optional[str] = Field(default=None, max_length=1000)


class ProceedRequest(BaseModel):
    txn_id: str
    verification_method: Optional[str] = Field(default=None, pattern="^(none|otp|trusted_contact|cooling_off_accept)$")


class CancelRequest(BaseModel):
    txn_id: str


class Decision(BaseModel):
    action: str
    risk_level: str
    risk_score: float
    hold_hours: float = 0.0
    steps: List[Dict[str, Any]] = []
    messages: Dict[str, str] = {}
    verified: bool = False


class ScoreResponse(BaseModel):
    txn_id: str
    risk_score: float
    risk_level: str
    decision: Decision
    feature_breakdown: List[Dict[str, Any]]
    explanation: List[str]
    warnings: List[str]
    hold_hours: float
    intervention_required: bool
    evidence_id: Optional[str] = None
    bank_alert_id: Optional[str] = None
    llm_opinion: Optional[Dict[str, Any]] = None