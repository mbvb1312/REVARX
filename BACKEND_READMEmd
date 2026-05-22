# 📁 BACKEND_README.md
### REVARX — backend/ folder
 
---
 
## What This Folder Does
Data storage, data models, CSV parsing, and scheduling.
- NO AI/LLM logic (that is in `agent_core/`)
- NO UI code (that is in `frontend/`)
- NO messaging/channel code (that is in `channels/`)
---
 
## Files to Create Here
 
| File | Purpose |
|---|---|
| `database.py` | SQLite connection, table creation, `get_db()` dependency |
| `models.py` | Pydantic data models for FastAPI validation |
| `csv_parser.py` | Parse uploaded CSV, insert into `leads` table |
| `scheduler.py` | APScheduler for time-based message sending |
 
---
 
## database.py — Full Implementation
 
```python
import os
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Boolean, Text, TIMESTAMP, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv
 
load_dotenv()
 
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
 
 
class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String)
    telegram_chat_id = Column(String)
    product_interest = Column(String)
    last_contact_date = Column(String)
    notes = Column(Text)
    status = Column(String, default="cold")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
 
 
class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    tone = Column(String, default="friendly")
    channel = Column(String, default="telegram")
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
 
 
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    variant = Column(String)       # "A" or "B"
    content = Column(Text)
    channel = Column(String)
    tone = Column(String)
    status = Column(String, default="pending")
    sent_at = Column(TIMESTAMP)
 
 
class Reply(Base):
    __tablename__ = "replies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    content = Column(Text)
    is_voice_note = Column(Boolean, default=False)
    classification = Column(String)
    received_at = Column(TIMESTAMP, default=datetime.utcnow)
 
 
def init_db():
    Base.metadata.create_all(bind=engine)
 
 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
 
---
 
## models.py — Pydantic Models
 
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
 
 
class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    product_interest: str
    last_contact_date: Optional[str] = None
    notes: Optional[str] = None
 
 
class LeadOut(LeadCreate):
    id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
 
 
class CampaignCreate(BaseModel):
    name: str
    tone: str = "friendly"
    channel: str = "telegram"
 
 
class MessageCreate(BaseModel):
    lead_id: int
    campaign_id: int
    variant: str
    content: str
    channel: str
    tone: str
 
 
class ReplyCreate(BaseModel):
    lead_id: int
    message_id: Optional[int] = None
    content: str
    is_voice_note: bool = False
    classification: Optional[str] = None
```
 
---
 
## csv_parser.py — Implementation
 
```python
import pandas as pd
from io import BytesIO
from backend.database import SessionLocal
from backend.database import Lead
 
REQUIRED_COLUMNS = ["name", "email", "product_interest", "last_contact_date", "notes"]
 
 
def parse_and_insert_csv(file_bytes: bytes) -> dict:
    """
    Parses CSV bytes and inserts leads into DB.
    Returns {"inserted": N, "skipped": M}
    """
    df = pd.read_csv(BytesIO(file_bytes))
 
    # Validate columns
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
 
    db = SessionLocal()
    inserted = 0
    skipped = 0
 
    try:
        existing_emails = {r[0] for r in db.query(Lead.email).all()}
 
        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            email = str(row.get("email", "")).strip()
 
            if not name:
                skipped += 1
                continue
            if email and email in existing_emails:
                skipped += 1
                continue
 
            lead = Lead(
                name=name,
                email=email if email else None,
                telegram_chat_id=str(row.get("telegram_chat_id", "")).strip() or None,
                product_interest=str(row.get("product_interest", "")).strip(),
                last_contact_date=str(row.get("last_contact_date", "")).strip() or None,
                notes=str(row.get("notes", "")).strip() or None,
                status="cold"
            )
            db.add(lead)
            existing_emails.add(email)
            inserted += 1
 
        db.commit()
    finally:
        db.close()
 
    return {"inserted": inserted, "skipped": skipped}
```
 
---
 
## scheduler.py — Implementation
 
```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
 
scheduler = BackgroundScheduler()
 
 
def scan_and_send():
    """
    Scans for pending messages and sends them.
    Called automatically by APScheduler every 30 mins.
    Also checks if scheduled_time (if any) has passed.
    """
    from backend.database import SessionLocal
    from backend.database import Message
    from channels.telegram_sender import send_telegram
    from channels.email_sender import send_email
 
    db = SessionLocal()
    try:
        pending = db.query(Message).filter(Message.status == "pending").all()
        for msg in pending:
            success = False
            if msg.channel == "telegram":
                lead = msg.lead
                if lead and lead.telegram_chat_id:
                    success = send_telegram(lead.telegram_chat_id, msg.content)
            elif msg.channel == "email":
                lead = msg.lead
                if lead and lead.email:
                    success = send_email(lead.email, "Re-connecting", msg.content)
 
            msg.status = "sent" if success else "failed"
            msg.sent_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
 
 
def start_scheduler():
    scheduler.add_job(scan_and_send, "interval", minutes=30, id="scan_and_send")
    scheduler.start()
 
 
def stop_scheduler():
    scheduler.shutdown()
```
 
---
 
## Dependencies for This Folder
```
sqlalchemy==2.0.30
pydantic (included with fastapi)
pandas==2.2.2
apscheduler==3.10.4
python-dotenv==1.0.0
```
 
## Rules for Working in This Folder
- Do NOT call Gemini or Groq here
- Do NOT import from `channels/` here (scheduler is an exception — it imports to trigger sends)
- Do NOT write Streamlit code here
- Always use `os.getenv()` — never hardcode values
---
 
*See AGENT_HANDOFF.md for current task status before starting work.*