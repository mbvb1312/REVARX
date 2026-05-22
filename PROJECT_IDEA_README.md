# 🤖 Dead Lead Reactivation Agent
### National Level Online Hackathon 2026 — Organized by Steps AI
### Problem Statement 3: Open Track — AI Agents for Real-World Problems

---

## ⚠️ READ THIS FIRST — FOR AI CODING AGENTS

This file is the **single source of truth** for this project. If you are an AI coding agent (Cursor, GitHub Copilot, Windsurf, Aider, Claude Code, etc.) picking up this codebase, read this file completely before writing a single line of code.

- The builder is switching between multiple AI agents and IDEs.
- **Do not assume previous context.** This file gives you everything.
- Always check `AGENT_HANDOFF.md` to see what is done and what is pending before starting work.
- Always check the sub-folder README inside whatever folder you are working in.
- After completing a task, update `AGENT_HANDOFF.md` and mark the task complete in `TASK_TRACKER.md`.

---

## 📋 Hackathon Context

| Field | Detail |
|---|---|
| **Event** | National Level Online Hackathon 2026 |
| **Organizer** | Steps AI |
| **Mode** | Online |
| **Duration** | 1 Week (builder has **2 days** remaining) |
| **Team Size** | Solo |
| **Problem Statement** | PS3 — Open Track: AI Agents for Real-World Problems |
| **Theme** | Building Practical AI Solutions for Real-World Challenges |

### Submission Requirements
- [ ] Source Code Repository (GitHub)
- [ ] Project Documentation (this README + sub READMEs)
- [ ] Working Prototype / Demo
- [ ] Presentation Deck
- [ ] Optional Demo Video (Loom, 2 min recommended)

### Evaluation Criteria (ranked by judge weight)
1. **Innovation & Creativity** — Is it a fresh idea? Not a clone?
2. **Technical Implementation** — Does it actually work end-to-end?
3. **Scalability & Practicality** — Can a real business use this?
4. **User Experience** — Is the UI clear and usable?
5. **Problem-Solving Approach** — Is the logic clean and explained?
6. **Final Presentation & Demonstration** — Does the demo work live?

---

## 🏢 About Steps AI (The Organizer / Hiring Company)

> **This hackathon is also a selection process for a Steps AI AI Intern role.**
> Everything you build should feel like it belongs in their product roadmap.

### What Steps AI Does
Steps AI builds **multi-channel AI agents** that let businesses deploy a single AI assistant across:
- Website chat
- WhatsApp
- Instagram DMs
- Slack
- Shopify / WooCommerce
- Internal knowledge bases

Their tagline: *"One agent. Every channel. Full context."*

Their metrics they publicly show:
- **3× avg. query growth in 90 days**
- **80%+ questions resolved autonomously**
- **75% support tickets deflected**
- **82% auto-resolved** (vs 13% handoff, 5% pending)
- **1.4s avg response time**, **99.98% uptime**

### What Steps AI Values (from their LinkedIn)
- Build once, deploy everywhere (same knowledge, same brand voice, across all channels)
- Turn every conversation into insight and revenue
- Proactive AI that learns and adapts — not just a chatbot
- Analytics: real insight into what visitors want

### Why Our Project Fits Steps AI Perfectly
Our "Dead Lead Reactivation Agent" is the **proactive** version of what they sell. Their product handles inbound conversations. Ours handles **outbound reactivation** — a use case their B2B customers desperately need. We use the same architecture: multi-channel, agentic, analytics-driven.

During the demo pitch, say:
> *"This is the proactive layer that sits beside a StepsAI deployment — turning cold leads back into conversations."*

---

## 💡 The Project: Dead Lead Reactivation Agent

### The Real-World Problem
Every small and medium business has a "lead graveyard" — people who showed interest (clicked an ad, filled a form, chatted once) and then went silent. These leads are already warm in intent but were never properly followed up. Manually re-engaging hundreds of them is:
- Time-consuming (hours per campaign)
- Generic (same message to everyone)
- Poorly timed (sent at wrong hours)
- Untracked (no idea what works)

