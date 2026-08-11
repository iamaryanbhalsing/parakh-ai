import json
import sys
import time
from pathlib import Path

from app.synthetic_data import generate_dataset, generate_scenario
from app.risk_engine import RiskEngine
from app.config import DEFAULT_POLICY
from app.schemas import ScoreRequest, TransactionContext, UserContext, CallContext, DeviceContext, VoiceRisk

INTERVENTION_ACTIONS = {"hold", "verify", "block", "cooling_off_wallet"}


def scenario_to_request(sc: dict) -> ScoreRequest:
    return ScoreRequest(
        transaction=TransactionContext(
            amount=sc["amount"],
            beneficiary_added_days_ago=sc.get("beneficiary_added_days_ago"),
            is_new_beneficiary=sc.get("is_new_beneficiary", False),
            beneficiary_previous_tx_count=sc.get("beneficiary_previous_tx_count", 0),
            account_balance=sc["account_balance"],
            balance_after_tx=max(0.0, sc["account_balance"] - sc["amount"]),
            txn_amount_30d_avg=sc["txn_amount_30d_avg"],
            txn_amount_30d_max=sc["txn_amount_30d_max"],
            txn_count_last_1h=sc.get("txn_count_last_1h", 0),
            unusual_hour=sc.get("unusual_hour", False),
        ),
        user=UserContext(user_id=sc["user_id"], age=sc["age"]),
        call=CallContext(
            call_type=sc.get("call_type", "none"),
            call_status=sc.get("call_status", "none"),
            screen_share_active=sc.get("screen_share", False),
            caller_number_not_in_contacts=sc.get("caller_not_contacts", False),
        ),
        device=DeviceContext(device_changed=sc.get("device_changed", False)),
        voice=VoiceRisk(
            acoustic_clone_probability=sc.get("voice_prob"),
            model_confidence=sc.get("voice_conf"),
        ),
        urgency_text=sc.get("urgency_text"),
    )


def decision_action_for(level: str, score: float) -> str:
    if level == "critical":
        if score >= 95:
            return "block"
        if score >= 85:
            return "cooling_off_wallet"
        return "hold"
    if level == "high":
        return "verify"
    return "allow"


def run_evaluation(n: int = 250, seed: int = 42, predict_threshold: float = 55.0) -> dict:
    engine = RiskEngine(DEFAULT_POLICY)
    dataset = generate_dataset(n, seed)
    latencies = []
    tp = fp = tn = fn = 0
    prediction_log = []

    for sc in dataset:
        req = scenario_to_request(sc)
        start = time.perf_counter()
        result = engine.score(
            req.transaction, req.user, req.call, req.device, req.voice,
            urgency_text=req.urgency_text,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        latencies.append(latency_ms)
        predicted_risky = result.score >= predict_threshold
        actual = sc["label"] == "fraud"
        if predicted_risky and actual:
            tp += 1
        elif predicted_risky and not actual:
            fp += 1
        elif not predicted_risky and actual:
            fn += 1
        else:
            tn += 1
        prediction_log.append({
            "preset": sc.get("preset", "n/a"),
            "label": sc["label"],
            "score": round(result.score, 2),
            "level": result.level,
            "predicted_risky": predicted_risky,
        })

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fp_rate = fp / (fp + tn) if fp + tn else 0.0

    return {
        "n_scenarios": n,
        "threshold": predict_threshold,
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_positive_rate": round(fp_rate, 4),
        "avg_latency_ms": round(sum(latencies) / len(latencies), 4),
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)], 4),
        "predictions": prediction_log,
    }


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    results = run_evaluation(n, seed)
    (output_dir / "evaluation_results.json").write_text(json.dumps(
        {k: v for k, v in results.items() if k != "predictions"}, indent=2, default=str
    ), encoding="utf-8")
    summary = {k: v for k, v in results.items() if k != "predictions"}
    for k, v in summary.items():
        print(f"{k}: {v}")
    return summary


if __name__ == "__main__":
    main()