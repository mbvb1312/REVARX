from typing import Dict, Tuple

from agent_core.message_generator import generate_message
from backend.database import Message, SessionLocal


def generate_ab_variants(
    lead: dict,
    campaign_id: int,
    tone: str,
    channel: str,
    db=None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Generates two message variants for a lead and stores them in the DB.
    Returns (variant_a, variant_b).
    """
    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        variant_a = generate_message(lead, tone, channel)
        variant_b = generate_message(lead, tone, channel)

        msg_a = Message(
            lead_id=lead["id"],
            campaign_id=campaign_id,
            variant="A",
            content=variant_a.get("message", ""),
            channel=channel,
            tone=tone,
            status="pending",
        )
        msg_b = Message(
            lead_id=lead["id"],
            campaign_id=campaign_id,
            variant="B",
            content=variant_b.get("message", ""),
            channel=channel,
            tone=tone,
            status="pending",
        )

        db.add_all([msg_a, msg_b])
        db.commit()
        return variant_a, variant_b
    finally:
        if owns_session:
            db.close()
