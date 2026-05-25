import re
from io import BytesIO, StringIO
from typing import Any

import pandas as pd

from backend.database import Lead, SessionLocal

EMAIL_RE = re.compile(r"[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}")
PHONE_CANDIDATE_RE = re.compile(r"(?:\+?\d[\d\s().-]{7,}\d)")

INDIAN_STATES = {
    "andhra pradesh",
    "arunachal pradesh",
    "assam",
    "bihar",
    "chhattisgarh",
    "goa",
    "gujarat",
    "haryana",
    "himachal pradesh",
    "jharkhand",
    "karnataka",
    "kerala",
    "madhya pradesh",
    "maharashtra",
    "manipur",
    "meghalaya",
    "mizoram",
    "nagaland",
    "odisha",
    "punjab",
    "rajasthan",
    "sikkim",
    "tamil nadu",
    "telangana",
    "tripura",
    "uttar pradesh",
    "uttarakhand",
    "west bengal",
    "delhi",
}

CATEGORY_KEYWORDS = {
    "electronics": [
        "airpods",
        "camera",
        "dell",
        "galaxy",
        "headphone",
        "iphone",
        "laptop",
        "macbook",
        "mobile",
        "phone",
        "samsung",
        "sony",
        "tablet",
        "tv",
        "wh-1000",
    ],
    "footwear": ["adidas", "air max", "footwear", "nike", "puma", "shoe", "sneaker", "ultraboost"],
    "fashion": ["dress", "fashion", "jeans", "kurta", "levis", "shirt", "t-shirt", "tshirt"],
    "accessories": ["bag", "belt", "fossil", "smartwatch", "sunglass", "watch"],
    "home_appliances": ["air fryer", "fridge", "mixer", "philips", "refrigerator", "washing machine"],
}

COLUMN_ALIASES = {
    "customer": "name",
    "customer_name": "name",
    "full_name": "name",
    "lead_name": "name",
    "email_address": "email",
    "email_id": "email",
    "mail": "email",
    "mobile": "phone",
    "mobile_no": "phone",
    "mobile_number": "phone",
    "number": "phone",
    "phone_no": "phone",
    "phone_number": "phone",
    "contact": "phone",
    "contact_number": "phone",
    "whatsapp": "phone",
    "whatsapp_number": "phone",
    "item": "product_viewed",
    "looking_at": "product_viewed",
    "product": "product_viewed",
    "product_interest": "product_viewed",
    "product_name": "product_viewed",
    "viewed": "product_viewed",
    "browsed": "product_viewed",
    "interested_in": "product_viewed",
    "category": "product_category",
    "type": "product_category",
    "browse_context": "notes",
    "cart_context": "notes",
    "comment": "notes",
    "comments": "notes",
    "context": "notes",
    "details": "notes",
}


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


def _canonical_key(key: Any) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")
    return COLUMN_ALIASES.get(cleaned, cleaned)


