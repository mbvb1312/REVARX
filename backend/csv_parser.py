from io import BytesIO

import pandas as pd

from backend.database import Lead, SessionLocal

REQUIRED_COLUMNS = ["name", "email", "product_interest", "last_contact_date", "notes"]


def parse_and_insert_csv(file_bytes: bytes) -> dict:
    """
    Parses CSV bytes and inserts leads into the DB.
    Returns {"inserted": N, "skipped": M}.
    """
    df = pd.read_csv(BytesIO(file_bytes))

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    db = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        existing_emails = {row[0] for row in db.query(Lead.email).all() if row[0]}

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
                phone=str(row.get("phone", "")).strip() or None,
                telegram_chat_id=str(row.get("telegram_chat_id", "")).strip() or None,
                product_interest=str(row.get("product_interest", "")).strip(),
                last_contact_date=str(row.get("last_contact_date", "")).strip() or None,
                notes=str(row.get("notes", "")).strip() or None,
                status="cold",
            )
            db.add(lead)
            if email:
                existing_emails.add(email)
            inserted += 1

        db.commit()
    finally:
        db.close()

    return {"inserted": inserted, "skipped": skipped}
