from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class FeatureContribution:
    name: str
    value: float
    weight: float
    contribution: float
    reason: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 4),
            "weight": round(self.weight, 4),
            "contribution": round(self.contribution, 4),
            "reason": self.reason,
        }


@dataclass
class RiskResult:
    score: float
    level: str
    contributions: List[FeatureContribution] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    explanation: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "level": self.level,
            "contributions": [c.as_dict() for c in self.contributions],
            "warnings": self.warnings,
            "explanation": self.explanation,
        }


class RiskEngine:
    SENSITIVITY_PENALTY = 0.92
    PUBLISHED_WEIGHTS: Dict[str, float] = {
        "new_beneficiary": 0.14,
        "amount_deviation": 0.18,
        "balance_drain": 0.12,
        "call_screen_share": 0.20,
        "device_change": 0.08,
        "velocity": 0.10,
        "urgency": 0.10,
        "voice_risk": 0.25,
    }

    def __init__(self, policy: Optional[Dict[str, Any]] = None):
        self.policy = policy or {}

    def _thresholds(self) -> Dict[str, float]:
        return self.policy.get("thresholds", {"low": 30.0, "medium": 55.0, "high": 75.0, "critical": 85.0})

    def _level_for(self, score: float) -> str:
        t = self._thresholds()
        if score >= t["critical"]:
            return "critical"
        if score >= t["high"]:
            return "high"
        if score >= t["medium"]:
            return "medium"
        if score >= t["low"]:
            return "medium"
        return "low"

    def _clamp(self, value: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, value))

    def _round_score(self, value: float) -> float:
        return round(self._clamp(value), 2)

    def _map01(self, value: float, lo: float, hi: float, invert: bool = False) -> float:
        if hi <= lo:
            return 0.0 if not invert else 1.0
        scaled = (value - lo) / (hi - lo)
        scaled = self._clamp(scaled, 0.0, 1.0)
        return 1.0 - scaled if invert else scaled

    def _feature(self, name: str, value: float, weight: float, contribution: float, reason: str) -> FeatureContribution:
        return FeatureContribution(
            name=name,
            value=round(self._clamp(value, 0.0, 1.0), 4),
            weight=round(weight, 4),
            contribution=self._clamp(contribution * 100),
            reason=reason,
        )

    def score(self, txn: Any, user: Any, call: Any, device: Any, voice: Any, urgency_text: Optional[str] = None, urgency_bonus: Optional[float] = None) -> RiskResult:
        contributions: List[FeatureContribution] = []
        warnings: List[str] = []
        explanation: List[str] = []

        new_beneficiary_value, new_beneficiary_reason = self._new_beneficiary(txn)
        contributions.append(self._feature("new_beneficiary", new_beneficiary_value, self.PUBLISHED_WEIGHTS["new_beneficiary"], new_beneficiary_value * self.PUBLISHED_WEIGHTS["new_beneficiary"], new_beneficiary_reason))

        amount_value, amount_reason = self._amount_deviation(txn)
        contributions.append(self._feature("amount_deviation", amount_value, self.PUBLISHED_WEIGHTS["amount_deviation"], amount_value * self.PUBLISHED_WEIGHTS["amount_deviation"], amount_reason))

        drain_value, drain_reason = self._balance_drain(txn)
        contributions.append(self._feature("balance_drain", drain_value, self.PUBLISHED_WEIGHTS["balance_drain"], drain_value * self.PUBLISHED_WEIGHTS["balance_drain"], drain_reason))

        call_value, call_reason = self._call_screen_share(call)
        contributions.append(self._feature("call_screen_share", call_value, self.PUBLISHED_WEIGHTS["call_screen_share"], call_value * self.PUBLISHED_WEIGHTS["call_screen_share"], call_reason))

        device_value, device_reason = self._device_change(device)
        contributions.append(self._feature("device_change", device_value, self.PUBLISHED_WEIGHTS["device_change"], device_value * self.PUBLISHED_WEIGHTS["device_change"], device_reason))

        velocity_value, velocity_reason = self._velocity(txn)
        contributions.append(self._feature("velocity", velocity_value, self.PUBLISHED_WEIGHTS["velocity"], velocity_value * self.PUBLISHED_WEIGHTS["velocity"], velocity_reason))

        urgency_value, urgency_reason = self._urgency(urgency_text)
        contributions.append(self._feature("urgency", urgency_value, self.PUBLISHED_WEIGHTS["urgency"], urgency_value * self.PUBLISHED_WEIGHTS["urgency"], urgency_reason))

        voice_value, voice_reason = self._voice_risk(voice, call)
        voice_weight = self.PUBLISHED_WEIGHTS["voice_risk"]
        contributions.append(self._feature("voice_risk", voice_value, voice_weight, voice_value * voice_weight, voice_reason))

        raw = sum(c.contribution for c in contributions)
        sensitivity = self.policy.get("sensitivity", self.SENSITIVITY_PENALTY)
        score = self._clamp(raw * sensitivity)

        extra = self.policy.get("urgent_critical_bonus", 15.0)
        if urgency_value > 0.6:
            score = self._clamp(score + extra * urgency_value)
            explanation.append(f"High conversational pressure detected: +{extra * urgency_value:.1f}")

        pattern_bonus = self.policy.get("pattern_bonus", 10.0)
        if new_beneficiary_value > 0.7 and call_value > 0.7:
            score = self._clamp(score + pattern_bonus)
            explanation.append(f"Impersonation pattern (new beneficiary + live call/screen-share): +{pattern_bonus:.1f}")
            if urgency_value > 0.6:
                signature_bonus = self.policy.get("signature_bonus", 5.0)
                score = self._clamp(score + signature_bonus)
                explanation.append(f"Full scam signature (new beneficiary + call + pressure): +{signature_bonus:.1f}")

        voice_pressure_bonus = self.policy.get("voice_pressure_bonus", 8.0)
        if voice_value > 0.5 and urgency_value > 0.35:
            score = self._clamp(score + voice_pressure_bonus)
            explanation.append(f"Cloned-voice pressure pattern: +{voice_pressure_bonus:.1f}")

        social_bonus = self.policy.get("social_engineering_bonus", 12.0)
        if call_value >= 0.25 and urgency_value > 0.35 and new_beneficiary_value >= 0.2:
            score = self._clamp(score + social_bonus)
            explanation.append(f"Social-engineering pattern (call + pressure + fresh beneficiary): +{social_bonus:.1f}")

        level = self._level_for(score)

        if new_beneficiary_value > 0.5:
            warnings.append("Beneficiary added recently")
        if amount_value > 0.7:
            warnings.append("Amount significantly above your usual pattern")
        if drain_value > 0.7:
            warnings.append("This payment would drain most of your balance")
        if call_value > 0.7:
            warnings.append("Active call with screen sharing detected")
        if device_value > 0.7:
            warnings.append("Device change detected")
        if velocity_value > 0.7:
            warnings.append("Unusual payment velocity")
        if urgency_value > 0.5:
            warnings.append("Conversation shows pressure or urgency cues")
        if voice_value > 0.5:
            warnings.append("Possible voice-clone indicators detected")

        for c in contributions:
            explanation.append(f"{c.reason} (+{c.contribution:.1f})")

        explanation.append(f"Base score after sensitivity adjustment: {score:.1f}")

        return RiskResult(score=self._round_score(score), level=level, contributions=contributions, warnings=warnings, explanation=explanation)

    def _new_beneficiary(self, txn) -> tuple[float, str]:
        if txn.is_new_beneficiary:
            return 1.0, "Beneficiary was added very recently"
        days = txn.beneficiary_added_days_ago
        if days is None:
            if txn.beneficiary_previous_tx_count == 0:
                return 0.7, "Beneficiary has no prior transaction history"
            return 0.1, "Beneficiary has transaction history"
        if days <= 1:
            return 0.9, f"Beneficiary added {days:.0f} day(s) ago"
        if days <= 7:
            return 0.5, f"Beneficiary added {days:.0f} days ago"
        if days <= 30:
            return 0.2, f"Beneficiary added {days:.0f} days ago"
        return 0.05, "Long-standing beneficiary"

    def _amount_deviation(self, txn) -> tuple[float, str]:
        avg = txn.txn_amount_30d_avg
        if avg is None or avg <= 0:
            if txn.amount >= 10000:
                return 0.6, "No spending baseline; large amount"
            return 0.1, "No spending baseline; small amount"
        ratio = txn.amount / avg
        if ratio >= 15:
            value = 1.0
        elif ratio >= 8:
            value = 0.85
        elif ratio >= 4:
            value = 0.6
        elif ratio >= 2:
            value = 0.35
        elif ratio <= 0.5:
            value = 0.05
        else:
            value = 0.0
        reason = f"Amount is {ratio:.1f}x your 30-day average (₹{avg:.0f})"
        return value, reason

    def _balance_drain(self, txn) -> tuple[float, str]:
        if txn.account_balance <= 0:
            return 0.0, "No account balance data"
        ratio = txn.balance_after_tx / txn.account_balance
        drained = 1.0 - ratio
        if txn.balance_after_tx >= txn.account_balance:
            return 0.0, "No balance drain"
        if drained >= 0.95:
            value = 1.0
        elif drained >= 0.8:
            value = 0.8
        elif drained >= 0.6:
            value = 0.5
        else:
            value = 0.0
        return value, f"Leaves only {ratio * 100:.0f}% of account balance"

    def _call_screen_share(self, call) -> tuple[float, str]:
        score = 0.0
        reasons = []
        if call.call_type == "phone":
            score += 0.25
            reasons.append("active phone call")
        elif call.call_type == "video":
            score += 0.35
            reasons.append("active video call")
        if call.call_status == "ended_within_60s":
            score += 0.15
            reasons.append("call ended within last 60s")
        if call.screen_share_active:
            score += 0.5
            reasons.append("screen sharing active")
        if call.caller_number_not_in_contacts:
            score += 0.2
            reasons.append("caller not in contacts")
        if call.call_type == "none" and not call.screen_share_active:
            return 0.0, "No active call or screen-sharing context"
        value = self._clamp(score)
        return value, "Call/screen-share signals: " + ", ".join(reasons)

    def _device_change(self, device) -> tuple[float, str]:
        value = 0.0
        reasons = []
        if device.device_changed:
            value += 0.55
            reasons.append("device recently changed")
        if device.rooted_or_emulator:
            value += 0.3
            reasons.append("rooted/emulator environment")
        sessions = device.app_session_count_24h
        if sessions is not None and sessions == 1:
            value += 0.05
            reasons.append("single app session today")
        loc = device.location_change_km or 0.0
        if loc > 500:
            value += 0.15
            reasons.append(f"large location change ({loc:.0f} km)")
        if not reasons:
            return 0.0, "Stable device environment"
        return self._clamp(value), "Device signals: " + ", ".join(reasons)

    def _velocity(self, txn) -> tuple[float, str]:
        count = txn.txn_count_last_1h
        if count >= 8:
            value = 1.0
        elif count >= 5:
            value = 0.7
        elif count >= 3:
            value = 0.4
        elif count >= 2:
            value = 0.2
        else:
            value = 0.0
        if count == 0:
            return 0.0, "Normal payment velocity"
        return value, f"{count} payment(s) in the last hour"

    def _urgency(self, text: Optional[str]) -> tuple[float, str]:
        from .nlp_urgency import detect_urgency
        if not text:
            return 0.0, "No conversation text provided"
        result = detect_urgency(text)
        return result["urgency_score"], f"Conversation urgency: {result['matched_terms']}"

    def _voice_risk(self, voice, call) -> tuple[float, str]:
        prob = voice.acoustic_clone_probability
        if prob is None:
            return 0.0, "No voice sample available"
        if call.call_type == "none":
            return 0.15 * prob, "Voice risk noted but no active call context"
        band_factor = 1.0
        if voice.model_confidence is not None:
            band_factor = self._map01(voice.model_confidence, 0.5, 0.99)
        return self._clamp(prob * band_factor), f"Voice-clone probability {prob:.0%} (model confidence {voice.model_confidence or 0:.0%})"