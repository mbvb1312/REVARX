# analytics/ — README for AI Coding Agents

## What This Folder Does
This folder contains all SQLite query logic that powers the dashboard.
Pure data-access functions. No AI, no UI, no sending.
Every function here returns a Python dict or list — no SQLAlchemy ORM objects.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `queries.py` | All analytics query functions used by the Streamlit dashboard and FastAPI endpoints |

---

## queries.py — Full Implementation Guide

```python
import os
from sqlalchemy import text
from backend.database import engine

def get_funnel_stats(campaign_id: int = None) -> dict:
    """
    Returns counts for the campaign funnel.
    If campaign_id is None, returns stats across all campaigns.
    
    Returns:
    {
        "sent": 38,
        "replied": 13,
        "hot": 5,
        "reply_rate": 34.2   ← (replied / sent) * 100, rounded to 1 decimal
    }
    """
    with engine.connect() as conn:
        # Count sent messages
        sent_query = "SELECT COUNT(*) FROM messages WHERE status='sent'"
        if campaign_id:
            sent_query += f" AND campaign_id={campaign_id}"
        sent = conn.execute(text(sent_query)).scalar()

        # Count replies
        replied_query = "SELECT COUNT(*) FROM replies"
        replied = conn.execute(text(replied_query)).scalar()

        # Count hot leads
        hot = conn.execute(text("SELECT COUNT(*) FROM leads WHERE status='hot'")).scalar()

        reply_rate = round((replied / sent * 100) if sent > 0 else 0, 1)
        
        return {"sent": sent, "replied": replied, "hot": hot, "reply_rate": reply_rate}


def get_ab_results(campaign_id: int = None) -> dict:
    """
    Compares reply rates for Variant A vs Variant B.
    
    Returns:
    {
        "variant_a_rate": 34.0,
        "variant_b_rate": 21.0,
        "winner": "A"
    }
    """
    with engine.connect() as conn:
        # Count variant A messages sent
        a_sent = conn.execute(text(
            "SELECT COUNT(*) FROM messages WHERE variant='A' AND status='sent'"
        )).scalar()
        
        # Count replies on variant A messages
        a_replied = conn.execute(text("""
            SELECT COUNT(*) FROM replies r
            JOIN messages m ON r.message_id = m.id
            WHERE m.variant = 'A'
        """)).scalar()
        
        # Same for variant B
        b_sent = conn.execute(text(
            "SELECT COUNT(*) FROM messages WHERE variant='B' AND status='sent'"
        )).scalar()
        b_replied = conn.execute(text("""
            SELECT COUNT(*) FROM replies r
            JOIN messages m ON r.message_id = m.id
            WHERE m.variant = 'B'
        """)).scalar()
        
        a_rate = round((a_replied / a_sent * 100) if a_sent > 0 else 0, 1)
        b_rate = round((b_replied / b_sent * 100) if b_sent > 0 else 0, 1)
        winner = "A" if a_rate >= b_rate else "B"
        
        return {"variant_a_rate": a_rate, "variant_b_rate": b_rate, "winner": winner}


def get_lead_status_counts() -> dict:
    """
    Returns count of leads by status.
    
    Returns:
    {
        "hot": 5,
        "warm": 4,
        "cold": 20,
        "unsubscribed": 5,
        "total": 50
    }
    """
    with engine.connect() as conn:
        results = {}
        for status in ["hot", "warm", "cold", "unsubscribed"]:
            count = conn.execute(text(
                f"SELECT COUNT(*) FROM leads WHERE status='{status}'"
            )).scalar()
            results[status] = count
        results["total"] = sum(results.values())
        return results


def get_hourly_reply_distribution() -> list:
    """
    Returns reply counts grouped by hour of day.
    Used for "best time to send" chart.
    
    Returns:
    [
        {"hour": 8, "count": 1},
        {"hour": 9, "count": 3},
        {"hour": 10, "count": 5},
        ...
        {"hour": 18, "count": 2}
    ]
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT CAST(strftime('%H', received_at) AS INTEGER) as hour, COUNT(*) as count
            FROM replies
            GROUP BY hour
            ORDER BY hour
        """)).fetchall()
        return [{"hour": row[0], "count": row[1]} for row in rows]


def get_all_leads_with_status() -> list:
    """
    Returns all leads with their current status and latest reply info.
    Used for the Lead Status Board page.
    
    Returns: list of dicts with keys:
        id, name, email, product_interest, status, last_contact_date,
        latest_reply (text or None), classification (or None)
    """
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT 
                l.id, l.name, l.email, l.product_interest, l.status, l.last_contact_date,
                r.content as latest_reply,
                r.classification
            FROM leads l
            LEFT JOIN replies r ON r.lead_id = l.id
                AND r.received_at = (
                    SELECT MAX(received_at) FROM replies WHERE lead_id = l.id
                )
            ORDER BY 
                CASE l.status WHEN 'hot' THEN 1 WHEN 'warm' THEN 2 WHEN 'cold' THEN 3 ELSE 4 END
        """)).fetchall()
        return [dict(row._mapping) for row in rows]


def get_tone_performance() -> dict:
    """
    Returns reply rate broken down by message tone.
    Used for "which tone works best" insight.
    
    Returns:
    {
        "friendly": 34.0,
        "professional": 22.0,
        "urgent": 18.0
    }
    """
    # Note: This requires storing 'tone' in the messages table.
    # Add a 'tone' column to the messages table if not already there.
    with engine.connect() as conn:
        result = {}
        for tone in ["friendly", "professional", "urgent"]:
            sent = conn.execute(text(
                f"SELECT COUNT(*) FROM messages WHERE tone='{tone}' AND status='sent'"
            )).scalar()
            replied = conn.execute(text(f"""
                SELECT COUNT(*) FROM replies r
                JOIN messages m ON r.message_id = m.id
                WHERE m.tone = '{tone}'
            """)).scalar()
            result[tone] = round((replied / sent * 100) if sent > 0 else 0, 1)
        return result
```

---

## FastAPI Endpoints That Use These Functions

These endpoints go in `main.py`:

```python
@app.get("/analytics/funnel")
def analytics_funnel():
    return get_funnel_stats()

@app.get("/analytics/ab")
def analytics_ab():
    return get_ab_results()

@app.get("/analytics/lead-counts")
def analytics_lead_counts():
    return get_lead_status_counts()

@app.get("/analytics/hourly")
def analytics_hourly():
    return get_hourly_reply_distribution()

@app.get("/analytics/tone")
def analytics_tone():
    return get_tone_performance()

@app.get("/leads")
def get_leads():
    return get_all_leads_with_status()
```

---

## Dependencies Used in This Folder
```
sqlalchemy==2.0.30
```

## What NOT to Do Here
- No Streamlit code
- No Gemini or Groq calls
- No direct `sqlite3` usage — use SQLAlchemy only
- All functions return plain Python dicts/lists (serializable to JSON)
- Never return SQLAlchemy row objects directly

---

## Demo Data Targets (what seed_data.py should produce)

When the dashboard runs against seed data, these are the numbers that should show:

| Metric | Target Value |
|---|---|
| Funnel: Sent | 38 |
| Funnel: Replied | 13 |
| Funnel: Hot | 5 |
| Reply Rate | ~34% |
| Variant A rate | ~34% |
| Variant B rate | ~21% |
| Peak reply hour | 10:00–12:00 |
| Best tone | friendly |

---

*See `AGENT_HANDOFF.md` for current task status.*
