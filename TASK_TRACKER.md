# ✅ TASK TRACKER
### Dead Lead Reactivation Agent — Steps AI Hackathon 2026

> Check off tasks as you complete them. Keep this in sync with `AGENT_HANDOFF.md`.
> Organized by priority and dependency order — build top to bottom.

---

## 🏗️ SETUP (Do first, takes ~15 mins)

- [ ] Create Python virtual environment: `python -m venv venv`
- [ ] Activate venv: `source venv/bin/activate`
- [x] Create `requirements.txt` (contents in PROJECT_IDEA_README.md)
- [ ] Run `pip install -r requirements.txt`
- [ ] Create `.env` file from `.env.example`
- [ ] Confirm Gemini API key works: test a basic call
- [ ] Confirm Groq API key works: test a basic call
- [ ] Create Telegram bot via @BotFather, get token
- [ ] Get your own Telegram chat ID (message @userinfobot)
- [ ] Create SendGrid account, get API key, verify sender email
- [x] Create project folder structure (mkdir backend agent_core channels frontend/pages frontend/components analytics)

---

## 📁 BACKEND

- [x] `backend/database.py`
  - [x] SQLite connection using SQLAlchemy
  - [x] Create `leads` table
  - [x] Create `campaigns` table
  - [x] Create `messages` table
  - [x] Create `replies` table
  - [x] `init_db()` function that creates all tables if they don't exist

- [x] `backend/models.py`
  - [x] Pydantic `LeadCreate` model (name, email, telegram_chat_id, product_interest, last_contact_date, notes)
  - [x] Pydantic `Lead` model (includes id, status, created_at)
  - [x] Pydantic `MessageCreate` model
  - [x] Pydantic `ReplyCreate` model

