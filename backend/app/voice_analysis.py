from typing import Dict, Optional


def confidence_band(probability: Optional[float]) -> str:
    if probability is None:
        return "no_data"
    if probability >= 0.85:
        return "high"
    if probability >= 0.6:
        return "medium"
    if probability >= 0.4:
        return "uncertain"
    return "low"


def analyze_voice(acoustic_clone_probability: Optional[float], model_confidence: Optional[float] = None, sample_duration_sec: Optional[float] = None) -> Dict:
    if acoustic_clone_probability is None:
        return {
            "verdict": "unavailable",
            "band": "no_data",
            "score": 0.0,
            "explanation": "No voice sample was available for analysis.",
        }

    prob = max(0.0, min(1.0, acoustic_clone_probability))
    conf = max(0.0, min(1.0, model_confidence if model_confidence is not None else 0.5))
    band = confidence_band(prob)

    factors = []
    if model_confidence is not None and model_confidence < 0.6:
        factors.append("model self-confidence is low")
    if sample_duration_sec is not None:
        if sample_duration_sec < 5:
            factors.append("sample shorter than 5s (less reliable)")
        elif sample_duration_sec > 30:
            factors.append("adequate sample duration")
    if not factors:
        factors.append("no quality flags")

    explanation = f"Voice-clone probability {prob:.0%} classified as {band} confidence band ({', '.join(factors)})."

    return {
        "verdict": "possible_clone" if band in ("high", "medium") else "inconclusive" if band == "uncertain" else "likely_authentic",
        "band": band,
        "score": round(prob, 4),
        "model_confidence": round(conf, 4),
        "sample_duration_sec": sample_duration_sec,
        "explanation": explanation,
    }