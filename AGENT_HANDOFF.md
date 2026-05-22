# 🔄 AGENT HANDOFF FILE
### Dead Lead Reactivation Agent — Steps AI Hackathon 2026

> **This file is updated after every work session.**
> If you are an AI coding agent picking up this project, read this BEFORE anything else.
> It tells you exactly where the project stands right now.

---

## ⏰ Time Remaining
**2 days to submission deadline.**
Priority order: Core pipeline → Reply classification → Analytics dashboard → Polish → Demo prep

---

## 📍 Current Project Status

**PHASE:** Foundation complete, AI core next (Day 1 Block 2)
**Last agent session:** Added backend foundation, CSV parser, and seed data; repo is live and updated
**Next agent should start at:** Implement `agent_core/message_generator.py` (Day 1 Block 2)

---

## ✅ COMPLETED — Do Not Redo

- [x] Project idea chosen: Dead Lead Reactivation Agent
- [x] Architecture designed (see PROJECT_IDEA_README.md)
- [x] Tech stack finalized (see requirements.txt section)
- [x] Database schema designed (4 tables: leads, campaigns, messages, replies)
- [x] Gemini prompt template written (in PROJECT_IDEA_README.md)
- [x] LangGraph agent flow designed (in PROJECT_IDEA_README.md)
- [x] Folder structure decided (see PROJECT_IDEA_README.md)
- [x] Demo pitch script written (in PROJECT_IDEA_README.md)
- [x] All README files written (this file + sub-folder READMEs)
- [x] Git repository initialized and pushed to GitHub
- [x] .gitignore added (ignores .env, venv, db, caches)
- [x] Base folder structure created (backend/, agent_core/, channels/, frontend/pages/, frontend/components/, analytics/)

---

## 🚧 IN PROGRESS — Currently Being Built

Day 1 Block 2: AI Message Generation (message_generator.py next)

---

## ❌ NOT STARTED — Needs to Be Built

### DAY 1 TASKS (Build these first)

#### Block 1: Foundation (do this first, in this order)
- [x] `requirements.txt` — create with all packages listed in PROJECT_IDEA_README.md
- [x] `.env.example` — create with all env var names (no real values)
- [x] `backend/database.py` — SQLite connection + create all 4 tables on startup
- [x] `backend/models.py` — Pydantic models for Lead, Campaign, Message, Reply
- [x] `backend/csv_parser.py` — accept uploaded CSV, validate, insert rows to `leads` table
- [x] `seed_data.py` — insert 50 realistic dummy leads into DB

#### Block 2: AI Message Generation
- [ ] `agent_core/message_generator.py` — Gemini 2.0 Flash call using prompt in PROJECT_IDEA_README.md
- [ ] `agent_core/ab_tester.py` — call message_generator twice per lead, label as variant A and B, store both in `messages` table
- [ ] Manual test: run ab_tester on 3 seed leads, print outputs, confirm they look personalised

#### Block 3: Send Channel (Telegram first, email second)
- [ ] `channels/telegram_sender.py` — function `send_telegram(chat_id, message)` using bot token
- [ ] `channels/email_sender.py` — function `send_email(to_email, subject, body)` using SendGrid
- [ ] Test: send one message to your own Telegram, confirm receipt on phone

#### Block 4: Basic Streamlit UI
- [ ] `frontend/app.py` — Streamlit multi-page shell with sidebar nav
- [ ] `frontend/pages/01_upload.py` — CSV file uploader, calls csv_parser, shows lead table
- [ ] `frontend/pages/02_campaign.py` — tone selector, channel selector, "Generate Messages" button, message preview for first 3 leads
- [ ] Test: full flow — upload CSV → generate messages → see previews → click Send → confirm Telegram receives it

**END OF DAY 1 GOAL:** Upload CSV → See generated messages → Send → Receive on phone.

---

### DAY 2 TASKS (Build these second)

#### Block 5: Reply Handling
- [ ] `channels/telegram_webhook.py` — FastAPI POST `/webhook` endpoint, receives Telegram updates, stores reply in `replies` table
- [ ] `agent_core/reply_classifier.py` — Groq LLaMA call: classify reply text as hot/warm/cold/unsubscribe
- [ ] Hot lead escalation: when classification = 'hot', call `telegram_sender.send_telegram(OWNER_CHAT_ID, alert_message)`
- [ ] `channels/whisper_transcriber.py` — if reply is a voice note (audio file), call Groq Whisper to transcribe first
- [ ] `main.py` — wire up FastAPI app: include webhook router, handle startup DB init
- [ ] Test: send message → manually reply → verify reply is stored + classified in DB

#### Block 6: Analytics Dashboard
- [ ] `analytics/queries.py` — functions: get_funnel_stats(), get_ab_results(), get_lead_status_counts(), get_hourly_reply_distribution()
- [ ] `frontend/pages/03_dashboard.py` — Plotly bar chart for funnel, Plotly grouped bar for A/B, metric cards for lead status counts
- [ ] `frontend/pages/04_leads.py` — table showing all leads with current status + classification

#### Block 7: Polish
- [ ] `backend/scheduler.py` — APScheduler job: scan for pending messages, send at scheduled time
- [ ] Follow-up logic: if lead replied 'warm', schedule a follow-up message 48h later (can be simplified: just mark as 'needs_followup')
- [ ] Unsubscribe: if classification = 'unsubscribe', update lead.status = 'unsubscribed', never send again (add check in sender)
- [ ] Error handling: wrap all API calls in try/except, log failures to console, retry once on send failure

#### Block 8: Submission Prep
- [ ] `seed_data.py` — ensure 50 realistic dummy leads with varied statuses (some already replied, some hot, some cold)
- [ ] Record 2-min Loom demo video
- [ ] Push to GitHub with clean commit history
- [ ] Prepare GitHub repo README (copy from PROJECT_IDEA_README.md, trim to essentials)

---

## 🔑 Key Facts for the Next Agent

| Item | Value |
|---|---|
| Database file | `leads.db` in project root |
| Gemini model | `gemini-2.0-flash` (not 1.5, not pro) |
| Groq classification model | `llama-3.1-8b-instant` |
| Groq whisper model | `whisper-large-v3` |
| Telegram webhook route | `POST /webhook` in main.py |
| Streamlit pages folder | `frontend/pages/` |
| All env vars | Loaded via python-dotenv from `.env` |

---

## ⚠️ Decisions Already Made — Do Not Change These

| Decision | Rationale |
|---|---|
| SQLite (not PostgreSQL) | Zero setup, file-based, enough for demo scope |
| LangGraph (not custom loop) | Signals technical depth to judges |
| Telegram as primary channel | Can demo on real phone live, free, no approval needed |
| Gemini 2.0 Flash (not Pro) | Free tier, sufficient quality for messages |
| Streamlit (not React/Next.js) | 2-day timeline, no frontend build time |
| No model training | Explicitly in scope constraints |
| A/B testing built-in | Key differentiator vs other submissions |

---

## 📝 Instructions for the Coding Agent

1. Read `PROJECT_IDEA_README.md` for full context, schema, prompts, and architecture
2. Read the sub-folder README inside any folder you plan to work in
3. Always use python-dotenv to load env vars — never hardcode
4. After completing each checkbox task above, mark it `[x]`
5. If you encounter a blocker, write it at the bottom of this file under "Blockers"
6. Do not refactor or rename anything already built — only build what is in the task list

---

## 🚫 Blockers / Known Issues

*(None yet — write any blockers here as you find them)*

---

*Update this file after every session. The next agent depends on it.*