- [x] `backend/csv_parser.py`
  - [x] `parse_csv(file)` function — accepts UploadFile from FastAPI
  - [x] Validate required columns: name, email, product_interest, last_contact_date, notes
  - [x] Insert each row as a Lead into DB
  - [x] Return count of inserted leads
  - [x] Handle duplicate emails gracefully (skip, don't crash)

- [ ] `backend/scheduler.py`
  - [ ] APScheduler setup
  - [ ] Job: `scan_and_send()` — runs every hour, finds messages with status='pending' and scheduled_time <= now, sends them
  - [ ] Morning slot: 9:00 AM
  - [ ] Afternoon slot: 5:00 PM

---

## 🤖 AGENT CORE

- [x] `agent_core/message_generator.py`
  - [x] Load Gemini API key from env
  - [x] `generate_message(lead, tone, channel)` function
  - [x] Use exact prompt template from PROJECT_IDEA_README.md
  - [x] Parse JSON response safely (handle malformed JSON)
  - [x] Return dict with `subject` and `message` keys
  - [ ] Test: call with 3 different leads, verify output quality

- [x] `agent_core/ab_tester.py`
  - [x] `generate_ab_variants(lead_id, campaign_id, tone, channel)` function
  - [x] Call `generate_message()` twice (same lead, same params — Gemini gives variation naturally)
  - [x] Store variant A in `messages` table
  - [x] Store variant B in `messages` table
  - [x] Return both message dicts

- [ ] `agent_core/reply_classifier.py`
  - [ ] Load Groq API key from env
  - [ ] `classify_reply(reply_text)` function
  - [ ] Groq LLaMA prompt: classify as EXACTLY one of: hot, warm, cold, unsubscribe
  - [ ] Return classification string (lowercase)
  - [ ] Test: classify "Yes I'm interested, let's talk" → must return 'hot'
  - [ ] Test: classify "Please remove me from your list" → must return 'unsubscribe'

- [ ] `agent_core/orchestrator.py`
  - [ ] LangGraph `StateGraph` setup
  - [ ] State: `{leads: list, campaign_id: int, messages: list, current_index: int}`
  - [ ] Node: `load_leads` — fetch cold leads from DB
  - [ ] Node: `generate_messages` — loop through leads, call ab_tester
  - [ ] Node: `send_messages` — loop through generated messages, call sender
  - [ ] Node: `update_status` — mark messages as sent in DB
  - [ ] Edge: load_leads → generate_messages → send_messages → update_status → END
  - [ ] `run_campaign(campaign_id, tone, channel)` entrypoint function

---

## 📡 CHANNELS

- [x] `channels/telegram_sender.py`
  - [x] Load bot token from env
  - [x] `send_telegram(chat_id, message)` async function using python-telegram-bot
  - [x] Return True on success, False on failure
  - [ ] Test: send "Hello from the agent" to your own chat_id

- [ ] `channels/telegram_webhook.py`
  - [ ] FastAPI `APIRouter` with `POST /webhook` endpoint
  - [ ] Parse incoming Telegram Update object
  - [ ] Extract: chat_id, message text, is_voice_note flag
  - [ ] If voice note: get file_id, download audio bytes, pass to whisper_transcriber
  - [ ] Find matching lead by telegram_chat_id in DB
  - [ ] Store reply in `replies` table
  - [ ] Call `reply_classifier.classify_reply(text)`
  - [ ] Update lead status in DB
  - [ ] If classification == 'hot': call `send_telegram(OWNER_CHAT_ID, alert)`
  - [ ] Return `{"ok": True}` to Telegram

- [x] `channels/email_sender.py`
  - [x] Load SendGrid key from env
  - [x] `send_email(to_email, subject, body)` function
  - [x] Return True on success, False on failure
  - [ ] Test: send test email, confirm receipt

- [ ] `channels/whisper_transcriber.py`
  - [ ] Load Groq key from env
  - [ ] `transcribe_audio(audio_bytes, filename)` function
  - [ ] Call Groq Whisper API with audio content
  - [ ] Return transcription string

---

## 🖥️ FRONTEND (Streamlit)

- [x] `frontend/app.py`
  - [x] Streamlit page config: title "Dead Lead Reactivation Agent", wide layout
  - [x] Sidebar: navigation links to all 4 pages
  - [x] Home page: brief intro text, key metrics cards (total leads, sent today, hot leads)

- [x] `frontend/pages/01_upload.py`
  - [x] Page title: "Upload Leads"
  - [x] `st.file_uploader()` for CSV files
  - [x] On upload: call FastAPI `/upload-leads` endpoint
  - [x] Show success message with count of leads imported
  - [x] Show leads table using `st.dataframe()`
  - [x] Add "Download sample CSV" button with an example CSV template

- [ ] `frontend/pages/02_campaign.py`
  - [ ] Page title: "Run Campaign"
  - [ ] `st.selectbox()` for tone: Friendly / Professional / Urgent
  - [ ] `st.selectbox()` for channel: Telegram / Email
  - [ ] `st.text_input()` for campaign name
  - [ ] "Generate Message Previews" button — calls agent, shows first 5 generated messages
  - [ ] For each preview: show variant A and variant B side by side
  - [ ] "Launch Campaign" button — sends all messages
  - [ ] Progress bar during sending
  - [ ] Success summary: "X messages sent"

- [ ] `frontend/pages/03_dashboard.py`
  - [ ] Page title: "Analytics"
  - [ ] Row 1: 4 metric cards — Sent / Replied / Hot Leads / Reply Rate %
  - [ ] Funnel chart: Sent → Replied → Hot (Plotly funnel chart)
  - [ ] A/B test results: grouped bar chart (Variant A vs B, reply rate)
  - [ ] Tone performance: which tone got best replies?
  - [ ] Hourly distribution: bar chart of what hour replies come in

- [ ] `frontend/pages/04_leads.py`
  - [ ] Page title: "Lead Status"
  - [ ] 4 colored metric cards: Hot (red), Warm (amber), Cold (gray), Unsubscribed (muted)
  - [ ] Filterable table: filter by status
  - [ ] For each lead: name, email, product_interest, status, last reply, classification
  - [ ] Click a lead row: expand to show full message sent + reply received

- [ ] `frontend/components/charts.py`
  - [ ] `funnel_chart(sent, replied, hot)` → Plotly figure
  - [ ] `ab_bar_chart(a_rate, b_rate)` → Plotly figure
  - [ ] `hourly_heatmap(hours_data)` → Plotly figure

---

## 📊 ANALYTICS

- [ ] `analytics/queries.py`
  - [ ] `get_funnel_stats(campaign_id=None)` → dict with sent, replied, hot counts
  - [ ] `get_ab_results(campaign_id=None)` → dict with variant_a_rate, variant_b_rate
  - [ ] `get_lead_status_counts()` → dict with hot, warm, cold, unsubscribed counts
  - [ ] `get_hourly_reply_distribution()` → list of (hour, count) tuples
  - [ ] `get_all_leads_with_status()` → list of lead dicts with latest reply info
  - [ ] `get_tone_performance()` → dict of tone → reply rate

---

## 🌱 SEED DATA

- [x] `seed_data.py`
  - [x] Generate 50 realistic leads with varied:
    - Names (Indian names — localised for Pondicherry context)
    - Product interests (productivity tool, CRM software, e-commerce solution, HR platform, inventory management)
    - Last contact dates (1–6 months ago)
    - Notes (e.g. "Attended webinar", "Requested pricing", "Trial expired")
    - Emails and telegram_chat_ids (fake but formatted correctly)
  - [x] Assign statuses: 20 cold, 10 warm, 5 hot, 5 unsubscribed, 10 pending
  - [x] Insert 50 messages (one per cold lead, sent)
  - [x] Insert 13 replies (for leads that replied):
    - 5 hot replies ("Yes let's talk", "I'm interested", etc.)
    - 4 warm replies ("Maybe next month", "Send me more info")
    - 4 cold replies ("Not interested right now")
  - [x] Confirm data looks good: `python seed_data.py && python -c "from backend.database import get_db; ..."`

---

## 🔌 MAIN APP

- [ ] `main.py`
  - [ ] FastAPI app init
  - [ ] Load `.env` on startup
  - [ ] Call `init_db()` on startup
  - [ ] Include `telegram_webhook.router`
  - [ ] `POST /upload-leads` endpoint: accepts CSV, calls csv_parser
  - [ ] `POST /run-campaign` endpoint: accepts campaign settings, calls orchestrator
  - [ ] `GET /leads` endpoint: returns all leads
  - [ ] `GET /analytics/funnel` endpoint: returns funnel stats
  - [ ] `GET /analytics/ab` endpoint: returns A/B results
  - [ ] Health check: `GET /health` returns `{"status": "ok"}`

---

## 📝 SUBMISSION PREP

- [ ] `.env.example` — all env var names with placeholder values, committed to repo
- [ ] `README.md` for GitHub — clean version of PROJECT_IDEA_README.md (remove internal agent notes)
- [ ] GitHub repo created and pushed (clean commit history, not one dump)
- [ ] Loom demo video (2 mins, use script in PROJECT_IDEA_README.md)
- [ ] All 4 screens working in demo mode with seed data
- [ ] Telegram bot tested — message arrives on real phone
- [ ] Practice pitch 2 times before submitting

---

## 📈 Progress Summary

| Phase | Tasks | Done | Remaining |
|---|---|---|---|
| Setup | 11 | 0 | 11 |
| Backend | 15 | 0 | 15 |
| Agent Core | 18 | 0 | 18 |
| Channels | 16 | 0 | 16 |
| Frontend | 21 | 0 | 21 |
| Analytics | 6 | 0 | 6 |
| Seed Data | 7 | 0 | 7 |
| Main App | 8 | 0 | 8 |
| Submission | 8 | 0 | 8 |
| **Total** | **110** | **0** | **110** |

---

*Update counts as tasks are completed.*
