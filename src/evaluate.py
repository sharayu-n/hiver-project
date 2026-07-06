import json
import os
import re
from pathlib import Path

DATASET_PATH = Path("data/dataset.jsonl")
PREDICTIONS_PATH = Path("outputs/predictions.jsonl")
SCORES_PATH = Path("outputs/scores.jsonl")
SUMMARY_PATH = Path("outputs/summary.json")


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def contains_any(text: str, phrases: list[str]) -> bool:
    text_n = normalize(text)
    return any(normalize(p) in text_n for p in phrases)


def point_match(point: str, reply: str, intent: str) -> bool:
    reply_n = normalize(reply)
    point_n = normalize(point)

    intent_rules = {
        "refund_request": {
            "apologize": ["sorry", "apologize", "apologies"],
            "request order number": ["order number", "order id", "order details", "send your order"],
            "mention refund process": ["refund", "processing the refund", "refund steps", "refund request"],
            "guarantee immediate refund": ["immediate refund", "guarantee a refund", "full refund right away"],
            "blame the customer": ["your fault", "because you", "you caused"],
        },
        "shipping_delay": {
            "acknowledge delay": ["sorry", "apologize", "delay", "late"],
            "request order number": ["order number", "order id", "order details"],
            "promise to check tracking": ["tracking", "shipment status", "check the status", "look into the shipment"],
            "promise exact delivery date": ["will arrive tomorrow", "exact delivery date", "guaranteed delivery"],
            "blame shipping carrier": ["carrier is at fault", "shipping company is the problem"],
        },
        "password_reset": {
            "acknowledge login issue": ["sorry", "trouble logging in", "login issue", "locked out"],
            "suggest forgot password": ["forgot password", "reset your password", "password reset"],
            "ask for account email": ["email associated", "account email", "email linked to the account"],
            "ask for password": ["send your password", "share your password"],
            "request sensitive credentials": ["password", "pin", "security answer"],
        },
        "order_cancellation": {
            "acknowledge cancellation request": ["cancel", "cancellation", "stop your order"],
            "request order number": ["order number", "order id", "order details"],
            "state cancellation depends on status": ["depends", "check whether", "if it has not shipped", "status"],
            "promise cancellation without checking": ["confirmed cancelled", "done immediately"],
            "mention refund without context": ["refund"] ,
        },
        "subscription_billing": {
            "acknowledge billing issue": ["sorry", "unexpected charge", "billing issue", "charge"],
            "request account email": ["account email", "email on the account", "email tied to the subscription"],
            "offer to investigate charge": ["investigate", "look into", "review the billing", "check the charge"],
            "confirm fraud": ["fraud", "unauthorized charge", "scam"],
            "promise immediate refund": ["immediate refund", "refund right away", "will refund now"],
        },
        "feature_request": {
            "thank the user": ["thanks", "thank you", "appreciate"],
            "acknowledge request": ["suggestion", "request", "feedback"],
            "say it will be shared with product team": ["shared with the team", "product team", "passed along", "logged your request"],
            "promise implementation": ["we will build", "it will be added", "coming soon"],
            "give timeline": ["by next week", "timeline", "eta"],
        },
        "bug_report": {
            "apologize": ["sorry", "apologize", "apologies"],
            "ask for repro steps": ["steps to reproduce", "repro steps", "what steps", "how to reproduce"],
            "ask for device/browser": ["device", "browser", "platform", "operating system"],
            "blame user": ["you did something wrong", "user error"],
            "claim fixed already": ["already fixed", "resolved", "known fixed"],
        },
        "account_locked": {
            "acknowledge lockout": ["locked out", "lockout", "blocked", "can't access"],
            "request account email": ["account email", "email tied to the account", "email on the account"],
            "mention security review": ["security lock", "review the lock", "security review", "verify"],
            "ask for password": ["send your password", "share your password"],
            "promise immediate unlock": ["unlock immediately", "restored right away", "instantly unlocked"],
        },
    }

    rules = intent_rules.get(intent, {})
    if point in rules:
        return contains_any(reply_n, rules[point])

    # Fallback: basic phrase/token overlap.
    tokens = [t for t in re.findall(r"[a-z0-9]+", point_n) if len(t) > 3]
    if not tokens:
        return False
    return all(t in reply_n for t in tokens)


