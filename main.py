import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_core.ab_tester import recommend_variant_for_lead
from agent_core.message_generator import generate_message
from analytics.queries import (
    get_ab_by_age_group,
    get_ab_by_gender,
    get_ab_by_product_category,
    get_ab_by_state,
    get_ab_results,
    get_all_leads_with_status,
    get_demographic_analytics,
    get_funnel_stats,
    get_hourly_reply_distribution,
    get_lead_status_counts,
    get_tone_performance,
    get_user_timeline,
)
from backend.csv_parser import parse_and_insert_leads
from backend.database import Campaign, Lead, Message, Reply, SessionLocal, get_db, init_db, utc_now
from backend.models import LeadCreate
from backend.scheduler import start_scheduler, stop_scheduler
from channels.email_sender import send_email
from channels.telegram_links import build_telegram_link
from channels.whatsapp_links import build_whatsapp_link

load_dotenv()

app = FastAPI(
    title="REVARX AI Recovery Agent API",
    description="E-commerce browse and cart abandonment recovery with live A/B learning.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from channels.telegram_webhook import router as telegram_router

app.include_router(telegram_router)


@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()
    print("[api] REVARX AI API started and database initialized.")


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()
    print("[api] REVARX AI API shutting down.")


class CampaignRun(BaseModel):
    campaign_name: str = "Live Recovery Campaign"
    tone: str = "ab-test"
    channel: str = "email"


class ReplySimulation(BaseModel):
    lead_id: int
    content: str
    is_voice_note: bool = False


def _create_campaign(db, name: str, channel: str = "email", tone: str = "ab-test") -> Campaign:
    campaign = Campaign(name=name, channel=channel, tone=tone)
    db.add(campaign)
    db.flush()
    return campaign


def _lead_to_generation_dict(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "age": lead.age,
        "gender": lead.gender,
        "state": lead.state,
        "product_category": lead.product_category,
        "product_viewed": lead.product_viewed or lead.product_interest,
        "product_interest": lead.product_interest,
        "last_contact_date": lead.last_contact_date,
        "notes": lead.notes,
    }


def send_recovery_email_for_lead(lead_id: int, campaign_id: Optional[int] = None) -> dict:
    """
    Generates the selected A/B variant, sends email, and persists tracking.
    Safe to call directly for single-customer tests or as a FastAPI background task.
    """
    db = SessionLocal()
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"ok": False, "error": "Lead not found", "lead_id": lead_id}

        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first() if campaign_id else None
        if not campaign:
            campaign = _create_campaign(db, "Instant Browse Recovery", channel="email")

        recommendation = recommend_variant_for_lead(lead, db)
        variant = recommendation["variant"]
        lead.ab_preference = variant

        generated = generate_message(_lead_to_generation_dict(lead), variant=variant, channel="email")
        message = Message(
            lead_id=lead.id,
            campaign_id=campaign.id,
            variant=variant,
            content=generated.get("message", ""),
            channel="email",
            tone="professional" if variant == "A" else "friendly",
            status="pending",
            llm_used=generated.get("llm_used", "REVARX Local Template"),
        )
        db.add(message)
        db.flush()

        email_sent = False
        if lead.email:
            subject = generated.get("subject") or f"Still interested in {lead.product_viewed or lead.product_interest}?"
            email_sent = send_email(lead.email, subject, generated.get("message", ""))

        message.status = "sent" if email_sent else "failed"
        message.sent_at = utc_now()
        lead.status = "pending" if email_sent else "email_failed"
        db.commit()

        return {
            "ok": True,
            "lead_id": lead.id,
            "variant_used": variant,
            "variant_label": "Professional" if variant == "A" else "Friendly",
            "selection_reason": recommendation["reason"],
            "email_sent": email_sent,
            "llm_used": message.llm_used,
            "message_id": message.id,
            "subject": generated.get("subject", ""),
        }
    except Exception as exc:
        db.rollback()
        print(f"[api] send_recovery_email_for_lead failed for lead {lead_id}: {exc}")
        return {"ok": False, "lead_id": lead_id, "error": str(exc)}
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc)}


@app.post("/upload-leads")
async def upload_leads(background_tasks: BackgroundTasks, file: UploadFile = File(...), db=Depends(get_db)):
    try:
        contents = await file.read()
        stats = parse_and_insert_leads(contents, file.filename or "leads.csv")

        campaign = _create_campaign(db, f"Bulk Recovery Upload - {file.filename}", channel="email")
        db.commit()

        email_lead_ids = stats.get("email_lead_ids", stats["lead_ids"])
        for lead_id in email_lead_ids:
            background_tasks.add_task(send_recovery_email_for_lead, lead_id, campaign.id)

        return {
            "inserted": stats["inserted"],
            "skipped": stats["skipped"],
            "customers_tracked": len(stats["lead_ids"]),
            "emails_queued": len(email_lead_ids),
            "phone_only": stats.get("phone_only", 0),
            "campaign_id": campaign.id,
            "message": "Customers imported. Recovery emails are queued for rows with email addresses; phone-only rows are tracked for future WhatsApp/Telegram follow-up.",
        }
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lead import failed: {exc}")