Most businesses just write these leads off. That's lost revenue.

### Our Solution
An **autonomous AI agent** that:
1. Takes a CSV of old/cold leads with context (name, product interest, last contact date, notes)
2. Uses **Gemini 2.0 Flash** to generate a **hyper-personalised** reactivation message per lead (not a template — genuinely personalised)
3. Generates **2 variants per lead (A/B test)** automatically
4. **Sends** the message at the optimal time via Telegram bot or email (SendGrid)
5. **Receives and classifies replies** using Groq LLaMA: Hot / Warm / Cold / Unsubscribe
6. **Escalates hot leads** instantly (sends an alert to the business owner)
7. Optionally transcribes **voice note replies** using Groq Whisper
8. Tracks everything in an **analytics dashboard**: funnel, A/B results, reply rates, best-performing message styles

### What Makes This New and Different
- Not a CRM (no manual tagging)
- Not a bulk mailer (every message is unique, AI-written)
- Not a chatbot (proactive, not reactive)
- The A/B testing loop is **automatic** — the agent learns which style works without human input
- Multi-channel: same agent sends on Telegram or email

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│                 INPUT LAYER                  │
│  CSV Upload → Lead Parser → Lead DB (SQLite) │
│  Streamlit UI (campaign controls + preview)  │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│               AGENT CORE                    │
│  LangGraph Orchestrator (stateful loop)     │
│  ┌─────────────┐  ┌──────────────┐          │
│  │ Gemini 2.0  │  │ A/B Tester   │          │
│  │ Flash       │  │ (variant gen)│          │
│  │ (message    │  └──────────────┘          │
│  │  generation)│  ┌──────────────┐          │
│  └─────────────┘  │ Reply        │          │
│                   │ Classifier   │          │
│                   │ (Groq LLaMA) │          │
│                   └──────────────┘          │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│              OUTPUT LAYER                   │
│  Telegram Bot API  │  SendGrid Email (free) │
│  Groq Whisper (voice reply transcription)   │
│  SQLite → Analytics Dashboard (Streamlit)   │
└─────────────────────────────────────────────┘
```

---

## 🗂️ Folder Structure

```
dead-lead-agent/
│
├── PROJECT_IDEA_README.md     ← YOU ARE HERE (master context file)
├── AGENT_HANDOFF.md           ← Current build status, what's done, what's next
├── TASK_TRACKER.md            ← Checkbox task list for the full project
│
├── main.py                    ← FastAPI entry point
├── requirements.txt           ← All Python dependencies
├── .env.example               ← Environment variables template (never commit .env)
├── seed_data.py               ← Script to seed 50 realistic dummy leads
│
├── backend/
│   ├── README.md              ← Agent instructions for backend work
│   ├── database.py            ← SQLite setup, table creation, ORM models
│   ├── models.py              ← Pydantic models / data schemas
│   ├── csv_parser.py          ← CSV upload, validation, insert to DB
│   └── scheduler.py           ← Time-of-day send scheduler (APScheduler)
│
├── agent_core/
│   ├── README.md              ← Agent instructions for AI/LLM work
│   ├── orchestrator.py        ← LangGraph stateful agent graph
│   ├── message_generator.py   ← Gemini 2.0 Flash prompt + call
│   ├── ab_tester.py           ← Generate variant A & B, store both
│   └── reply_classifier.py    ← Groq LLaMA classification logic
│
├── channels/
│   ├── README.md              ← Agent instructions for channel integrations
│   ├── telegram_sender.py     ← Send messages via Telegram Bot API
│   ├── telegram_webhook.py    ← Receive replies from Telegram webhook
│   ├── email_sender.py        ← SendGrid email sending
│   └── whisper_transcriber.py ← Groq Whisper for voice note replies
│
├── frontend/
│   ├── README.md              ← Agent instructions for Streamlit UI
│   ├── app.py                 ← Main Streamlit app (multi-page)
│   ├── pages/
│   │   ├── 01_upload.py       ← CSV upload + lead table view
│   │   ├── 02_campaign.py     ← Campaign settings + message preview
│   │   ├── 03_dashboard.py    ← Analytics dashboard
│   │   └── 04_leads.py        ← Lead status board (hot/warm/cold)
│   └── components/
│       └── charts.py          ← Reusable Plotly chart functions
│
└── analytics/
    ├── README.md              ← Agent instructions for analytics work
    └── queries.py             ← All SQLite query functions for dashboard
