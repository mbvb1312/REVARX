def build_telegram_link(bot_username: str, payload: str = "") -> str:
    """
    Builds a Telegram bot deep link with an optional start payload.
    """
    if not bot_username:
        return ""
    username = bot_username.lstrip("@")
    if payload:
        return f"https://t.me/{username}?start={payload}"
    return f"https://t.me/{username}"
