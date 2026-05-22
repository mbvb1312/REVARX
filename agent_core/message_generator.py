import json
import os

from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")
if _API_KEY:
    genai.configure(api_key=_API_KEY)

_model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = (
    "You are a skilled sales copywriter helping a business re-engage cold leads.\n"
    "Your messages must feel personal, warm, and human - never like a bulk email.\n"
    "You write in a conversational style appropriate to the given tone.\n"
    "Always return ONLY valid JSON, no markdown, no preamble, no code fences."
)

USER_PROMPT_TEMPLATE = (
    "Write a personalised reactivation message for this lead.\n\n"
    "Lead details:\n"
    "- Name: {name}\n"
    "- Product/service they showed interest in: {product_interest}\n"
    "- Last contact: {last_contact_date}\n"
    "- Context/notes: {notes}\n\n"
    "Tone: {tone}  (friendly | professional | urgent)\n"
    "Channel: {channel}  (telegram | email)\n\n"
    "Rules:\n"
    "- Keep it under 120 words\n"
    "- Reference their specific product interest naturally\n"
    "- Do NOT sound like a template or mass email\n"
    "- Include one clear, low-pressure call to action\n"
    "- If channel is email, also include a subject line\n\n"
    "Return JSON ONLY in this exact format:\n"
    "{\n"
    "  \"subject\": \"Subject line here (only for email, empty string for telegram)\",\n"
    "  \"message\": \"The full message body here\"\n"
    "}"
)


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("No JSON object found")


def generate_message(lead: dict, tone: str = "friendly", channel: str = "telegram") -> dict:
    """
    Generates a personalized reactivation message for a single lead.

    Returns a dict with keys: subject, message.
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        name=lead.get("name", ""),
        product_interest=lead.get("product_interest", ""),
        last_contact_date=lead.get("last_contact_date", "some time ago"),
        notes=lead.get("notes", ""),
        tone=tone,
        channel=channel,
    )

    try:
        response = _model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.8),
        )
        parsed = _extract_json(response.text)
        return {
            "subject": str(parsed.get("subject", "")),
            "message": str(parsed.get("message", "")),
        }
    except Exception as exc:
        lead_name = lead.get("name", "unknown")
        print(f"[message_generator] Error for lead {lead_name}: {exc}")
        return {"subject": "", "message": ""}