def score_reply(row: dict, prediction: dict) -> dict:
    reply = prediction["generated_reply"]
    intent = row["intent"]
    required = row["required_points"]
    forbidden = row["forbidden_points"]

    matched_required = [p for p in required if point_match(p, reply, intent)]
    missing_required = [p for p in required if p not in matched_required]

    hit_forbidden = [p for p in forbidden if point_match(p, reply, intent)]

    coverage = len(matched_required) / max(1, len(required))
    clean = 1.0 - (len(hit_forbidden) / max(1, len(forbidden)))

    polite = contains_any(reply, ["sorry", "thanks", "thank you", "appreciate"])
    signed = contains_any(reply, ["best,", "best regards", "support team"])
    concise = len(reply.split()) <= 180

    tone_score = 1.0 if polite else 0.5
    format_score = 1.0 if signed else 0.5
    brevity_score = 1.0 if concise else 0.7

    final_score = round(
        100
        * (
            0.55 * coverage
            + 0.25 * max(clean, 0.0)
            + 0.10 * tone_score
            + 0.05 * format_score
            + 0.05 * brevity_score
        ),
        2,
    )

    reasons = []
    if matched_required:
        reasons.append(f"Covered: {', '.join(matched_required)}")
    if missing_required:
        reasons.append(f"Missing: {', '.join(missing_required)}")
    if hit_forbidden:
        reasons.append(f"Violations: {', '.join(hit_forbidden)}")
    if not hit_forbidden:
        reasons.append("No forbidden claims detected")
    if polite:
        reasons.append("Polite tone detected")
    if signed:
        reasons.append("Proper sign-off detected")

    return {
        "id": row["id"],
        "intent": intent,
        "coverage_score": round(coverage * 100, 2),
        "groundedness_score": round(max(clean, 0.0) * 100, 2),
        "tone_score": round(tone_score * 100, 2),
        "format_score": round(format_score * 100, 2),
        "brevity_score": round(brevity_score * 100, 2),
        "final_score": final_score,
        "matched_required": matched_required,
        "missing_required": missing_required,
        "forbidden_hits": hit_forbidden,
        "reason": "; ".join(reasons),
    }


def evaluate():
    dataset = load_jsonl(DATASET_PATH)
    predictions = load_jsonl(PREDICTIONS_PATH)
    pred_by_id = {p["id"]: p for p in predictions}

    os.makedirs("outputs", exist_ok=True)

    scores = []
    with SCORES_PATH.open("w", encoding="utf-8") as f:
        for row in dataset:
            pred = pred_by_id.get(row["id"])
            if not pred:
                continue
            scored = score_reply(row, pred)
            scores.append(scored)
            f.write(json.dumps(scored, ensure_ascii=False) + "\n")

    overall = round(sum(s["final_score"] for s in scores) / max(1, len(scores)), 2)

    summary = {
        "num_examples": len(scores),
        "overall_score": overall,
        "avg_coverage": round(sum(s["coverage_score"] for s in scores) / max(1, len(scores)), 2),
        "avg_groundedness": round(sum(s["groundedness_score"] for s in scores) / max(1, len(scores)), 2),
        "avg_tone": round(sum(s["tone_score"] for s in scores) / max(1, len(scores)), 2),
        "avg_format": round(sum(s["format_score"] for s in scores) / max(1, len(scores)), 2),
        "avg_brevity": round(sum(s["brevity_score"] for s in scores) / max(1, len(scores)), 2),
    }

    with SUMMARY_PATH.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\nEvaluation complete")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    evaluate()