def _normalise_phone(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    match = PHONE_CANDIDATE_RE.search(text)
    candidate = match.group(0) if match else text
    digits = re.sub(r"\D", "", candidate)
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    if len(digits) >= 8:
        return f"+{digits}" if text.strip().startswith("+") else digits
    return ""


def _infer_category(*values: Any) -> str | None:
    text = " ".join(_clean(value).lower() for value in values if _clean(value))
    if not text:
        return None
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category
    return None


def _looks_like_gender(value: Any) -> bool:
    return _clean(value).lower() in {"male", "female", "other"}


def _looks_like_state(value: Any) -> bool:
    return _clean(value).lower() in INDIAN_STATES


def _looks_like_category(value: Any) -> bool:
    return _clean(value).lower() in CATEGORY_KEYWORDS


def _strip_contact_tokens(text: str) -> str:
    text = EMAIL_RE.sub(" ", text)
    text = PHONE_CANDIDATE_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip(" ,|;-")


def _extract_product_from_text(text: str) -> str:
    text = _strip_contact_tokens(text)
    text = re.sub(
        r"^(looking\s+at|looked\s+at|viewed|viewing|browsed|browsing|interested\s+in|wanted|wants|product|item|cart\s+for)\s+",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.split(
        r"\b(asked|asking|discount|price too high|already bought|compared|spent|viewed \d+|added to cart)\b",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return text.strip(" ,|;-")


def _normalise_row(row: dict) -> dict:
    canonical_row = {}
    for key, value in row.items():
        canonical_key = _canonical_key(key)
        if canonical_key not in canonical_row or not _clean(canonical_row[canonical_key]):
            canonical_row[canonical_key] = value

    product_viewed = (
        _clean(canonical_row.get("product_viewed"))
        or _clean(canonical_row.get("product_interest"))
        or _extract_product_from_text(_clean(canonical_row.get("notes")))
    )
    product_category = (
        _clean(canonical_row.get("product_category"))
        or _clean(canonical_row.get("category"))
        or _infer_category(product_viewed, canonical_row.get("notes"))
    )
    return {
        "name": _clean(canonical_row.get("name")),
        "email": _clean(canonical_row.get("email")).lower(),
        "phone": _normalise_phone(canonical_row.get("phone")) or None,
        "telegram_chat_id": _clean(canonical_row.get("telegram_chat_id")) or None,
        "age": _clean_int(canonical_row.get("age")),
        "gender": _clean(canonical_row.get("gender")).lower() or None,
        "state": _clean(canonical_row.get("state")) or None,
        "product_category": product_category or None,
        "product_viewed": product_viewed or None,
        "product_interest": product_viewed or _clean(canonical_row.get("product_interest")) or None,
        "last_contact_date": _clean(canonical_row.get("last_contact_date")) or None,
        "notes": _clean(canonical_row.get("notes")) or _clean(canonical_row.get("browse_context")) or None,
    }


def _parse_csv(file_bytes: bytes) -> list[dict]:
    df = pd.read_csv(BytesIO(file_bytes))
    recognised_columns = {_canonical_key(column) for column in df.columns}
    if not recognised_columns.intersection({"name", "email", "phone", "product_viewed", "product_category", "notes"}):
        headerless_df = pd.read_csv(BytesIO(file_bytes), header=None)
        text_lines = []
        for _, row in headerless_df.iterrows():
            parts = [_clean(value) for value in row.to_list() if _clean(value)]
            if parts:
                text_lines.append(", ".join(parts))
        return _parse_text("\n".join(text_lines).encode("utf-8"))

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
        phone_match = PHONE_CANDIDATE_RE.search(line)
        email = email_match.group(0).lower() if email_match else ""
        phone = _normalise_phone(phone_match.group(0)) if phone_match else ""
        contact_matches = [match for match in (email_match, phone_match) if match]
        first_contact = min(contact_matches, key=lambda match: match.start()) if contact_matches else None

        parts = [part.strip() for part in re.split(r"\s*(?:,|\||;|\t| - )\s*", line) if part.strip()]

        name = ""
        if first_contact:
            name = _strip_contact_tokens(line[: first_contact.start()])
        if not name and parts:
            name = _strip_contact_tokens(parts[0])

        age = None
        gender = ""
        state = ""
        product_category = ""
        product_candidates = []
        notes_candidates = []

        for part in parts:
            cleaned_part = _strip_contact_tokens(part)
            if not cleaned_part or cleaned_part == name:
                continue
            maybe_age = _clean_int(cleaned_part)
            if maybe_age and not age:
                age = maybe_age
                continue
            if _looks_like_gender(cleaned_part) and not gender:
                gender = cleaned_part.lower()
                continue
            if _looks_like_state(cleaned_part) and not state:
                state = cleaned_part
                continue
            if _looks_like_category(cleaned_part) and not product_category:
                product_category = cleaned_part.lower()
                continue
            if not product_candidates:
                product_candidates.append(cleaned_part)
            else:
                notes_candidates.append(cleaned_part)

        if first_contact:
            after_contact = line[first_contact.end() :]
            after_product = _extract_product_from_text(after_contact)
            if after_product and (
                not product_candidates
                or (name and product_candidates[0].lower().startswith(name.lower()))
            ):
                product_candidates.insert(0, after_product)

        product_viewed = product_candidates[0] if product_candidates else _extract_product_from_text(line)
        product_category = product_category or _infer_category(product_viewed, line) or ""
        notes = " | ".join(notes_candidates)

        rows.append(
            _normalise_row(
                {
                    "name": name,
                    "email": email,
                    "phone": phone,
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
    email_lead_ids = []
    phone_only = 0

    try:
        existing_emails = {row[0].lower() for row in db.query(Lead.email).all() if row[0]}
        existing_phones = {_normalise_phone(row[0]) for row in db.query(Lead.phone).all() if row[0]}

        for row in rows:
            email = row["email"]
            phone = _normalise_phone(row["phone"])
            if not row["name"] or not row["product_viewed"] or not (email or phone):
                skipped += 1
                continue
            if email and email in existing_emails:
                skipped += 1
                continue
            if not email and phone and phone in existing_phones:
                skipped += 1
                continue

            lead = Lead(
                name=row["name"],
                email=email or None,
                phone=phone or None,
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
            if email:
                existing_emails.add(email)
                email_lead_ids.append(lead.id)
            elif phone:
                existing_phones.add(phone)
                phone_only += 1
            lead_ids.append(lead.id)
            inserted += 1

        db.commit()
    finally:
        db.close()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "lead_ids": lead_ids,
        "email_lead_ids": email_lead_ids,
        "phone_only": phone_only,
    }


def parse_and_insert_csv(file_bytes: bytes) -> dict:
    return parse_and_insert_leads(file_bytes, "leads.csv")
