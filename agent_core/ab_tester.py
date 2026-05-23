import random
from typing import Any, Dict, Tuple

from agent_core.message_generator import generate_message
from backend.database import Lead, Message, Reply, SessionLocal

POSITIVE_CLASSES = {"hot", "warm"}


def age_group(age: int | None) -> str:
    if age is None:
        return "Unknown"
    try:
        age = int(age)
    except (TypeError, ValueError):
        return "Unknown"
    if age <= 20:
        return "10-20"
    if age <= 30:
        return "21-30"
    if age <= 40:
        return "31-40"
    if age <= 50:
        return "41-50"
    if age <= 60:
        return "51-60"
    return "60+"


def _value(obj: Any, field: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def _outcome_value(classification: str | None) -> float:
    classification = (classification or "").lower()
    if classification == "hot":
        return 1.0
    if classification == "warm":
        return 0.65
    if classification == "cold":
        return 0.1
    if classification == "unsubscribe":
        return -0.6
    return 0.0


def _similarity_weight(candidate: Lead, age: int | None, gender: str | None, state: str | None, product_category: str | None) -> float:
    weight = 0.15

    if product_category and candidate.product_category and candidate.product_category.lower() == product_category.lower():
        weight += 1.5
    if state and candidate.state and candidate.state.lower() == state.lower():
        weight += 1.0
    if gender and candidate.gender and candidate.gender.lower() == gender.lower():
        weight += 0.75
    if age_group(candidate.age) == age_group(age) and age_group(age) != "Unknown":
        weight += 1.0

    return weight


def recommend_variant_with_reason(
    age: int | None,
    gender: str | None,
    state: str | None,
    product_category: str | None,
    db,
) -> dict:
    """
    Weighted A/B learner.
    Hot/warm replies increase future probability. Cold replies barely help.
    Unsubscribes penalize. No response counts as zero and lowers the average.
    """
    rows = (
        db.query(Message, Lead, Reply)
        .join(Lead, Lead.id == Message.lead_id)
        .outerjoin(Reply, Reply.message_id == Message.id)
        .filter(Message.status == "sent", Message.variant.in_(["A", "B"]))
        .all()
    )

    weighted_scores = {"A": 0.0, "B": 0.0}
    weighted_exposures = {"A": 0.0, "B": 0.0}

    for message, candidate, reply in rows:
        variant = (message.variant or "").upper()
        if variant not in weighted_scores:
            continue
        weight = _similarity_weight(candidate, age, gender, state, product_category)
        weighted_scores[variant] += weight * _outcome_value(reply.classification if reply else None)
        weighted_exposures[variant] += weight

    rates = {}
    for variant in ("A", "B"):
        exposure = weighted_exposures[variant]
        rates[variant] = weighted_scores[variant] / exposure if exposure else None

    if rates["A"] is None and rates["B"] is None:
        selected = random.choice(["A", "B"])
        return {
            "variant": selected,
            "reason": "No historical match yet, using 50/50 exploration.",
            "scores": rates,
            "age_group": age_group(age),
        }

    if rates["A"] is None:
        selected = "B"
    elif rates["B"] is None:
        selected = "A"
    elif abs(rates["A"] - rates["B"]) < 0.04:
        selected = random.choice(["A", "B"])
    else:
        selected = "A" if rates["A"] > rates["B"] else "B"

    label = "Professional" if selected == "A" else "Friendly"
    return {
        "variant": selected,
        "reason": f"{label} variant has the stronger weighted conversion score for similar customers.",
        "scores": rates,
        "age_group": age_group(age),
    }


def recommend_variant(age, gender, state, product_category, db) -> str:
    return recommend_variant_with_reason(age, gender, state, product_category, db)["variant"]


def recommend_variant_for_lead(lead: Any, db) -> dict:
    return recommend_variant_with_reason(
        _value(lead, "age"),
        _value(lead, "gender"),
        _value(lead, "state"),
        _value(lead, "product_category"),
        db,
    )


def generate_ab_variants(
    lead: dict,
    campaign_id: int,
    tone: str = "ab-test",
    channel: str = "email",
    db=None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Generates professional and friendly variants for comparison/previews.
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        variant_a = generate_message(lead, variant="A", channel=channel)
        variant_b = generate_message(lead, variant="B", channel=channel)

        msg_a = Message(
            lead_id=lead["id"],
            campaign_id=campaign_id,
            variant="A",
            content=variant_a.get("message", ""),
            channel=channel,
            tone="professional",
            status="pending",
            llm_used=variant_a.get("llm_used", "REVARX Local Template"),
        )
        msg_b = Message(
            lead_id=lead["id"],
            campaign_id=campaign_id,
            variant="B",
            content=variant_b.get("message", ""),
            channel=channel,
            tone="friendly",
            status="pending",
            llm_used=variant_b.get("llm_used", "REVARX Local Template"),
        )

        db.add_all([msg_a, msg_b])
        db.commit()
        return variant_a, variant_b
    finally:
        if owns_session:
            db.close()