@app.post("/leads")
def create_lead(lead: LeadCreate, db=Depends(get_db)):
    product_viewed = lead.product_viewed or lead.product_interest
    if not product_viewed:
        raise HTTPException(status_code=400, detail="product_viewed or product_interest is required")

    try:
        db_lead = Lead(
            name=lead.name,
            email=lead.email,
            phone=lead.phone,
            telegram_chat_id=lead.telegram_chat_id,
            product_interest=product_viewed,
            age=lead.age,
            gender=lead.gender.lower() if lead.gender else None,
            state=lead.state,
            product_category=lead.product_category,
            product_viewed=product_viewed,
            last_contact_date=lead.last_contact_date,
            notes=lead.notes,
            status="new",
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    result = send_recovery_email_for_lead(db_lead.id)
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Recovery email failed"))
    whatsapp_message = f"Hi, I was looking at {product_viewed}. Can you share more details?"
    whatsapp_link = build_whatsapp_link(whatsapp_message, os.getenv("WHATSAPP_BUSINESS_NUMBER", ""))
    telegram_payload = f"lead-{db_lead.id}"
    telegram_link = build_telegram_link(os.getenv("TELEGRAM_BOT_USERNAME", ""), telegram_payload)

    return {
        **result,
        "whatsapp_link": whatsapp_link,
        "telegram_link": telegram_link,
        "telegram_payload": telegram_payload,
        "opt_in_note": "WhatsApp and Telegram require the user to click the link and start the chat.",
    }


@app.get("/leads")
def list_leads():
    return get_all_leads_with_status()


@app.get("/leads/{lead_id}/timeline")
def lead_timeline(lead_id: int):
    timeline = get_user_timeline(lead_id)
    if not timeline:
        raise HTTPException(status_code=404, detail="Lead not found")
    return timeline


@app.post("/generate-previews")
def generate_previews(campaign: CampaignRun, db=Depends(get_db)):
    leads = db.query(Lead).order_by(Lead.id.desc()).limit(5).all()
    if not leads:
        return {"previews": [], "message": "No customers found. Add or seed data first."}

    previews = []
    for lead in leads:
        lead_dict = _lead_to_generation_dict(lead)
        variant_a = generate_message(lead_dict, variant="A", channel="email")
        variant_b = generate_message(lead_dict, variant="B", channel="email")
        previews.append({"lead": lead_dict, "variant_a": variant_a, "variant_b": variant_b})

    return {"previews": previews}


@app.post("/run-campaign")
def run_campaign_endpoint(campaign_req: CampaignRun, background_tasks: BackgroundTasks, db=Depends(get_db)):
    campaign = _create_campaign(db, campaign_req.campaign_name, channel="email", tone="ab-test")
    leads = (
        db.query(Lead)
        .filter(Lead.status.in_(["new", "cold", "email_failed"]))
        .order_by(Lead.id.asc())
        .all()
    )
    db.commit()

    for lead in leads:
        background_tasks.add_task(send_recovery_email_for_lead, lead.id, campaign.id)

    return {
        "queued": len(leads),
        "campaign_id": campaign.id,
        "message": "Campaign queued in background to avoid request timeouts.",
    }


@app.post("/simulate-reply")
def simulate_reply(sim: ReplySimulation, db=Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == sim.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    msg = (
        db.query(Message)
        .filter(Message.lead_id == lead.id, Message.status == "sent")
        .order_by(Message.id.desc())
        .first()
    )
    msg_id = msg.id if msg else None

    try:
        from agent_core.reply_classifier import classify_reply

        classification, classifier_llm = classify_reply(sim.content)
    except Exception:
        classification, classifier_llm = "cold", "REVARX Local Heuristics"

    db_reply = Reply(
        lead_id=lead.id,
        message_id=msg_id,
        content=sim.content,
        is_voice_note=sim.is_voice_note,
        classification=classification,
        received_at=utc_now(),
        llm_used=classifier_llm,
    )
    db.add(db_reply)

    lead.status = "unsubscribed" if classification == "unsubscribe" else classification
    db.commit()

    return {
        "ok": True,
        "lead_status_updated_to": lead.status,
        "reply_classification": classification,
        "classifier_llm_used": classifier_llm,
        "ab_learning_note": "This reply now feeds the future A/B recommendation weights.",
    }


@app.post("/leads/{lead_id}/mark-no-response")
def mark_no_response(lead_id: int, db=Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = "no_response"
    db.commit()
    return {"ok": True, "lead_id": lead_id, "status": lead.status}


@app.get("/analytics/funnel")
def analytics_funnel(campaign_id: Optional[int] = None):
    return get_funnel_stats(campaign_id)


@app.get("/analytics/ab")
def analytics_ab(campaign_id: Optional[int] = None):
    return get_ab_results(campaign_id)


@app.get("/analytics/lead-counts")
def analytics_lead_counts():
    return get_lead_status_counts()


@app.get("/analytics/hourly")
def analytics_hourly():
    return get_hourly_reply_distribution()


@app.get("/analytics/tone")
def analytics_tone():
    return get_tone_performance()


@app.get("/analytics/demographics")
def analytics_demographics():
    return get_demographic_analytics()


@app.get("/analytics/ab-by-demographics")
def analytics_ab_by_demographics():
    return {
        "age_group": get_ab_by_age_group(),
        "gender": get_ab_by_gender(),
        "state": get_ab_by_state(),
        "product_category": get_ab_by_product_category(),
    }
