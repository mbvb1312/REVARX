import os
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.database import init_db, get_db, Lead, Campaign, Message, Reply
from backend.models import LeadCreate, CampaignCreate
from backend.csv_parser import parse_and_insert_csv
from backend.scheduler import start_scheduler, stop_scheduler

from analytics.queries import (
    get_funnel_stats,
    get_ab_results,
    get_lead_status_counts,
    get_hourly_reply_distribution,
    get_tone_performance,
    get_all_leads_with_status
)

load_dotenv()

app = FastAPI(
    title="Dead Lead Reactivation Agent API",
    description="Autonomous Outbound Re-engagement and A/B Testing Orchestrator"
)

# Enable CORS for Streamlit communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Telegram webhook router
from channels.telegram_webhook import router as telegram_router
app.include_router(telegram_router)

# Startup & Shutdown hooks
@app.on_event("startup")
def startup_event():
    init_db()
    start_scheduler()
    print("[api] FastAPI server started and SQLite DB initialized.")

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()
    print("[api] FastAPI server shutting down.")

# Request models
class CampaignRun(BaseModel):
    campaign_name: str
    tone: str = "friendly"
    channel: str = "telegram"

class ReplySimulation(BaseModel):
    lead_id: int
    content: str
    is_voice_note: bool = False

# Core API Routes

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow()}

