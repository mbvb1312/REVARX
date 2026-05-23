import os
from fastapi import APIRouter, Request
from dotenv import load_dotenv

from backend.database import SessionLocal, Lead, Reply, Message, utc_now
from agent_core.reply_classifier import classify_reply
from channels.whisper_transcriber import transcribe_audio
from channels.telegram_sender import send_hot_lead_alert

load_dotenv()
router = APIRouter()

@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Receives all Telegram updates (messages sent TO the bot).
    Always returns 200 OK to Telegram to prevent retry loops.
    """
    try:
        data = await request.json()
        print(f"[telegram_webhook] Received webhook update: {data}")
        
        # Extract message from update
        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "")
        
        # Check for voice note
        voice = message.get("voice")
        is_voice = voice is not None
        
        if is_voice and voice:
            file_id = voice.get("file_id")
            try:
                audio_bytes = await download_telegram_file(file_id)
                text = transcribe_audio(audio_bytes, "voice.ogg")
                print(f"[telegram_webhook] Voice note transcribed successfully: '{text}'")
            except Exception as voice_err:
                print(f"[telegram_webhook] Voice note download or transcription failed: {voice_err}")
                text = ""

        if not text:
            # Ignore empty messages, stickers, documents, etc.
            return {"ok": True}

        if text.startswith("/start"):
            db = SessionLocal()
            try:
                payload = text.split(maxsplit=1)[1] if " " in text else ""
                lead_id = None
                if payload.startswith("lead-"):
                    try:
                        lead_id = int(payload.replace("lead-", ""))
                    except ValueError:
                        lead_id = None
                elif payload.isdigit():
                    lead_id = int(payload)

                if lead_id:
                    lead = db.query(Lead).filter(Lead.id == lead_id).first()
                    if lead:
                        lead.telegram_chat_id = chat_id
                        db.commit()
                        print(f"[telegram_webhook] Linked chat_id {chat_id} to lead {lead.id}.")
            finally:
                db.close()
            return {"ok": True}

        # database lookup and transition handling
        db = SessionLocal()
        try:
            lead = db.query(Lead).filter(Lead.telegram_chat_id == chat_id).first()
            if lead:
                # Find matching message_id (most recent outbound message)
                msg = db.query(Message).filter(
                    Message.lead_id == lead.id, 
                    Message.status == "sent"
                ).order_by(Message.id.desc()).first()
                msg_id = msg.id if msg else None

                # Classify the reply
                classification, classifier_llm = classify_reply(text)
                print(f"[telegram_webhook] Classified reply from {lead.name} as '{classification}' via {classifier_llm}")

                # Store reply in DB
                reply = Reply(
                    lead_id=lead.id,
                    message_id=msg_id,
                    content=text,
                    is_voice_note=is_voice,
                    classification=classification,
                    received_at=utc_now(),
                    llm_used=classifier_llm
                )
                db.add(reply)

                # State transition on lead
                lead.status = "unsubscribed" if classification == "unsubscribe" else classification
                db.commit()

                # Hot lead owner escalation
                if classification == "hot":
                    send_hot_lead_alert(lead.name, text)
            else:
                print(f"[telegram_webhook] Message received from chat_id {chat_id} but no matching lead found in DB.")
        finally:
            db.close()

    except Exception as e:
        print(f"[telegram_webhook] Error parsing Telegram update: {e}")

    return {"ok": True}  # Always return 200 to Telegram


async def download_telegram_file(file_id: str) -> bytes:
    """Downloads a file from Telegram servers and returns raw bytes."""
    import httpx
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not configured in environment variables.")
        
    async with httpx.AsyncClient() as client:
        # Get file path from Telegram api
        resp = await client.get(f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}")
        if not resp.is_success:
            raise Exception(f"Failed to get file path from Telegram API: {resp.text}")
        
        file_path = resp.json()["result"]["file_path"]
        
        # Download physical file bytes
        file_resp = await client.get(f"https://api.telegram.org/file/bot{token}/{file_path}")
        if not file_resp.is_success:
            raise Exception(f"Failed to download file bytes from Telegram server: {file_resp.text}")
            
        return file_resp.content
