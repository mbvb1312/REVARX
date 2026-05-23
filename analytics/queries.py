from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import text

from backend.database import Lead, Message, Reply, SessionLocal, engine

AGE_GROUP_SQL = """
CASE
    WHEN l.age IS NULL THEN 'Unknown'
    WHEN l.age <= 20 THEN '10-20'
    WHEN l.age <= 30 THEN '21-30'
    WHEN l.age <= 40 THEN '31-40'
    WHEN l.age <= 50 THEN '41-50'
    WHEN l.age <= 60 THEN '51-60'
    ELSE '60+'
END
"""


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator * 100) if denominator else 0, 1)


def get_funnel_stats(campaign_id: int = None) -> dict:
    with engine.connect() as conn:
        params = {}
        campaign_filter = ""
        reply_campaign_filter = ""
        if campaign_id:
            campaign_filter = " AND campaign_id = :campaign_id"
            reply_campaign_filter = " AND m.campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id

        total = conn.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0
        sent = conn.execute(
            text(f"SELECT COUNT(*) FROM messages WHERE status='sent'{campaign_filter}"),
            params,
        ).scalar() or 0
        replied = conn.execute(
            text(
                f"""
                SELECT COUNT(DISTINCT r.id)
                FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE 1=1{reply_campaign_filter}
                """
            ),
            params,
        ).scalar() or 0
        recovered = conn.execute(text("SELECT COUNT(*) FROM leads WHERE status IN ('hot', 'warm')")).scalar() or 0
        hot = conn.execute(text("SELECT COUNT(*) FROM leads WHERE status='hot'")).scalar() or 0

        return {
            "tracked": total,
            "sent": sent,
            "replied": replied,
            "recovered": recovered,
            "hot": hot,
            "reply_rate": _rate(replied, sent),
            "recovery_rate": _rate(recovered, sent),
            "estimated_revenue_recovered": recovered * 4500,
        }


def get_ab_results(campaign_id: int = None) -> dict:
    with engine.connect() as conn:
        params = {}
        campaign_filter = ""
        if campaign_id:
            campaign_filter = " AND m.campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id

        rows = conn.execute(
            text(
                f"""
                SELECT
                    m.variant,
                    COUNT(DISTINCT m.id) AS sent,
                    COUNT(DISTINCT r.id) AS replied,
                    SUM(CASE WHEN r.classification IN ('hot', 'warm') THEN 1 ELSE 0 END) AS converted
                FROM messages m
                LEFT JOIN replies r ON r.message_id = m.id
                WHERE m.variant IN ('A', 'B') AND m.status = 'sent'{campaign_filter}
                GROUP BY m.variant
                """
            ),
            params,
        ).fetchall()

        data = {
            "A": {"sent": 0, "replied": 0, "converted": 0},
            "B": {"sent": 0, "replied": 0, "converted": 0},
        }
        for row in rows:
            mapping = row._mapping
            data[mapping["variant"]] = {
                "sent": mapping["sent"] or 0,
                "replied": mapping["replied"] or 0,
                "converted": mapping["converted"] or 0,
            }

        a_rate = _rate(data["A"]["converted"], data["A"]["sent"])
        b_rate = _rate(data["B"]["converted"], data["B"]["sent"])
        winner = "A" if a_rate >= b_rate else "B"

        return {
            "variant_a_rate": a_rate,
            "variant_b_rate": b_rate,
            "variant_a_reply_rate": _rate(data["A"]["replied"], data["A"]["sent"]),
            "variant_b_reply_rate": _rate(data["B"]["replied"], data["B"]["sent"]),
            "variant_a_sent": data["A"]["sent"],
            "variant_b_sent": data["B"]["sent"],
            "winner": winner,
            "winner_label": "Professional" if winner == "A" else "Friendly",
        }


def get_lead_status_counts() -> dict:
    statuses = ["new", "pending", "hot", "warm", "cold", "no_response", "email_failed", "unsubscribed"]
    with engine.connect() as conn:
        results = {}
        for status in statuses:
            results[status] = conn.execute(
                text("SELECT COUNT(*) FROM leads WHERE status = :status"),
                {"status": status},
            ).scalar() or 0
        results["total"] = conn.execute(text("SELECT COUNT(*) FROM leads")).scalar() or 0
        return results


