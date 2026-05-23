import os

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

VALID_CLASSES = {"hot", "warm", "cold", "unsubscribe"}

CLASSIFIER_PROMPT = (
    "Classify this e-commerce abandoned-cart recovery reply into exactly one category:\n"
    "- hot: wants to buy, asks for discount/coupon/availability/payment/delivery, or asks to proceed\n"
    "- warm: interested but delayed, asks to check later, needs more information\n"
    "- cold: not interested, bought elsewhere, price too high without intent to continue\n"
    "- unsubscribe: asks to stop, remove, unsubscribe, or never contact again\n\n"
    "Reply with one word only: hot, warm, cold, or unsubscribe."
)


def _clean_label(text: str) -> str:
    label = (text or "").strip().lower().replace(".", "").replace('"', "").replace("'", "")
    if label in VALID_CLASSES:
        return label
    for candidate in VALID_CLASSES:
        if candidate in label:
            return candidate
    return ""


def _classify_with_groq(reply_text: str) -> tuple[str, str]:
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": f"Reply to classify: {reply_text}"},
        ],
        max_tokens=5,
        temperature=0,
    )
    result = _clean_label(response.choices[0].message.content)
    if result:
        return result, f"Groq {GROQ_MODEL}"
    raise ValueError("Groq returned an unknown class")


def _classify_with_sambanova(reply_text: str) -> tuple[str, str]:
    import requests

    response = requests.post(
        "https://api.sambanova.ai/v1/chat/completions",
        json={
            "model": SAMBANOVA_MODEL,
            "messages": [
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": f"Reply to classify: {reply_text}"},
            ],
            "max_tokens": 5,
            "temperature": 0,
        },
        headers={
            "Authorization": f"Bearer {os.getenv('SAMBANOVA_API_KEY')}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    response.raise_for_status()
    result = _clean_label(response.json()["choices"][0]["message"]["content"])
    if result:
        return result, f"SambaNova {SAMBANOVA_MODEL}"
    raise ValueError("SambaNova returned an unknown class")


def _classify_with_gemini(reply_text: str) -> tuple[str, str]:
    if not genai or not types:
        raise RuntimeError("google-genai is not installed")

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{CLASSIFIER_PROMPT}\n\nReply to classify: {reply_text}",
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=5),
    )
    result = _clean_label(response.text)
    if result:
        return result, f"Google {GEMINI_MODEL}"
    raise ValueError("Gemini returned an unknown class")


def _classify_locally(reply_text: str) -> tuple[str, str]:
    txt = (reply_text or "").lower()
    if any(word in txt for word in ["unsubscribe", "stop", "remove me", "do not contact", "don't contact", "never email"]):
        return "unsubscribe", "REVARX Local Heuristics"
    if any(word in txt for word in ["yes", "buy", "purchase", "coupon", "discount", "available", "delivery", "payment", "checkout", "proceed", "send link"]):
        return "hot", "REVARX Local Heuristics"
    if any(word in txt for word in ["later", "maybe", "next week", "next month", "remind", "more info", "details", "thinking"]):
        return "warm", "REVARX Local Heuristics"
    if any(word in txt for word in ["bought", "amazon", "flipkart", "too high", "expensive", "not interested", "no thanks", "different"]):
        return "cold", "REVARX Local Heuristics"
    return "cold", "REVARX Local Heuristics"


def classify_reply(reply_text: str) -> tuple[str, str]:
    """
    Classifies a customer reply.
    Priority: Groq -> SambaNova -> Gemini -> local heuristics.
    """
    if os.getenv("GROQ_API_KEY"):
        try:
            return _classify_with_groq(reply_text)
        except Exception as exc:
            print(f"[reply_classifier] Groq failed, trying SambaNova. Error: {exc}")

    if os.getenv("SAMBANOVA_API_KEY"):
        try:
            return _classify_with_sambanova(reply_text)
        except Exception as exc:
            print(f"[reply_classifier] SambaNova failed, trying Gemini. Error: {exc}")

    if os.getenv("GEMINI_API_KEY"):
        try:
            return _classify_with_gemini(reply_text)
        except Exception as exc:
            print(f"[reply_classifier] Gemini failed, using local heuristics. Error: {exc}")

    return _classify_locally(reply_text)
