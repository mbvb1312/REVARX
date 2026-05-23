import json
import os
from typing import Any

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional fallback dependency
    genai = None
    types = None

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
SAMBANOVA_MODEL = os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.3-70B-Instruct")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

SYSTEM_PROMPT = (
    "You analyze e-commerce abandoned browse/cart sessions. "
    "Classify purchase intent and recommend the next recovery action. Return ONLY valid JSON."
)

USER_PROMPT_TEMPLATE = (
    "Analyze this customer recovery opportunity.\n\n"
    "- Name: {name}\n"
    "- Product viewed: {product_viewed}\n"
    "- Product category: {product_category}\n"
    "- Age: {age}\n"
    "- Gender: {gender}\n"
    "- State: {state}\n"
    "- Browse/cart notes: {notes}\n\n"
    "Return JSON:\n"
    "{{\n"
    "  \"lead_score\": \"hot|warm|cold\",\n"
    "  \"follow_up\": \"Short next step recommendation\"\n"
    "}}"
)


def _value(lead: Any, field: str, default: Any = "") -> Any:
    if isinstance(lead, dict):
        value = lead.get(field, default)
    else:
        value = getattr(lead, field, default)
    return default if value is None else value


def _context(lead: Any) -> dict:
    product_viewed = _value(lead, "product_viewed") or _value(lead, "product_interest") or "unknown product"
    return {
        "name": _value(lead, "name", ""),
        "product_viewed": product_viewed,
        "product_category": _value(lead, "product_category", "unknown"),
        "age": _value(lead, "age", "not provided"),
        "gender": _value(lead, "gender", "not provided"),
        "state": _value(lead, "state", "not provided"),
        "notes": _value(lead, "notes", ""),
    }


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"):
            text = text[4:].strip()

    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("No JSON object found")


def _normalize(parsed: dict) -> dict:
    lead_score = str(parsed.get("lead_score", "cold")).lower()
    if lead_score not in {"hot", "warm", "cold"}:
        lead_score = "cold"
    return {
        "lead_score": lead_score,
        "follow_up": str(parsed.get("follow_up", "Send a personalized recovery email.")),
    }


def _local_analyze(lead: Any) -> dict:
    notes = str(_value(lead, "notes", "")).lower()
    if any(term in notes for term in ["added to cart", "checkout", "viewed 3", "spent 12", "coupon"]):
        return {"lead_score": "hot", "follow_up": "Send the recovery email immediately with a direct return-to-cart CTA."}
    if any(term in notes for term in ["compared", "wishlist", "viewed"]):
        return {"lead_score": "warm", "follow_up": "Send a helpful comparison-style recovery email."}
    return {"lead_score": "cold", "follow_up": "Send a light reminder and avoid aggressive urgency."}


def analyze_lead(lead: Any) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(**_context(lead))

    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq

            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            return _normalize(_extract_json(response.choices[0].message.content))
        except Exception as exc:
            print(f"[lead_analyzer] Groq failed, trying SambaNova. Error: {exc}")

    if os.getenv("SAMBANOVA_API_KEY"):
        try:
            import requests

            response = requests.post(
                "https://api.sambanova.ai/v1/chat/completions",
                json={
                    "model": SAMBANOVA_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
                headers={
                    "Authorization": f"Bearer {os.getenv('SAMBANOVA_API_KEY')}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            response.raise_for_status()
            return _normalize(_extract_json(response.json()["choices"][0]["message"]["content"]))
        except Exception as exc:
            print(f"[lead_analyzer] SambaNova failed, trying Gemini. Error: {exc}")

    if os.getenv("GEMINI_API_KEY"):
        try:
            if not genai or not types:
                raise RuntimeError("google-genai is not installed")
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
                config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json"),
            )
            return _normalize(_extract_json(response.text))
        except Exception as exc:
            print(f"[lead_analyzer] Gemini failed, using local analyzer. Error: {exc}")

    return _local_analyze(lead)
