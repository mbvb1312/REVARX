# REVARX AI

## Plain-English Summary

Every ecommerce business loses money when customers browse products, add items to cart, and then disappear. The intent is warm, but follow-up is usually manual, generic, and untracked.

REVARX AI turns those abandoned sessions into an automated recovery workflow:

1. A customer is added (single form or bulk upload).
2. The AI writes a personalized recovery message.
3. The system chooses the best A/B style (professional vs friendly).
4. The message is sent and tracked.
5. Replies are classified (hot, warm, cold, unsubscribe).
6. Analytics show which style converts for each segment.

This gives founders and evaluators a clear, end-to-end recovery loop: intent in, outreach out, learning back in.

## How the Demo Feels

- Add one customer and see an email sent instantly.
- Upload a CSV/TXT list and queue a bulk recovery campaign.
- Simulate replies to update lead status and A/B learning.
- Watch dashboards update by age group, gender, state, and product category.

Email is active now via Resend. WhatsApp and Telegram are modeled as user-initiated opt-in flows (deep links + bot start), which aligns with real-world consent requirements.

## Why It Matters (Evaluator Lens)

- Clear business pain: abandoned intent and lost revenue.
- AI used for personalization and classification, not just a chatbot.
- A/B learning is measurable and explainable by demographic slice.
- Demo is realistic and audit-friendly, with a mock mode and simulator.

## Technical Overview

### Architecture

- Frontend: Streamlit multi-page app for live demo, campaign control, analytics, and customer timeline.
- Backend: FastAPI for lead intake, A/B generation, email dispatch, and analytics APIs.
- Database: SQLite for leads, campaigns, messages, and replies.
- Scheduling: APScheduler for pending-message scan and send.

### AI Stack

- Primary: Groq
- Fallback: SambaNova
- Optional: Gemini
- Local templates and heuristics ensure the demo still works without keys.

### Channels

- Email: active via Resend (instant send after form submission).
- WhatsApp: user-initiated deep link (wa.me with prefilled message).
- Telegram: user-initiated bot start (deep link to bot).

### A/B Learning Logic

- Variant A: professional marketplace tone.
- Variant B: friendly casual tone.
- Weighted learning uses age group, gender, state, and product category.
- Hot/warm replies boost the winning style; unsubscribes penalize it.

## Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

Start the frontend:

```bash
streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```

## Environment Variables

```env
GROQ_API_KEY=your_groq_key
SAMBANOVA_API_KEY=your_sambanova_key
GEMINI_API_KEY=optional_gemini_key
RESEND_API_KEY=your_resend_key
FROM_EMAIL=your_verified_resend_sender
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_USERNAME=your_telegram_bot_username
WHATSAPP_BUSINESS_NUMBER=your_whatsapp_business_number
DATABASE_URL=sqlite:///./leads.db
```

For Resend test mode, emails may only be allowed to your verified/testing recipient. Verify a sender domain for broader live sends.

## CSV Columns

Recommended columns:

```text
name,email,age,gender,state,product_viewed,product_category,notes
```

TXT upload supports lines like:

```text
Priya Nair, priya@example.com, 28, female, Kerala, Nike Air Max 270, footwear, Viewed 3 times
Rahul Verma, rahul@example.com, Samsung Galaxy S24 Ultra, Added to cart
```

## Main Endpoints

- POST /leads: create one customer and send recovery email immediately.
- POST /upload-leads: upload CSV/TXT and queue recovery emails.
- GET /leads: live customer board data.
- GET /leads/{id}/timeline: per-customer journey.
- POST /simulate-reply: classify a reply and update A/B learning.
- POST /leads/{id}/mark-no-response: mark no response for learning.
- GET /analytics/demographics: demographic analytics.
- GET /analytics/ab-by-demographics: A/B winner by demographic slice.
