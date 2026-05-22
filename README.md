# backend/ — README for AI Coding Agents

## What This Folder Does
This folder contains everything related to data storage, data models, CSV parsing, and task scheduling.
It has NO AI/LLM logic — that lives in `agent_core/`.
It has NO UI — that lives in `frontend/`.
It has NO messaging/channel code — that lives in `channels/`.

## Files in This Folder

| File | Purpose |
|---|---|
| `database.py` | SQLite connection, table creation, `get_db()` dependency |
| `models.py` | Pydantic data models (for FastAPI request/response validation) |
| `csv_parser.py` | Parse uploaded CSV files and insert into `leads` table |
| `scheduler.py` | APScheduler setup for time-based message sending |

---

## database.py — Exact Implementation Guide

```python
# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define all 4 ORM table classes here (Lead, Campaign, Message, Reply)
# See PROJECT_IDEA_README.md for exact schema

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## models.py — Pydantic Models

These are for FastAPI validation only. SQLAlchemy ORM classes go in `database.py`.

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

class Lead(LeadCreate):
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
    variant: str   # "A" or "B"
    content: str
    channel: str

class ReplyCreate(BaseModel):
    lead_id: int
    message_id: Optional[int] = None
    content: str
    is_voice_note: bool = False
    classification: Optional[str] = None
```

## csv_parser.py — Important Rules

- Required CSV columns: `name`, `email`, `product_interest`, `last_contact_date`, `notes`
- Optional: `telegram_chat_id`
- Use `pandas.read_csv()` to read the file
- Skip rows where `name` is empty
- On duplicate email: skip and log, do not raise an exception
- Return `{"inserted": N, "skipped": M}` dict

## scheduler.py — Important Rules

- Use `APScheduler` `BackgroundScheduler`
- Start scheduler in `main.py` on FastAPI startup event
- Job function `scan_and_send()` should be importable from this file
- Scheduler runs every 30 minutes and checks for messages with `status='pending'` and `scheduled_time <= now`
- For demo purposes: also expose a `send_now(message_id)` function that bypasses the schedule

---

## Dependencies Used in This Folder
```
sqlalchemy==2.0.30
pydantic==2.x (comes with fastapi)
pandas==2.2.2
apscheduler==3.10.4
python-dotenv==1.0.0
```

## What NOT to Do Here
- Do NOT make Gemini or Groq API calls in this folder
- Do NOT import from `channels/` in this folder
- Do NOT write Streamlit code here
- Do NOT store API keys — use `os.getenv()`

---

*See `AGENT_HANDOFF.md` for current task status.*
