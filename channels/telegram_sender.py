import asyncio
import os

from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = os.getenv("TELEGRAM_OWNER_CHAT_ID", "")

bot = Bot(token=BOT_TOKEN)


async def send_telegram_async(chat_id: str, message: str) -> bool:
    """
    Sends a text message to a Telegram chat.
    Returns True on success, False on failure.
    """
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return True
    except TelegramError as exc:
        print(f"[telegram_sender] Failed for chat_id {chat_id}: {exc}")
        return False


def send_telegram(chat_id: str, message: str) -> bool:
    """Synchronous wrapper for non-async contexts."""
    return asyncio.run(send_telegram_async(chat_id, message))


def send_hot_lead_alert(lead_name: str, reply_text: str) -> bool:
    """
    Sends a hot lead escalation alert to the business owner chat.
    """
    if not OWNER_CHAT_ID:
        return False

    alert = (
        "Hot Lead Alert\n\n"
        f"Lead: {lead_name}\n"
        f"Their reply: {reply_text}\n\n"
        "Reply now while they are warm."
    )
    return send_telegram(OWNER_CHAT_ID, alert)