def get_hourly_reply_distribution() -> list:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT CAST(strftime('%H', received_at) AS INTEGER) AS hour, COUNT(*) AS count
                FROM replies
                GROUP BY hour
                ORDER BY hour
                """
            )
        ).fetchall()

        data_dict = {row[0]: row[1] for row in rows}
        return [{"hour": hour, "count": data_dict.get(hour, 0)} for hour in range(8, 23)]


def get_all_leads_with_status() -> list:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    l.id, l.name, l.email, l.phone, l.product_interest, l.product_viewed,
                    l.product_category, l.age, l.gender, l.state, l.ab_preference,
                    l.status, l.last_contact_date, l.notes, l.created_at,
                    r.content AS latest_reply,
                    r.classification,
                    r.llm_used AS reply_llm,
                    r.received_at AS reply_received_at,
                    m.content AS outreach_sent,
                    m.variant,
                    m.status AS message_status,
                    m.sent_at,
                    m.llm_used AS msg_llm
                FROM leads l
                LEFT JOIN replies r ON r.lead_id = l.id
                    AND r.id = (
                        SELECT MAX(id) FROM replies WHERE lead_id = l.id
                    )
                LEFT JOIN messages m ON m.lead_id = l.id
                    AND m.id = (
                        SELECT MAX(id) FROM messages WHERE lead_id = l.id
                    )
                ORDER BY
                    CASE l.status
                        WHEN 'pending' THEN 1
                        WHEN 'hot' THEN 2
                        WHEN 'warm' THEN 3
                        WHEN 'new' THEN 4
                        WHEN 'no_response' THEN 5
                        WHEN 'cold' THEN 6
                        WHEN 'email_failed' THEN 7
                        WHEN 'unsubscribed' THEN 8
                        ELSE 9
                    END,
                    l.id DESC
                """
            )
        ).fetchall()
        return [dict(row._mapping) for row in rows]


def get_tone_performance() -> dict:
    with engine.connect() as conn:
        result = {}
        for tone in ["professional", "friendly"]:
            sent = conn.execute(
                text("SELECT COUNT(*) FROM messages WHERE tone = :tone AND status = 'sent'"),
                {"tone": tone},
            ).scalar() or 0
            converted = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM replies r
                    JOIN messages m ON r.message_id = m.id
                    WHERE m.tone = :tone AND r.classification IN ('hot', 'warm')
                    """
                ),
                {"tone": tone},
            ).scalar() or 0
            result[tone] = _rate(converted, sent)
        return result


def _ab_breakdown(group_sql: str, order_by: str = "segment") -> list:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT
                    {group_sql} AS segment,
                    m.variant,
                    COUNT(DISTINCT m.id) AS sent,
                    COUNT(DISTINCT r.id) AS replied,
                    SUM(CASE WHEN r.classification IN ('hot', 'warm') THEN 1 ELSE 0 END) AS converted
                FROM messages m
                JOIN leads l ON l.id = m.lead_id
                LEFT JOIN replies r ON r.message_id = m.id
                WHERE m.status = 'sent' AND m.variant IN ('A', 'B')
                GROUP BY segment, m.variant
                ORDER BY {order_by}
                """
            )
        ).fetchall()

    grouped = defaultdict(lambda: {"A": {"sent": 0, "replied": 0, "converted": 0}, "B": {"sent": 0, "replied": 0, "converted": 0}})
    for row in rows:
        mapping = row._mapping
        segment = mapping["segment"] or "Unknown"
        variant = mapping["variant"]
        grouped[segment][variant] = {
            "sent": mapping["sent"] or 0,
            "replied": mapping["replied"] or 0,
            "converted": mapping["converted"] or 0,
        }

    output = []
    for segment, variants in grouped.items():
        a_rate = _rate(variants["A"]["converted"], variants["A"]["sent"])
        b_rate = _rate(variants["B"]["converted"], variants["B"]["sent"])
        output.append(
            {
                "segment": segment,
                "variant_a_rate": a_rate,
                "variant_b_rate": b_rate,
                "variant_a_sent": variants["A"]["sent"],
                "variant_b_sent": variants["B"]["sent"],
                "winner": "A" if a_rate >= b_rate else "B",
            }
        )
    return output


