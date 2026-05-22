import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CLASSIFIER_PROMPT = (
    "You are classifying a sales reply message into exactly one category: "
    "hot, warm, cold, unsubscribe. "
    "Reply with one word only."
)


def classify_reply(reply_text: str) -> str:
    """
    Classifies a reply into hot, warm, cold, or unsubscribe.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": f"Reply to classify: {reply_text}"},
            ],
            max_tokens=5,
            temperature=0,
        )
        result = response.choices[0].message.content.strip().lower()
        if result not in {"hot", "warm", "cold", "unsubscribe"}:
            return "cold"
        return result
    except Exception as exc:
        print(f"[reply_classifier] Error: {exc}")
        return "cold"
