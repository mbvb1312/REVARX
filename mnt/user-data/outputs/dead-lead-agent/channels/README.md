# channels/ — README for AI Coding Agents

## What This Folder Does
This folder handles ALL external communication — sending messages out and receiving replies in.
No AI/LLM logic here. No database schema here (only DB reads/writes for tracking).
No UI code here.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `telegram_sender.py` | Send a text message to a Telegram chat via Bot API |
| `telegram_webhook.py` | FastAPI router — receives incoming Telegram updates (replies) |
| `email_sender.py` | Send an email using SendGrid free tier |
| `whisper_transcriber.py` | Transcribe a voice note audio file using Groq Whisper |

---

## telegram_sender.py — Implementation Guide

```python
import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

async def send_telegram_async(chat_id: str, message: str) -> bool:
    """
    Sends a text message to a Telegram chat.
    Args:
        chat_id: Telegram chat ID (string, e.g. "123456789")
        message: plain text message body
    Returns:
        True on success, False on failure
    """
    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        return True
    except TelegramError as e:
        print(f"[telegram_sender] Failed for chat_id {chat_id}: {e}")
        return False

def send_telegram(chat_id: str, message: str) -> bool:
    """Synchronous wrapper for use in non-async contexts."""
    return asyncio.run(send_telegram_async(chat_id, message))


OWNER_CHAT_ID = os.getenv("TELEGRAM_OWNER_CHAT_ID")

def send_hot_lead_alert(lead_name: str, reply_text: str) -> bool:
    """
    Sends a hot lead escalation alert to the business owner.
    Always sends to TELEGRAM_OWNER_CHAT_ID.
    """
    alert = (
        f"🔥 *Hot Lead Alert!*\n\n"
        f"*Lead:* {lead_name}\n"
        f"*Their reply:* {reply_text}\n\n"
        f"Reply to them now while they're warm!"
    )
    return send_telegram(OWNER_CHAT_ID, alert)
```

**How to get a Telegram chat ID for a test lead:**
1. Start a conversation with your bot
2. Send any message
3. Check: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `message.chat.id` in the JSON response

---

## telegram_webhook.py — Implementation Guide

This is the most complex file. Read carefully.

```python
import os
from fastapi import APIRouter, Request
from dotenv import load_dotenv
# Import: db session, lead lookup, reply_classifier, send_hot_lead_alert, whisper_transcriber

load_dotenv()
router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Receives all Telegram updates (messages sent TO the bot).
    Telegram sends a POST request here for every message.
    
    Flow:
    1. Parse the incoming JSON update
    2. Extract chat_id, message text (or voice note)
    3. If voice note: download audio, call whisper_transcriber
    4. Find the lead in DB by telegram_chat_id
    5. Store reply in replies table
    6. Classify the reply text using reply_classifier
    7. Update lead status in DB (hot/warm/cold/unsubscribed)
    8. If hot: call send_hot_lead_alert
    9. Return {"ok": True} — ALWAYS return 200 OK to Telegram
    """
    try:
        data = await request.json()
        
        # Extract message from update
        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        
        # Check for voice note
        voice = message.get("voice")
        is_voice = voice is not None
        
        if is_voice and voice:
            # Download voice note and transcribe
            # file_id = voice["file_id"]
            # audio_bytes = await download_telegram_file(file_id)
            # text = whisper_transcriber.transcribe_audio(audio_bytes, "voice.ogg")
            pass
        
        if not text and not is_voice:
            return {"ok": True}  # Ignore non-text, non-voice messages
        
        # Look up lead by chat_id, classify, store, escalate
        # ... (DB logic here)
        
    except Exception as e:
        print(f"[telegram_webhook] Error: {e}")
    
    return {"ok": True}  # Always return 200 to avoid Telegram retries


async def download_telegram_file(file_id: str) -> bytes:
    """Downloads a file from Telegram servers and returns raw bytes."""
    import httpx
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    async with httpx.AsyncClient() as client:
        # Get file path
        resp = await client.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
        file_path = resp.json()["result"]["file_path"]
        # Download file
        file_resp = await client.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
        return file_resp.content
```

**Setting up the Telegram Webhook:**
```bash
# Using ngrok to expose localhost during development:
ngrok http 8000

# Set the webhook (replace <TOKEN> and <NGROK_URL>):
curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>/webhook"

# Verify it's set:
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## email_sender.py — Implementation Guide

```python
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Sends an email via SendGrid.
    Args:
        to_email: recipient email address
        subject: email subject line
        body: plain text email body
    Returns:
        True on success, False on failure
    """
    try:
        message = Mail(
            from_email=os.getenv("FROM_EMAIL"),
            to_emails=to_email,
            subject=subject,
            plain_text_content=body
        )
        sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        response = sg.send(message)
        return response.status_code in [200, 201, 202]
    except Exception as e:
        print(f"[email_sender] Failed to send to {to_email}: {e}")
        return False
```

**SendGrid Free Tier Limits:**
- 100 emails/day on free tier — more than enough for demo
- Must verify sender email address in SendGrid dashboard
- Emails may land in spam — tell demo audience to check spam

---

## whisper_transcriber.py — Implementation Guide

```python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """
    Transcribes voice note audio using Groq Whisper.
    Args:
        audio_bytes: raw audio bytes (ogg, mp3, wav, etc.)
        filename: filename with correct extension for format detection
    Returns:
        Transcribed text string, or empty string on failure
    """
    try:
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            response_format="text"
        )
        return transcription
    except Exception as e:
        print(f"[whisper_transcriber] Error: {e}")
        return ""
```

---

## Dependencies Used in This Folder
```
python-telegram-bot==21.3
sendgrid==6.11.0
groq==0.9.0
httpx==0.27.0
python-dotenv==1.0.0
fastapi==0.111.0
```

---

## What NOT to Do Here
- Do NOT generate messages here — that's `agent_core/message_generator.py`
- Do NOT classify replies here — that's `agent_core/reply_classifier.py`
- Do NOT write Streamlit code here
- ALWAYS return 200 OK to Telegram webhook even on errors (prevents infinite retries)

---

*See `AGENT_HANDOFF.md` for current task status.*
