import os
from sqlalchemy import text
from backend.database import engine

def get_funnel_stats(campaign_id: int = None) -> dict:
    """
    Returns counts for the campaign funnel.
    If campaign_id is None, returns stats across all campaigns.
    """
    with engine.connect() as conn:
        sent_query = "SELECT COUNT(*) FROM messages WHERE status='sent'"
        if campaign_id:
            sent_query += f" AND campaign_id={campaign_id}"
        sent = conn.execute(text(sent_query)).scalar() or 0

        if campaign_id:
            replied_query = f"""
                SELECT COUNT(*) FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE m.campaign_id = {campaign_id}
            """
        else:
            replied_query = "SELECT COUNT(*) FROM replies"
        replied = conn.execute(text(replied_query)).scalar() or 0

        hot = conn.execute(text("SELECT COUNT(*) FROM leads WHERE status='hot'")).scalar() or 0

        reply_rate = round((replied / sent * 100) if sent > 0 else 0, 1)
        
        return {"sent": sent, "replied": replied, "hot": hot, "reply_rate": reply_rate}


def get_ab_results(campaign_id: int = None) -> dict:
    """
    Compares reply rates for Variant A vs Variant B.
    """
    with engine.connect() as conn:
        a_sent_q = "SELECT COUNT(*) FROM messages WHERE variant='A' AND status='sent'"
        b_sent_q = "SELECT COUNT(*) FROM messages WHERE variant='B' AND status='sent'"
        
        a_replied_q = """
            SELECT COUNT(*) FROM replies r
            JOIN messages m ON r.message_id = m.id
            WHERE m.variant = 'A'
        """
        b_replied_q = """
            SELECT COUNT(*) FROM replies r
            JOIN messages m ON r.message_id = m.id
            WHERE m.variant = 'B'
        """
        
        if campaign_id:
            a_sent_q += f" AND campaign_id={campaign_id}"
            b_sent_q += f" AND campaign_id={campaign_id}"
            a_replied_q += f" AND m.campaign_id={campaign_id}"
            b_replied_q += f" AND m.campaign_id={campaign_id}"

        a_sent = conn.execute(text(a_sent_q)).scalar() or 0
        a_replied = conn.execute(text(a_replied_q)).scalar() or 0
        
        b_sent = conn.execute(text(b_sent_q)).scalar() or 0
        b_replied = conn.execute(text(b_replied_q)).scalar() or 0
        
        a_rate = round((a_replied / a_sent * 100) if a_sent > 0 else 0, 1)
        b_rate = round((b_replied / b_sent * 100) if b_sent > 0 else 0, 1)
        winner = "A" if a_rate >= b_rate else "B"
        
        return {"variant_a_rate": a_rate, "variant_b_rate": b_rate, "winner": winner}


def get_lead_status_counts() -> dict:
    """
    Returns count of leads by status.
    """
    with engine.connect() as conn:
        results = {}
        for status in ["hot", "warm", "cold", "unsubscribed"]:
            count = conn.execute(text(
                f"SELECT COUNT(*) FROM leads WHERE status='{status}'"
            )).scalar() or 0
            results[status] = count
        results["total"] = sum(results.values())
        return results


def get_hourly_reply_distribution() -> list:
    """
    Returns reply counts grouped by hour of day.
    Used for "best time to send" chart.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT CAST(strftime('%H', received_at) AS INTEGER) as hour, COUNT(*) as count
            FROM replies
            GROUP BY hour
            ORDER BY hour
        """)).fetchall()
        
        # Ensure we have hours 9 to 18 represented for a full dashboard bar chart
        data_dict = {row[0]: row[1] for row in rows}
        output = []
        for h in range(9, 19):
            output.append({"hour": h, "count": data_dict.get(h, 0)})
        return output


def get_all_leads_with_status() -> list:
    """
    Returns all leads with their current status and latest reply info.
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT 
                l.id, l.name, l.email, l.product_interest, l.status, l.last_contact_date, l.notes,
                r.content as latest_reply,
                r.classification,
                r.llm_used as reply_llm,
                m.content as outreach_sent,
                m.variant,
                m.llm_used as msg_llm
            FROM leads l
            LEFT JOIN replies r ON r.lead_id = l.id
                AND r.received_at = (
                    SELECT MAX(received_at) FROM replies WHERE lead_id = l.id
                )
            LEFT JOIN messages m ON m.lead_id = l.id
                AND m.status = 'sent'
                AND m.id = (
                    SELECT MAX(id) FROM messages WHERE lead_id = l.id AND status = 'sent'
                )
            ORDER BY 
                CASE l.status 
                    WHEN 'hot' THEN 1 
                    WHEN 'warm' THEN 2 
                    WHEN 'cold' THEN 3 
                    ELSE 4 
                END
        """)).fetchall()
        return [dict(row._mapping) for row in rows]


def get_tone_performance() -> dict:
    """
    Returns reply rate broken down by message tone.
    """
    with engine.connect() as conn:
        result = {}
        for tone in ["friendly", "professional", "urgent"]:
            sent = conn.execute(text(
                f"SELECT COUNT(*) FROM messages WHERE tone='{tone}' AND status='sent'"
            )).scalar() or 0
            replied = conn.execute(text(f"""
                SELECT COUNT(*) FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE m.tone = '{tone}'
            """)).scalar() or 0
            result[tone] = round((replied / sent * 100) if sent > 0 else 0, 1)
        return result
