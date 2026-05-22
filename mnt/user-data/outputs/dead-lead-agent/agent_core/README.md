# agent_core/ — README for AI Coding Agents

## What This Folder Does
This folder contains ALL AI/LLM logic. This is the brain of the project.
- Message generation via Gemini
- A/B variant generation
- Reply classification via Groq
- LangGraph orchestration of the full agent loop

No database writes happen here except through imported DB functions.
No UI code here. No Telegram/email sending here — that's in `channels/`.

---

## Files in This Folder

| File | Purpose |
|---|---|
| `message_generator.py` | Calls Gemini 2.0 Flash to write a personalised reactivation message |
| `ab_tester.py` | Generates two variants (A and B) per lead using `message_generator` |
| `reply_classifier.py` | Calls Groq LLaMA to classify a reply text as hot/warm/cold/unsubscribe |
| `orchestrator.py` | LangGraph state machine that runs the full campaign pipeline |

---

## message_generator.py — Implementation Guide

```python
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """
You are a skilled sales copywriter helping a business re-engage cold leads.
Your messages must feel personal, warm, and human — never like a bulk email.
You write in a conversational style appropriate to the given tone.
Always return ONLY valid JSON, no markdown, no preamble, no code fences.
"""

USER_PROMPT_TEMPLATE = """
Write a personalised reactivation message for this lead.

Lead details:
- Name: {name}
- Product/service they showed interest in: {product_interest}
- Last contact: {last_contact_date}
- Context/notes: {notes}

Tone: {tone}  (friendly | professional | urgent)
Channel: {channel}  (telegram | email)

Rules:
- Keep it under 120 words
- Reference their specific product interest naturally
- Do NOT sound like a template or mass email
- Include one clear, low-pressure call to action
- If channel is email, also include a subject line

Return JSON ONLY in this exact format:
{{
  "subject": "Subject line here (only for email, empty string for telegram)",
  "message": "The full message body here"
}}
"""

def generate_message(lead: dict, tone: str = "friendly", channel: str = "telegram") -> dict:
    """
    Generates a personalised reactivation message for a single lead.
    
    Args:
        lead: dict with keys: name, product_interest, last_contact_date, notes
        tone: 'friendly' | 'professional' | 'urgent'
        channel: 'telegram' | 'email'
    
    Returns:
        dict with keys: subject (str), message (str)
        On failure: returns {"subject": "", "message": ""}
    """
    prompt = USER_PROMPT_TEMPLATE.format(
        name=lead.get("name", ""),
        product_interest=lead.get("product_interest", ""),
        last_contact_date=lead.get("last_contact_date", "some time ago"),
        notes=lead.get("notes", ""),
        tone=tone,
        channel=channel
    )
    
    try:
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\n\n{prompt}",
            generation_config=genai.types.GenerationConfig(temperature=0.8)
        )
        text = response.text.strip()
        # Strip any accidental markdown code fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"[message_generator] Error for lead {lead.get('name')}: {e}")
        return {"subject": "", "message": ""}
```

---

## ab_tester.py — Implementation Guide

```python
from agent_core.message_generator import generate_message
# Import DB session and Message model from backend

def generate_ab_variants(lead: dict, campaign_id: int, tone: str, channel: str, db) -> tuple:
    """
    Generates two message variants for a lead and stores them in DB.
    Returns (variant_a_dict, variant_b_dict)
    """
    variant_a = generate_message(lead, tone, channel)
    variant_b = generate_message(lead, tone, channel)  # Gemini varies naturally at temp=0.8
    
    # Store both in messages table with variant='A' and variant='B'
    # ... (DB insert logic here)
    
    return variant_a, variant_b
```

---

## reply_classifier.py — Implementation Guide

```python
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

CLASSIFIER_PROMPT = """
You are classifying a sales reply message into exactly one of these categories:
- hot: The person is clearly interested and wants to take action now
- warm: The person is somewhat interested but not ready yet (maybe later, send more info)
- cold: The person is not interested right now
- unsubscribe: The person explicitly wants to be removed / never contacted again

Reply ONLY with one word: hot, warm, cold, or unsubscribe.
No punctuation, no explanation.
"""

def classify_reply(reply_text: str) -> str:
    """
    Classifies a reply text.
    Returns one of: 'hot', 'warm', 'cold', 'unsubscribe'
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": CLASSIFIER_PROMPT},
                {"role": "user", "content": f"Reply to classify: {reply_text}"}
            ],
            max_tokens=5,
            temperature=0
        )
        result = response.choices[0].message.content.strip().lower()
        if result not in ["hot", "warm", "cold", "unsubscribe"]:
            return "cold"   # safe default
        return result
    except Exception as e:
        print(f"[reply_classifier] Error: {e}")
        return "cold"
```

**Test Cases — Must Pass:**
```python
assert classify_reply("Yes I'm very interested, let's schedule a call!") == "hot"
assert classify_reply("Maybe next quarter, remind me then") == "warm"
assert classify_reply("Not interested at this time") == "cold"
assert classify_reply("Please remove me from your list") == "unsubscribe"
assert classify_reply("Stop messaging me") == "unsubscribe"
```

---

## orchestrator.py — LangGraph Agent

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CampaignState(TypedDict):
    leads: List[dict]
    campaign_id: int
    tone: str
    channel: str
    generated_messages: List[dict]
    sent_count: int
    failed_count: int

def load_leads(state: CampaignState) -> CampaignState:
    # Fetch leads with status='cold' from DB
    # Update state['leads']
    pass

def generate_messages(state: CampaignState) -> CampaignState:
    # For each lead in state['leads'], call ab_tester.generate_ab_variants
    # Append to state['generated_messages']
    pass

def send_messages(state: CampaignState) -> CampaignState:
    # For each generated message, call the appropriate sender
    # telegram_sender if channel='telegram', email_sender if channel='email'
    # Update sent_count and failed_count
    pass

def update_status(state: CampaignState) -> CampaignState:
    # Mark all sent messages in DB with status='sent' and sent_at=now
    pass

# Build the graph
graph = StateGraph(CampaignState)
graph.add_node("load_leads", load_leads)
graph.add_node("generate_messages", generate_messages)
graph.add_node("send_messages", send_messages)
graph.add_node("update_status", update_status)

graph.set_entry_point("load_leads")
graph.add_edge("load_leads", "generate_messages")
graph.add_edge("generate_messages", "send_messages")
graph.add_edge("send_messages", "update_status")
graph.add_edge("update_status", END)

app = graph.compile()

def run_campaign(campaign_id: int, tone: str, channel: str) -> dict:
    """
    Run a full reactivation campaign.
    Returns summary dict with sent_count and failed_count.
    """
    result = app.invoke({
        "leads": [],
        "campaign_id": campaign_id,
        "tone": tone,
        "channel": channel,
        "generated_messages": [],
        "sent_count": 0,
        "failed_count": 0
    })
    return {"sent": result["sent_count"], "failed": result["failed_count"]}
```

---

## Dependencies Used in This Folder
```
google-generativeai==0.7.2
groq==0.9.0
langgraph==0.1.0
langchain-core==0.2.0
python-dotenv==1.0.0
```

## What NOT to Do Here
- Do NOT write Streamlit or UI code here
- Do NOT directly call Telegram API here — import from `channels/telegram_sender.py`
- Do NOT hardcode any API keys
- Do NOT use any paid API (OpenAI, Anthropic API) — use only Gemini and Groq

---

*See `AGENT_HANDOFF.md` for current task status.*
