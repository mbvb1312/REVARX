# AGENT HANDOFF

## Current Product

REVARX AI is now an e-commerce browse and cart abandonment recovery agent.

It is not a generic cold sales lead system anymore.

## Current Status

Completed overhaul:

- Backend schema supports abandoned customer demographics.
- Single customer creation sends recovery email immediately.
- CSV and TXT upload queue background recovery emails.
- A/B testing is professional vs friendly.
- A/B selection uses weighted historical conversion by age group, gender, state, and product category.
- LLM priority is Groq, then SambaNova, then optional Gemini, then local fallback.
- Analytics include demographic A/B breakdowns.
- Live customer board includes status, reply classification, timeline, and no-response marking.
- Seed data is now e-commerce focused with Indian names, all 28 states, product categories, browse notes, and realistic replies.

## Important Runtime Notes

- FastAPI backend: `uvicorn main:app --reload --port 8000`
- Streamlit frontend: `streamlit run frontend/app.py`
- Demo URL: `http://localhost:8501`
- Default DB: `leads.db`
- Existing DB was backed up before reseeding as `leads.pre-revarx-*.db`

## Live Demo Flow

1. Open the Streamlit app.
2. Use "Live Demo: Add Customers".
3. Add a single customer with email, age, gender, state, product viewed, and category.
4. Confirm API returns variant, LLM used, and email send status.
5. Use "Live Customer Board" to inspect the timeline.
6. Use homepage or board reply simulator to classify a reply.
7. Use "Analytics" to show A/B learning by demographic slice.

## Environment Variables

```env
GROQ_API_KEY=
SAMBANOVA_API_KEY=
GEMINI_API_KEY=
RESEND_API_KEY=
FROM_EMAIL=
DATABASE_URL=sqlite:///./leads.db
```

## Known Constraints

- Resend test mode may only send to verified/test addresses unless a sender domain is verified.
- WhatsApp and Telegram outbound are intentionally future scope for this version.
- Local fallback keeps demos working without API keys but will not actually send email without Resend.

## Verification Already Run

- `python -m compileall files`
- `venv\Scripts\python.exe -m pip install -r requirements.txt`
- Temp DB seed and analytics smoke test
- FastAPI TestClient smoke test for `/leads`, `/simulate-reply`, `/leads`, `/leads/{id}/timeline`, `/analytics/ab-by-demographics`
- Started FastAPI on `127.0.0.1:8000`
- Started Streamlit on `127.0.0.1:8501`
