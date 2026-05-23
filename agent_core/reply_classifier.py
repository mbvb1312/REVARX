import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Initialize Gemini
_gemini_key = os.getenv("GEMINI_API_KEY")
if _gemini_key:
    genai.configure(api_key=_gemini_key)

_model = genai.GenerativeModel("gemini-2.0-flash")

CLASSIFIER_PROMPT = (
    "You are classifying a sales reply message into exactly one category: "
    "hot, warm, cold, unsubscribe.\n"
    "Reply with one word only (hot, warm, cold, unsubscribe)."
)


def classify_reply(reply_text: str) -> tuple[str, str]:
    """
    Classifies a reply text into one of: 'hot', 'warm', 'cold', 'unsubscribe'.
    Returns (classification_string, llm_used_string).
    
    First priority: Gemini 2.0 Flash.
    Backup: Groq LLaMA-3.1 8B.
    Local Fallback: Rule-based keyword checks.
    """
    # 1st Priority: Gemini
    if _gemini_key:
        try:
            response = _model.generate_content(
                f"{CLASSIFIER_PROMPT}\n\nReply to classify: {reply_text}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=5
                )
            )
            result = response.text.strip().lower().replace(".", "").replace('"', '').replace("'", "")
            if result in {"hot", "warm", "cold", "unsubscribe"}:
                return result, "Google Gemini 2.0 Flash"
        except Exception as gemini_exc:
            print(f"[reply_classifier] Gemini classification failed, trying Groq. Error: {gemini_exc}")

    # 2nd Priority / Backup: Groq LLaMA
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": f"Reply to classify: {reply_text}"},
                ],
                max_tokens=5,
                temperature=0,
            )
            result = response.choices[0].message.content.strip().lower().replace(".", "").replace('"', '').replace("'", "")
            if result in {"hot", "warm", "cold", "unsubscribe"}:
                return result, "Groq LLaMA-3.1 8B"
        except Exception as groq_exc:
            print(f"[reply_classifier] Groq classification failed: {groq_exc}")

    # Local Heuristics Fallback (guarantees uptime even under zero internet or api outages)
    txt = reply_text.lower()
    if any(w in txt for w in ["yes", "interest", "call", "schedule", "talk", "demo", "pricing", "pricing", "cost"]):
        return "hot", "Steps AI Local Heuristics"
    elif any(w in txt for w in ["maybe", "later", "next month", "remind"]):
        return "warm", "Steps AI Local Heuristics"
    elif any(w in txt for w in ["stop", "remove", "unsubscribe", "don't"]):
        return "unsubscribe", "Steps AI Local Heuristics"

    return "cold", "Steps AI Local Heuristics"
