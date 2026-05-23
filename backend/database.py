import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, TIMESTAMP, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

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
    phone = Column(String)
    telegram_chat_id = Column(String)
    product_interest = Column(String)
    last_contact_date = Column(String)
    notes = Column(Text)
    lead_score = Column(String, default="cold")
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
    variant = Column(String)
    content = Column(Text)
    channel = Column(String)
    tone = Column(String)
    status = Column(String, default="pending")
    sent_at = Column(TIMESTAMP)
    llm_used = Column(String, default="Google Gemini 2.0 Flash")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    content = Column(Text)
    is_voice_note = Column(Boolean, default=False)
    classification = Column(String)
    received_at = Column(TIMESTAMP, default=datetime.utcnow)
    llm_used = Column(String, default="Google Gemini 2.0 Flash")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
