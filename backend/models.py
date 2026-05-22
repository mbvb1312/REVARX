from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LeadCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    product_interest: str
    last_contact_date: Optional[str] = None
    notes: Optional[str] = None


class Lead(LeadCreate):
    id: int
    status: str
    lead_score: str
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
