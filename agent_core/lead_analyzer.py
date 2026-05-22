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
    "You are a lead qualification assistant. "
    "Classify lead intent and recommend a next step. "
    "Return ONLY valid JSON."
)

USER_PROMPT_TEMPLATE = (
    "Analyze the following lead and respond with JSON only.\n\n"
    "Lead details:\n"
    "- Name: {name}\n"
    "- Product interest: {product_interest}\n"
    "- Last contact: {last_contact_date}\n"
    "- Notes: {notes}\n\n"
    "Return JSON in this format:\n"
    "{\n"
    "  \"lead_score\": \"hot|warm|cold\",\n"
    "  \"follow_up\": \"Short next step recommendation\"\n"
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


def analyze_lead(lead: dict) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(
        name=lead.get("name", ""),
        product_interest=lead.get("product_interest", ""),
        last_contact_date=lead.get("last_contact_date", "some time ago"),
        notes=lead.get("notes", ""),
    )

    try:
        response = _model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.2),
        )
        parsed = _extract_json(response.text)
        lead_score = str(parsed.get("lead_score", "cold")).lower()
        if lead_score not in {"hot", "warm", "cold"}:
            lead_score = "cold"
        return {
            "lead_score": lead_score,
            "follow_up": str(parsed.get("follow_up", "Send a gentle follow-up.")),
        }
    except Exception as exc:
        print(f"[lead_analyzer] Error: {exc}")
        return {"lead_score": "cold", "follow_up": "Send a gentle follow-up."}
