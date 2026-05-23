import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Initialize Gemini
_gemini_key = os.getenv("GEMINI_API_KEY")
if _gemini_key:
    genai.configure(api_key=_gemini_key)

_model = genai.GenerativeModel("gemini-1.5-flash")

CLASSIFIER_PROMPT = (
    "You are classifying a sales reply message into exactly one category: "
    "hot, warm, cold, unsubscribe.\n"
    "Reply with one word only (hot, warm, cold, unsubscribe)."
)


def classify_reply(reply_text: str) -> tuple[str, str]:
    """
    Classifies a reply text into one of: 'hot', 'warm', 'cold', 'unsubscribe'.
    Returns (classification_string, llm_used_string).
    
    1st priority: Gemini 1.5 Flash.
    2nd priority: Groq LLaMA-3.1 8B.
    3rd priority: SambaNova LLaMA 3.1 405B.
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
                return result, "Google Gemini 1.5 Flash"
        except Exception as gemini_exc:
            print(f"[reply_classifier] Gemini 1.5 Flash classification failed, trying Groq. Error: {gemini_exc}")

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
            print(f"[reply_classifier] Groq classification failed, trying SambaNova. Error: {groq_exc}")

    # 3rd Priority / Backup: SambaNova LLaMA 3.1 405B (smartest open-source model)
    sambanova_key = os.getenv("SAMBANOVA_API_KEY")
    if sambanova_key:
        try:
            import requests
            url = "https://api.sambanova.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {sambanova_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "Meta-Llama-3.1-405B-Instruct",
                "messages": [
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": f"Reply to classify: {reply_text}"}
                ],
                "max_tokens": 5,
                "temperature": 0
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.ok:
                result = resp.json()["choices"][0]["message"]["content"].strip().lower().replace(".", "").replace('"', '').replace("'", "")
                if result in {"hot", "warm", "cold", "unsubscribe"}:
                    return result, "SambaNova LLaMA 3.1 405B"
        except Exception as samba_exc:
            print(f"[reply_classifier] SambaNova classification failed: {samba_exc}")

    # Local Heuristics Fallback (guarantees uptime even under zero internet or api outages)
    txt = reply_text.lower()
    if any(w in txt for w in ["yes", "interest", "call", "schedule", "talk", "demo", "pricing", "pricing", "cost"]):
        return "hot", "Steps AI Local Heuristics"
    elif any(w in txt for w in ["maybe", "later", "next month", "remind"]):
        return "warm", "Steps AI Local Heuristics"
    elif any(w in txt for w in ["stop", "remove", "unsubscribe", "don't"]):
        return "unsubscribe", "Steps AI Local Heuristics"

    return "cold", "Steps AI Local Heuristics"
