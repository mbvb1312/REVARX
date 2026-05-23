import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()

scheduler = BackgroundScheduler()

def scan_and_send():
    """
    Scans for pending messages and sends them.
    Called automatically by APScheduler every 30 mins.
    """
    from backend.database import SessionLocal, Message, Lead, utc_now
    from channels.telegram_sender import send_telegram
    from channels.email_sender import send_email

    db = SessionLocal()
    try:
        pending = db.query(Message).filter(Message.status == "pending").all()
        for msg in pending:
            success = False
            lead = db.query(Lead).filter(Lead.id == msg.lead_id).first()
            
            if not lead:
                print(f"[scheduler] No lead found for message_id {msg.id}")
                msg.status = "failed"
                continue

            # Ensure we don't contact unsubscribed leads
            if lead.status == "unsubscribed":
                print(f"[scheduler] Skipping unsubscribed lead: {lead.name}")
                msg.status = "failed"
                continue

            if msg.channel == "telegram":
                if lead.telegram_chat_id:
                    success = send_telegram(lead.telegram_chat_id, msg.content)
                else:
                    print(f"[scheduler] Missing Telegram chat ID for lead: {lead.name}")
            elif msg.channel == "email":
                if lead.email:
                    subject = f"Still interested in {lead.product_viewed or lead.product_interest}?"
                    success = send_email(lead.email, subject, msg.content)
                else:
                    print(f"[scheduler] Missing email for lead: {lead.name}")

            msg.status = "sent" if success else "failed"
            msg.sent_at = utc_now()
        db.commit()
    except Exception as exc:
        print(f"[scheduler] Error in scan_and_send: {exc}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.get_job("scan_and_send"):
        scheduler.add_job(scan_and_send, "interval", minutes=30, id="scan_and_send")
    if not scheduler.running:
        scheduler.start()
        print("[scheduler] APScheduler started.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("[scheduler] APScheduler stopped.")