```

---

## 🛠️ Full Tech Stack (100% Free)

| Layer | Tool | Why |
|---|---|---|
| LLM - Message Gen | Gemini 2.0 Flash (API key) | Best free-tier quality, fast |
| LLM - Classification | Groq LLaMA 3.1 8B (API key) | Ultra-fast inference, free |
| Voice Transcription | Groq Whisper (via Groq API) | Free with Groq key |
| Agent Orchestration | LangGraph (open source) | Stateful agent loops |
| Backend Framework | FastAPI | Async, clean, production-grade |
| Database | SQLite | Zero setup, file-based, enough for demo |
| Messaging Channel | Telegram Bot API | Free, instant, real phone demo |
| Email Channel | SendGrid Free Tier | 100 emails/day free |
| Frontend/UI | Streamlit | Fast to build, looks decent |
| Charts | Plotly (via streamlit) | Beautiful interactive charts |
| Scheduling | APScheduler | In-process job scheduling, free |
| Task Running | Python threading | No Celery needed for demo scope |

### API Keys Needed
```
GEMINI_API_KEY=       # From Google AI Studio (free)
GROQ_API_KEY=         # From console.groq.com (free)
TELEGRAM_BOT_TOKEN=   # From @BotFather on Telegram (free)
SENDGRID_API_KEY=     # From sendgrid.com (free tier)
```

---

## 🗃️ Database Schema

```sql
-- Leads imported from CSV
CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    telegram_chat_id TEXT,
    product_interest TEXT,
    last_contact_date TEXT,
    notes TEXT,
    status TEXT DEFAULT 'cold',        -- cold | warm | hot | unsubscribed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns (a batch of lead outreach)
CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    tone TEXT DEFAULT 'friendly',       -- friendly | professional | urgent
    channel TEXT DEFAULT 'telegram',    -- telegram | email
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages sent (one per lead per campaign, two variants)
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER REFERENCES leads(id),
    campaign_id INTEGER REFERENCES campaigns(id),
    variant TEXT,                        -- A or B
    content TEXT,
    channel TEXT,
    status TEXT DEFAULT 'pending',       -- pending | sent | failed
    sent_at TIMESTAMP,
    opened_at TIMESTAMP                  -- future: webhook tracking
);

-- Replies received
CREATE TABLE replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER REFERENCES leads(id),
    message_id INTEGER REFERENCES messages(id),
    content TEXT,                        -- text or transcribed voice
    is_voice_note BOOLEAN DEFAULT 0,
    classification TEXT,                 -- hot | warm | cold | unsubscribe
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🤖 Gemini Prompt Template (message_generator.py)

```python
SYSTEM_PROMPT = """
You are a skilled sales copywriter helping a business re-engage cold leads.
Your messages must feel personal, warm, and human — never like a bulk email.
You write in a conversational style appropriate to the given tone.
Always return ONLY valid JSON, no markdown, no preamble.
"""

USER_PROMPT = """
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
```

---

## 🔁 LangGraph Agent Flow

```
START
  │
  ▼
[load_leads] — fetch all leads with status='cold' from DB
  │
  ▼
[generate_messages] — for each lead: call Gemini, get variant A + B
  │
  ▼
[schedule_send] — determine send time (morning 9am / afternoon 5pm)
  │
  ▼
[send_messages] — send via Telegram or Email, update status in DB
  │
  ▼
[wait_for_replies] — Telegram webhook catches replies, stores in DB
  │
  ▼
[classify_replies] — Groq LLaMA classifies each reply
  │
  ├── HOT → [escalate] — send alert message to business owner Telegram
  ├── WARM → [mark_warm] — update lead status, schedule follow-up
  ├── COLD → [mark_cold] — update status
  └── UNSUBSCRIBE → [mark_unsubscribed] — never contact again
  │
  ▼
[update_analytics] — write all stats to DB for dashboard
  │
  ▼
END (or loop back for follow-up campaign)
```