def get_ab_by_age_group() -> list:
    return _ab_breakdown(AGE_GROUP_SQL)


def get_ab_by_gender() -> list:
    return _ab_breakdown("COALESCE(NULLIF(l.gender, ''), 'Unknown')")


def get_ab_by_state() -> list:
    return _ab_breakdown("COALESCE(NULLIF(l.state, ''), 'Unknown')")


def get_ab_by_product_category() -> list:
    return _ab_breakdown("COALESCE(NULLIF(l.product_category, ''), 'Unknown')")


def get_demographic_analytics() -> dict:
    return {
        "status_counts": get_lead_status_counts(),
        "age_group": get_ab_by_age_group(),
        "gender": get_ab_by_gender(),
        "state": get_ab_by_state(),
        "product_category": get_ab_by_product_category(),
    }


def get_user_timeline(lead_id: int) -> dict | None:
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return None

        events = [
            {
                "event": "entered",
                "label": "Customer entered recovery system",
                "timestamp": _iso(lead.created_at),
                "status": "complete",
                "details": f"Viewed {lead.product_viewed or lead.product_interest}",
            }
        ]

        messages = db.query(Message).filter(Message.lead_id == lead.id).order_by(Message.id.asc()).all()
        replies = db.query(Reply).filter(Reply.lead_id == lead.id).order_by(Reply.id.asc()).all()
        replies_by_message = defaultdict(list)
        for reply in replies:
            replies_by_message[reply.message_id].append(reply)

        for message in messages:
            if message.status == "sent":
                events.append(
                    {
                        "event": "email_sent",
                        "label": f"Recovery email sent - Variant {message.variant}",
                        "timestamp": _iso(message.sent_at),
                        "status": "complete",
                        "details": f"{message.tone.title()} tone via {message.llm_used}",
                    }
                )
            elif message.status == "failed":
                events.append(
                    {
                        "event": "email_failed",
                        "label": f"Email failed - Variant {message.variant}",
                        "timestamp": _iso(message.sent_at),
                        "status": "failed",
                        "details": message.llm_used,
                    }
                )
            else:
                events.append(
                    {
                        "event": "message_generated",
                        "label": f"Variant {message.variant} generated",
                        "timestamp": _iso(message.sent_at),
                        "status": "pending",
                        "details": message.llm_used,
                    }
                )

            for reply in replies_by_message.get(message.id, []):
                events.append(
                    {
                        "event": "reply_received",
                        "label": f"Reply classified as {reply.classification}",
                        "timestamp": _iso(reply.received_at),
                        "status": reply.classification,
                        "details": reply.content,
                        "llm_used": reply.llm_used,
                    }
                )

        for reply in replies_by_message.get(None, []):
            events.append(
                {
                    "event": "reply_received",
                    "label": f"Reply classified as {reply.classification}",
                    "timestamp": _iso(reply.received_at),
                    "status": reply.classification,
                    "details": reply.content,
                    "llm_used": reply.llm_used,
                }
            )

        if lead.status == "pending" and not replies:
            events.append(
                {
                    "event": "waiting",
                    "label": "Waiting for customer reply",
                    "timestamp": None,
                    "status": "waiting",
                    "details": "No response received yet.",
                }
            )
        if lead.status == "no_response":
            events.append(
                {
                    "event": "no_response",
                    "label": "No response recorded",
                    "timestamp": None,
                    "status": "no_response",
                    "details": "This lowers the sent variant's future weighted score.",
                }
            )

        return {
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "age": lead.age,
                "gender": lead.gender,
                "state": lead.state,
                "product_viewed": lead.product_viewed or lead.product_interest,
                "product_category": lead.product_category,
                "status": lead.status,
                "ab_preference": lead.ab_preference,
            },
            "events": events,
        }
    finally:
        db.close()
