import random
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

from backend.database import SessionLocal, Lead, Message, utc_now
from agent_core.ab_tester import generate_ab_variants
from channels.telegram_sender import send_telegram
from channels.email_sender import send_email

class CampaignState(TypedDict):
    leads: List[dict]
    campaign_id: int
    tone: str
    channel: str
    sent_count: int
    failed_count: int

def load_leads(state: CampaignState) -> CampaignState:
    """
    Query database for unsent abandoned customers.
    """
    db = SessionLocal()
    try:
        cold_leads = db.query(Lead).filter(Lead.status.in_(["new", "cold", "email_failed"])).all()
        leads_list = []
        for lead in cold_leads:
            leads_list.append({
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "telegram_chat_id": lead.telegram_chat_id,
                "product_interest": lead.product_viewed or lead.product_interest,
                "product_viewed": lead.product_viewed or lead.product_interest,
                "product_category": lead.product_category,
                "age": lead.age,
                "gender": lead.gender,
                "state": lead.state,
                "last_contact_date": lead.last_contact_date or "some time ago",
                "notes": lead.notes or ""
            })
        state["leads"] = leads_list
    except Exception as exc:
        print(f"[orchestrator] load_leads node failed: {exc}")
    finally:
        db.close()
    return state

def generate_messages(state: CampaignState) -> CampaignState:
    """
    Loops through abandoned customers and generates professional/friendly variants.
    """
    db = SessionLocal()
    try:
        for lead in state["leads"]:
            # This generates Variant A and B, saving them in messages table as status='pending'
            generate_ab_variants(lead, state["campaign_id"], state["tone"], state["channel"], db)
    except Exception as exc:
        print(f"[orchestrator] generate_messages node failed: {exc}")
    finally:
        db.close()
    return state

def send_messages(state: CampaignState) -> CampaignState:
    """
    Loops through generated messages, chooses one variant to send, dispatches it, and updates DB status.
    """
    db = SessionLocal()
    sent_count = 0
    failed_count = 0
    try:
        for lead in state["leads"]:
            # Fetch the generated messages for this lead and campaign
            msgs = db.query(Message).filter(
                Message.lead_id == lead["id"],
                Message.campaign_id == state["campaign_id"],
                Message.status == "pending"
            ).all()

            if not msgs:
                continue

            # Randomly select one variant to send, and mark the other as "unused"
            chosen_msg = random.choice(msgs)
            for m in msgs:
                if m.id != chosen_msg.id:
                    m.status = "unused"

            success = False
            if state["channel"] == "telegram":
                if lead["telegram_chat_id"]:
                    success = send_telegram(lead["telegram_chat_id"], chosen_msg.content)
                else:
                    print(f"[orchestrator] Missing Telegram chat ID for lead {lead['name']}. Cannot send.")
            elif state["channel"] == "email":
                if lead["email"]:
                    success = send_email(lead["email"], f"Still interested in {lead['product_interest']}?", chosen_msg.content)
                else:
                    print(f"[orchestrator] Missing email for lead {lead['name']}. Cannot send.")

            if success:
                chosen_msg.status = "sent"
                chosen_msg.sent_at = utc_now()
                
                # Update lead status to "pending" (awaiting reply)
                db_lead = db.query(Lead).filter(Lead.id == lead["id"]).first()
                if db_lead:
                    db_lead.status = "pending"
                sent_count += 1
            else:
                chosen_msg.status = "failed"
                failed_count += 1
                
        db.commit()
    except Exception as exc:
        print(f"[orchestrator] send_messages node failed: {exc}")
    finally:
        db.close()

    state["sent_count"] = sent_count
    state["failed_count"] = failed_count
    return state

# Setup LangGraph workflow
workflow = StateGraph(CampaignState)

workflow.add_node("load_leads", load_leads)
workflow.add_node("generate_messages", generate_messages)
workflow.add_node("send_messages", send_messages)

workflow.set_entry_point("load_leads")
workflow.add_edge("load_leads", "generate_messages")
workflow.add_edge("generate_messages", "send_messages")
workflow.add_edge("send_messages", END)

# Compile graph
app_graph = workflow.compile()

def run_campaign(campaign_id: int, tone: str, channel: str) -> dict:
    """
    Public entrypoint to invoke the LangGraph Campaign StateGraph.
    """
    initial_state = {
        "leads": [],
        "campaign_id": campaign_id,
        "tone": tone,
        "channel": channel,
        "sent_count": 0,
        "failed_count": 0
    }
    result = app_graph.invoke(initial_state)
    return {
        "sent": result.get("sent_count", 0),
        "failed": result.get("failed_count", 0)
    }