---

## 📊 Analytics Dashboard (What to Show)

These are the key screens judges will see. Build these first on Day 2.

### Screen 1: Campaign Funnel
- Sent → Replied → Hot leads (numbers + bar chart)

### Screen 2: A/B Test Results
- Variant A reply rate vs Variant B reply rate
- Best tone: friendly vs professional vs urgent
- Winner badge on the better variant

### Screen 3: Lead Status Board
- Cards: X Hot | X Warm | X Cold | X Unsubscribed
- Table: lead name, status, last activity, classification

### Screen 4: Activity Heatmap
- When do replies arrive? (hour of day)
- Best send time recommendation

### Demo Numbers to Pre-seed (seed_data.py)
Use these realistic numbers in dummy data:
- 50 leads total
- 38 sent, 12 pending
- 13 replies (34% rate on variant A, 21% on variant B)
- 5 hot, 4 warm, 4 cold
- Peak reply time: 10am–12pm

---

## ⚡ 2-Day Sprint Plan

> **You have 2 days. Every hour matters. Follow this exactly.**

### DAY 1 — Core Pipeline (Get it working end-to-end)

**Morning (0–3h): Foundation**
- [ ] Set up repo, virtual env, install requirements
- [ ] `backend/database.py` — create all 4 tables
- [ ] `backend/csv_parser.py` — parse CSV, insert leads to DB
- [ ] `seed_data.py` — seed 50 realistic dummy leads with realistic fields
- [ ] Test: `python seed_data.py` → verify data in DB

**Midday (3–6h): AI Message Generation**
- [ ] `agent_core/message_generator.py` — Gemini call with the prompt above
- [ ] `agent_core/ab_tester.py` — call generator twice per lead, store A+B
- [ ] Test: generate messages for 3 leads, print them, verify they feel personal

**Afternoon (6–9h): Send Channel**
- [ ] `channels/telegram_sender.py` — send a message to your own Telegram
- [ ] `channels/email_sender.py` — send a test email via SendGrid
- [ ] `frontend/app.py` + `pages/01_upload.py` — CSV upload UI
- [ ] `frontend/pages/02_campaign.py` — campaign settings + message preview panel

**End of Day 1 Goal:** Upload CSV → See generated messages in UI → Click send → Message arrives on Telegram phone

---

### DAY 2 — Intelligence + Dashboard + Polish

**Morning (0–3h): Reply Handling**
- [ ] `channels/telegram_webhook.py` — FastAPI webhook endpoint to receive replies
- [ ] `agent_core/reply_classifier.py` — Groq LLaMA classifies reply text
- [ ] Hot lead escalation — send alert to your Telegram when hot lead detected
- [ ] Test end-to-end: send message → reply manually → verify classification

**Midday (3–5h): Analytics Dashboard**
- [ ] `analytics/queries.py` — all stats queries from SQLite
- [ ] `frontend/pages/03_dashboard.py` — funnel chart + A/B chart
- [ ] `frontend/pages/04_leads.py` — lead status board
- [ ] Use seed data to make dashboard look populated

**Afternoon (5–7h): Polish**
- [ ] Follow-up logic: if no reply in X hours, send one more message
- [ ] Unsubscribe handling
- [ ] Error handling: failed sends retry once
- [ ] Clean up Streamlit sidebar + navigation

**Evening (7–9h): Submission Prep**
- [ ] Record 2-min Loom demo video
- [ ] Write GitHub README (use this file as base)
- [ ] Clean up commits
- [ ] Prepare verbal pitch (script in this file)

---

## 🎤 Demo Pitch Script (3 Minutes)

**[0:00–0:30] Open with the problem**
> "Every SMB has a graveyard of leads — people who showed interest and then went silent. Manually re-engaging them is slow, generic, and untracked. Most businesses just write them off. That's the problem we solve."

