import re
from io import BytesIO, StringIO
from typing import Any

import pandas as pd

from backend.database import Lead, SessionLocal

EMAIL_RE = re.compile(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value).strip()


def _clean_int(value: Any) -> int | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _normalise_row(row: dict) -> dict:
    product_viewed = _clean(row.get("product_viewed")) or _clean(row.get("product_interest")) or _clean(row.get("product"))
    return {
        "name": _clean(row.get("name")),
        "email": _clean(row.get("email")).lower(),
        "phone": _clean(row.get("phone")) or None,
        "telegram_chat_id": _clean(row.get("telegram_chat_id")) or None,
        "age": _clean_int(row.get("age")),
        "gender": _clean(row.get("gender")).lower() or None,
        "state": _clean(row.get("state")) or None,
        "product_category": _clean(row.get("product_category")) or _clean(row.get("category")) or None,
        "product_viewed": product_viewed or None,
        "product_interest": product_viewed or _clean(row.get("product_interest")) or None,
        "last_contact_date": _clean(row.get("last_contact_date")) or None,
        "notes": _clean(row.get("notes")) or _clean(row.get("browse_context")) or None,
    }


def _parse_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(BytesIO(file_bytes))
    rows = []
    for _, row in df.iterrows():
        rows.append(_normalise_row(row.to_dict()))
    return rows


def _parse_text(file_bytes: bytes) -> list[dict]:
    text = file_bytes.decode("utf-8", errors="ignore")

    # If someone uploads CSV-like text as .txt, pandas can still handle it.
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    if "," in first_line and "email" in first_line.lower():
        df = pd.read_csv(StringIO(text))
        return [_normalise_row(row.to_dict()) for _, row in df.iterrows()]

    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        email_match = EMAIL_RE.search(line)
        email = email_match.group(0).lower() if email_match else ""
        parts = [part.strip() for part in re.split(r"[,|;]", line) if part.strip()]

        email_index = next((idx for idx, part in enumerate(parts) if EMAIL_RE.fullmatch(part)), None)
        if email_index is None and email:
            before_email = line[: email_match.start()].strip(" ,|;")
            after_email = line[email_match.end() :].strip(" ,|;")
            parts = [before_email, email] + [part.strip() for part in re.split(r"[,|;]", after_email) if part.strip()]
            email_index = 1

        name = parts[0] if parts else ""
        age = parts[email_index + 1] if email_index is not None and len(parts) > email_index + 1 else ""
        gender = parts[email_index + 2] if email_index is not None and len(parts) > email_index + 2 else ""
        state = parts[email_index + 3] if email_index is not None and len(parts) > email_index + 3 else ""
        product_viewed = parts[email_index + 4] if email_index is not None and len(parts) > email_index + 4 else ""
        product_category = parts[email_index + 5] if email_index is not None and len(parts) > email_index + 5 else ""
        notes = " | ".join(parts[email_index + 6 :]) if email_index is not None and len(parts) > email_index + 6 else ""

        # Also support a compact format: name, email, product, notes
        if not _clean_int(age):
            product_viewed = age or product_viewed
            age = ""
            gender = gender if gender.lower() in {"male", "female", "other"} else ""

        rows.append(
            _normalise_row(
                {
                    "name": name,
                    "email": email,
                    "age": age,
                    "gender": gender,
                    "state": state,
                    "product_viewed": product_viewed,
                    "product_category": product_category,
                    "notes": notes,
                }
            )
        )

    return rows


def parse_and_insert_leads(file_bytes: bytes, filename: str = "leads.csv") -> dict:
    """
    Parses CSV or TXT lead files and inserts abandoned customers.
    Returns inserted lead ids so the API can queue instant recovery emails.
    """
    filename = (filename or "").lower()
    rows = _parse_text(file_bytes) if filename.endswith(".txt") else _parse_csv(file_bytes)

    db = SessionLocal()
    inserted = 0
    skipped = 0
    lead_ids = []

    try:
        existing_emails = {row[0].lower() for row in db.query(Lead.email).all() if row[0]}

        for row in rows:
            if not row["name"] or not row["email"] or not row["product_viewed"]:
                skipped += 1
                continue
            if row["email"] in existing_emails:
                skipped += 1
                continue

            lead = Lead(
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
                telegram_chat_id=row["telegram_chat_id"],
                product_interest=row["product_interest"],
                age=row["age"],
                gender=row["gender"],
                state=row["state"],
                product_category=row["product_category"],
                product_viewed=row["product_viewed"],
                last_contact_date=row["last_contact_date"],
                notes=row["notes"],
                status="new",
            )
            db.add(lead)
            db.flush()
            existing_emails.add(row["email"])
            lead_ids.append(lead.id)
            inserted += 1

        db.commit()
    finally:
        db.close()

    return {"inserted": inserted, "skipped": skipped, "lead_ids": lead_ids}


def parse_and_insert_csv(file_bytes: bytes) -> dict:
    return parse_and_insert_leads(file_bytes, "leads.csv")
