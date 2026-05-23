import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, TIMESTAMP, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leads.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    telegram_chat_id = Column(String)
    product_interest = Column(String)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    state = Column(String, nullable=True)
    product_category = Column(String, nullable=True)
    product_viewed = Column(String, nullable=True)
    ab_preference = Column(String, nullable=True)
    last_contact_date = Column(String)
    notes = Column(Text)
    lead_score = Column(String, default="cold")
    status = Column(String, default="new")
    created_at = Column(TIMESTAMP, default=utc_now)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    tone = Column(String, default="friendly")
    channel = Column(String, default="email")
    created_at = Column(TIMESTAMP, default=utc_now)


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
    opened_at = Column(TIMESTAMP, nullable=True)
    llm_used = Column(String, default="REVARX Local Template")


class Reply(Base):
    __tablename__ = "replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    content = Column(Text)
    is_voice_note = Column(Boolean, default=False)
    classification = Column(String)
    received_at = Column(TIMESTAMP, default=utc_now)
    llm_used = Column(String, default="REVARX Local Heuristics")


def _ensure_sqlite_columns() -> None:
    """Adds newly introduced columns when an existing SQLite DB is present."""
    if engine.dialect.name != "sqlite":
        return

    expected_columns = {
        "leads": {
            "age": "INTEGER",
            "gender": "VARCHAR",
            "state": "VARCHAR",
            "product_category": "VARCHAR",
            "product_viewed": "VARCHAR",
            "ab_preference": "VARCHAR",
        },
        "messages": {
            "opened_at": "TIMESTAMP",
        },
    }

    with engine.begin() as conn:
        for table_name, columns in expected_columns.items():
            existing = {
                row._mapping["name"]
                for row in conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
            }
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