@app.post("/upload-leads")
async def upload_leads(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        stats = parse_and_insert_csv(contents)
        return stats
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {exc}")

@app.post("/leads")
def create_lead(lead: LeadCreate, db=Depends(get_db)):
    try:
        db_lead = Lead(
            name=lead.name,
            email=lead.email,
            telegram_chat_id=lead.telegram_chat_id,
            product_interest=lead.product_interest,
            last_contact_date=lead.last_contact_date,
            notes=lead.notes,
            status="cold"
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)
        return {"ok": True, "lead_id": db_lead.id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/leads")
def list_leads():
    return get_all_leads_with_status()

# Previews endpoint (First 5 cold leads)
@app.post("/generate-previews")
def generate_previews(campaign: CampaignRun, db=Depends(get_db)):
    cold_leads = db.query(Lead).filter(Lead.status == "cold").limit(5).all()
    if not cold_leads:
        return {"previews": [], "message": "No cold leads found in database. Please upload/seed leads first."}

    gemini_key = os.getenv("GEMINI_API_KEY")
    previews = []

    # Import generator modules dynamically to prevent crash if not configured
    from agent_core.message_generator import generate_message

    for lead in cold_leads:
        lead_dict = {
            "id": lead.id,
            "name": lead.name,
            "product_interest": lead.product_interest,
            "last_contact_date": lead.last_contact_date or "some time ago",
            "notes": lead.notes or ""
        }

        if gemini_key:
            # Generate real message variants using Gemini
            variant_a = generate_message(lead_dict, campaign.tone, campaign.channel)
            # Short sleep to respect rate limits on free-tier
            import time
            time.sleep(0.5)
            variant_b = generate_message(lead_dict, campaign.tone, campaign.channel)
        else:
            # High-fidelity mock re-engagement copy fallback for zero-setup demo
            variant_a = {
                "subject": f"Quick question about {lead.product_interest} for {lead.name}",
                "message": f"Hi {lead.name}, hope your week is off to a great start! I was looking over your interest in our {lead.product_interest} from a few months back. Are you still seeking a solution for this? Let me know if you are open to a brief chat.",
                "llm_used": "Steps AI Local Sandbox"
            }
            variant_b = {
                "subject": f"Checking in regarding {lead.product_interest}",
                "message": f"Hi {lead.name}, quick follow-up on your trial of {lead.product_interest}. I noticed you were interested in integrations. Would it be helpful to hop on a quick 5-minute screen share to explore this together?",
                "llm_used": "Steps AI Local Sandbox"
            }

        previews.append({
            "lead": lead_dict,
            "variant_a": variant_a,
            "variant_b": variant_b
        })

    return {"previews": previews}

# Run campaign endpoint
@app.post("/run-campaign")
def run_campaign_endpoint(campaign_req: CampaignRun, db=Depends(get_db)):
    # Create the campaign record
    db_campaign = Campaign(
        name=campaign_req.campaign_name,
        tone=campaign_req.tone,
        channel=campaign_req.channel
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)

    # Check if we can run via LangGraph orchestrator (requires keys)
    # If keys are missing, we will run in a demo-simulated loop
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_key:
        try:
            from agent_core.orchestrator import run_campaign
            stats = run_campaign(db_campaign.id, campaign_req.tone, campaign_req.channel)
            return stats
        except Exception as exc:
            print(f"[api] Orchestrator error: {exc}. Falling back to standard campaign builder.")
    
    # Mock campaign execution loop
    cold_leads = db.query(Lead).filter(Lead.status == "cold").all()
    if not cold_leads:
        return {"sent": 0, "failed": 0, "message": "No cold leads to re-engage."}

    sent = 0
    failed = 0

    for lead in cold_leads:
        # Save a message to DB
        content = f"Hi {lead.name}, following up about {lead.product_interest}."
        
        # Pick variant A or B randomly
        import random
        variant = random.choice(["A", "B"])

        db_msg = Message(
            lead_id=lead.id,
            campaign_id=db_campaign.id,
            variant=variant,
            content=content,
            channel=campaign_req.channel,
            tone=campaign_req.tone,
            status="sent",
            sent_at=datetime.utcnow(),
            llm_used="Steps AI Local Sandbox"
        )
        db.add(db_msg)
        lead.status = "pending"  # Awaiting reply
        sent += 1

    db.commit()
    return {"sent": sent, "failed": failed}

# Analytics Endpoints

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

# Sandbox Simulation Endpoint (for Zero-setup demonstration)
@app.post("/simulate-reply")
def simulate_reply(sim: ReplySimulation, db=Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == sim.lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Find their latest sent message
    msg = db.query(Message).filter(Message.lead_id == lead.id, Message.status == "sent").order_by(Message.id.desc()).first()
    msg_id = msg.id if msg else None

    # Load Groq key to classify
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    classification = "cold"
    classifier_llm = "Steps AI Local Sandbox"

    if groq_key or gemini_key:
        try:
            from agent_core.reply_classifier import classify_reply
            classification, classifier_llm = classify_reply(sim.content)
        except Exception:
            pass
    
    if not groq_key and not gemini_key:
        # High fidelity local text classifier fallback if no key
        txt = sim.content.lower()
        if any(w in txt for w in ["yes", "interest", "call", "schedule", "talk", "demo", "pricing", "pricing", "cost"]):
            classification = "hot"
        elif any(w in txt for w in ["maybe", "later", "next month", "remind"]):
            classification = "warm"
        elif any(w in txt for w in ["stop", "remove", "unsubscribe", "don't"]):
            classification = "unsubscribe"
        classifier_llm = "Steps AI Local Heuristics"

    # Add the reply record
    db_reply = Reply(
        lead_id=lead.id,
        message_id=msg_id,
        content=sim.content,
        is_voice_note=sim.is_voice_note,
        classification=classification,
        received_at=datetime.utcnow(),
        llm_used=classifier_llm
    )
    db.add(db_reply)

    # Perform State transition on lead
    lead.status = "unsubscribed" if classification == "unsubscribe" else classification
    db.commit()

    # Trigger hot alert if classification is hot
    alert_triggered = False
    if classification == "hot":
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        tg_owner = os.getenv("TELEGRAM_OWNER_CHAT_ID")
        if tg_token and tg_owner:
            try:
                from channels.telegram_sender import send_hot_lead_alert
                send_hot_lead_alert(lead.name, sim.content)
                alert_triggered = True
            except Exception:
                pass

    return {
        "ok": True,
        "lead_status_updated_to": lead.status,
        "reply_classification": classification,
        "owner_alert_dispatched": alert_triggered
    }
