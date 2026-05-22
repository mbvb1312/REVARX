from urllib.parse import quote


def build_whatsapp_link(message: str, business_number: str) -> str:
    """
    Builds a WhatsApp deep link with a prefilled message.
    """
    if not business_number:
        return ""
    encoded = quote(message or "")
    return f"https://wa.me/{business_number}?text={encoded}"