**[0:30–1:30] Live demo**
> "Watch — I upload this CSV of 50 cold leads. The agent reads each lead's history and writes a genuinely personalised message — not a template. Here's what it wrote for Priya, who was interested in a productivity tool three months ago. [show message]. That just took 1.4 seconds. It also wrote a variant B automatically for A/B testing."

**[1:30–2:15] Show the intelligence**
> "When a reply comes in, the agent classifies it instantly — hot, warm, cold, or unsubscribe. Hot leads trigger an immediate alert to the business owner. And look at this: variant A got a 34% reply rate, variant B got 21%. The agent learned that automatically. Next campaign, it'll use the winner."

**[2:15–3:00] The StepsAI connection**
> "This is the proactive layer that sits beside a StepsAI deployment. You already help businesses handle inbound conversations across every channel. This handles the moment before a customer becomes a customer — turning cold leads back into conversations, with full analytics. I built this solo in 2 days using free tools. I'd love the chance to build the production version inside StepsAI."

---

## 🏆 How to Stand Out Among 30 Participants

Most participants will build one of these:
- An AI study assistant (PS1 — will be 10+ submissions)
- A mock interview bot (PS2 — will be 5+ submissions)
- A generic chatbot for PS3

**You are doing none of those. Here's your edge:**

| What others do | What you do |
|---|---|
| Static chatbot that answers questions | Autonomous agent that takes actions |
| One LLM call per interaction | Multi-step LangGraph orchestration |
| No analytics | Full analytics dashboard with A/B test results |
| Generic UI | Real Telegram message arriving on a real phone |
| Talk about multi-channel | Actually build two channels |
| No real-world grounding | Directly tied to Steps AI's own product line |
| 7-day polish | Demo-ready in 2 days (signals speed and focus) |

**The single biggest differentiator:** Show the Telegram message arriving on your real phone during the demo. Nothing in a hackathon beats a live, real-world moment.

---

## 🔑 Environment Variables

Create a `.env` file (never commit this):

```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_OWNER_CHAT_ID=your_personal_chat_id_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_sender@email.com
DATABASE_URL=sqlite:///./leads.db
```

---

## 📦 requirements.txt

```
fastapi==0.111.0
uvicorn==0.29.0
python-dotenv==1.0.0
google-generativeai==0.7.2
groq==0.9.0
langgraph==0.1.0
langchain-core==0.2.0
python-telegram-bot==21.3
sendgrid==6.11.0
streamlit==1.35.0
plotly==5.22.0
pandas==2.2.2
SQLAlchemy==2.0.30
apscheduler==3.10.4
python-multipart==0.0.9
httpx==0.27.0
```

---

## 🚀 How to Run

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd dead-lead-agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your actual keys

# 3. Seed dummy data
python seed_data.py

# 4. Start the FastAPI backend (handles Telegram webhook)
uvicorn main:app --reload --port 8000

# 5. Start the Streamlit frontend (separate terminal)
streamlit run frontend/app.py

# 6. (Optional) Expose webhook for Telegram using ngrok
ngrok http 8000
# Then set webhook: https://api.telegram.org/bot<TOKEN>/setWebhook?url=<ngrok-url>/webhook
```

---

## 📝 Notes for AI Coding Agents

- **Always load `.env` using `python-dotenv` at the top of every file that needs API keys.**
- **Never hardcode API keys.**
- **SQLite database file is `leads.db` in project root.**
- **All Gemini calls use `gemini-2.0-flash` model.**
- **All Groq classification calls use `llama-3.1-8b-instant` model for speed.**
- **Telegram webhook endpoint must be at `POST /webhook` in `main.py`.**
- **Streamlit app is multi-page. Pages are in `frontend/pages/`. Main app is `frontend/app.py`.**
- **Check `AGENT_HANDOFF.md` before starting — it tells you exactly what is built and what is not.**

---

*Last updated: Start of project. Builder: Solo. Hackathon: Steps AI National Hackathon 2026.*
