import os

from dotenv import load_dotenv

load_dotenv()


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """
    Transcribes audio bytes using Groq Whisper.
    The Groq client is initialized lazily so missing keys do not break app startup.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("[whisper_transcriber] GROQ_API_KEY is not configured.")
        return ""

    try:
        from groq import Groq

        client = Groq(api_key=groq_key)
        transcription = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model="whisper-large-v3",
            response_format="text",
        )
        return str(transcription)
    except Exception as exc:
        print(f"[whisper_transcriber] Error: {exc}")
        return ""
