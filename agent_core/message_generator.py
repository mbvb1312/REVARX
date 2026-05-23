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
    "You write e-commerce browse and cart abandonment recovery emails for small and medium businesses. "
    "Return ONLY valid JSON with subject and message. No markdown, no preamble."
)

PROFESSIONAL_PROMPT = (
    "Write Variant A: a professional, formal recovery email.\n\n"
    "Customer details:\n"
    "- Name: {name}\n"
    "- Product viewed: {product_viewed}\n"
    "- Product category: {product_category}\n"
    "- Age: {age}\n"
    "- Gender: {gender}\n"
    "- State: {state}\n"
    "- Browse/cart context: {notes}\n\n"
    "Rules:\n"
    "- Sound like a trusted e-commerce marketplace, not a pushy sales rep\n"
    "- Mention the exact product naturally\n"
    "- Keep the body under 120 words\n"
    "- Include one clear, low-pressure call to action\n"
    "- Do not invent specific discount amounts unless the context says so\n\n"
    "Return JSON only in this shape:\n"
    "{{\"subject\":\"...\",\"message\":\"...\"}}"
)

FRIENDLY_PROMPT = (
    "Write Variant B: a friendly, casual recovery email like a Swiggy or Zomato nudge.\n\n"
    "Customer details:\n"
    "- Name: {name}\n"
    "- Product viewed: {product_viewed}\n"
    "- Product category: {product_category}\n"
    "- Age: {age}\n"
    "- Gender: {gender}\n"
    "- State: {state}\n"
    "- Browse/cart context: {notes}\n\n"
    "Rules:\n"
    "- Fun, warm, and short\n"
    "- Mention the exact product naturally\n"
    "- Keep the body under 110 words\n"
    "- Include one clear, low-pressure call to action\n"
    "- Emojis are allowed only if they fit naturally\n\n"
    "Return JSON only in this shape:\n"
    "{{\"subject\":\"...\",\"message\":\"...\"}}"
)


def _lead_value(lead: Any, field: str, default: Any = "") -> Any:
    if isinstance(lead, dict):
        value = lead.get(field, default)
    else:
        value = getattr(lead, field, default)
    return default if value is None else value


def _lead_context(lead: Any) -> dict:
    product_viewed = (
        _lead_value(lead, "product_viewed")
        or _lead_value(lead, "product_interest")
        or "the product you were viewing"
    )
    return {
        "name": _lead_value(lead, "name", "there"),
        "product_viewed": product_viewed,
        "product_category": _lead_value(lead, "product_category", "shopping"),
        "age": _lead_value(lead, "age", "not provided"),
        "gender": _lead_value(lead, "gender", "not provided"),
        "state": _lead_value(lead, "state", "not provided"),
        "notes": _lead_value(lead, "notes", "Browsed recently and left without purchasing."),
    }


def _normalize_variant(variant: str) -> str:
    variant = (variant or "B").strip().upper()
    if variant in {"A", "PROFESSIONAL", "FORMAL"}:
        return "A"
    if variant in {"B", "FRIENDLY", "CASUAL"}:
        return "B"
    return "B"


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


def _build_prompt(lead: Any, variant: str, channel: str) -> str:
    context = _lead_context(lead)
    template = PROFESSIONAL_PROMPT if variant == "A" else FRIENDLY_PROMPT
    return f"Channel: {channel}\n\n{template.format(**context)}"


def _fallback_message(lead: Any, variant: str) -> dict:
    context = _lead_context(lead)
    name = context["name"]
    product = context["product_viewed"]

    if variant == "A":
        return {
            "subject": f"Still considering {product}?",
            "message": (
                f"Dear {name}, we noticed you were browsing {product}. "
                "If you are still comparing options, you can return to your selection and review "
                "current availability, delivery choices, and any active offers."
            ),
            "llm_used": "REVARX Local Template",
        }

    return {
        "subject": f"{product} is still waiting for you",
        "message": (
            f"Hey {name}, that {product} you were checking out is still here. "
            "Take one more look when you are ready. Your cart is only a click away."
        ),
        "llm_used": "REVARX Local Template",
    }


def _generate_with_groq(prompt: str, variant: str) -> dict:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.35 if variant == "A" else 0.8,
        response_format={"type": "json_object"},
    )
    parsed = _extract_json(response.choices[0].message.content)
    return {
        "subject": str(parsed.get("subject", "")),
        "message": str(parsed.get("message", "")),
        "llm_used": f"Groq {GROQ_MODEL}",
    }


def _generate_with_sambanova(prompt: str, variant: str) -> dict:
    import requests

    response = requests.post(
        "https://api.sambanova.ai/v1/chat/completions",
        json={
            "model": SAMBANOVA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.35 if variant == "A" else 0.8,
        },
        headers={
            "Authorization": f"Bearer {os.getenv('SAMBANOVA_API_KEY')}",
            "Content-Type": "application/json",
        },
        timeout=20,
    )
    response.raise_for_status()
    parsed = _extract_json(response.json()["choices"][0]["message"]["content"])
    return {
        "subject": str(parsed.get("subject", "")),
        "message": str(parsed.get("message", "")),
        "llm_used": f"SambaNova {SAMBANOVA_MODEL}",
    }


def _generate_with_gemini(prompt: str, variant: str) -> dict:
    if not genai or not types:
        raise RuntimeError("google-genai is not installed")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
        config=types.GenerateContentConfig(
            temperature=0.35 if variant == "A" else 0.8,
            response_mime_type="application/json",
        ),
    )
    parsed = _extract_json(response.text)
    return {
        "subject": str(parsed.get("subject", "")),
        "message": str(parsed.get("message", "")),
        "llm_used": f"Google {GEMINI_MODEL}",
    }


def generate_message(lead: Any, variant: str = "B", channel: str = "email") -> dict:
    """
    Generates a personalized e-commerce recovery message.
    Priority: Groq -> SambaNova -> Gemini -> local template.
    Variant A is professional/formal. Variant B is friendly/casual.
    """
    normalized_variant = _normalize_variant(variant)
    prompt = _build_prompt(lead, normalized_variant, channel)

    if os.getenv("GROQ_API_KEY"):
        try:
            return _generate_with_groq(prompt, normalized_variant)
        except Exception as exc:
            print(f"[message_generator] Groq failed, trying SambaNova. Error: {exc}")

    if os.getenv("SAMBANOVA_API_KEY"):
        try:
            return _generate_with_sambanova(prompt, normalized_variant)
        except Exception as exc:
            print(f"[message_generator] SambaNova failed, trying Gemini. Error: {exc}")

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _generate_with_gemini(prompt, normalized_variant)
        except Exception as exc:
            print(f"[message_generator] Gemini failed, using local template. Error: {exc}")

    return _fallback_message(lead, normalized_variant)
