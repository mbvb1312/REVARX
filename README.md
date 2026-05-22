# 🤖 Steps AI Reactivation Agent (REVARX AI)
### National Level Online Hackathon 2026 — Organized by Steps AI
**Problem Statement 3: Open Track — AI Agents for Real-World Problems**

---

## 🏢 Executive Summary & Alignment with Steps AI

**Steps AI** empowers businesses to autonomously manage **inbound** queries across website chat, Telegram, WhatsApp, and Shopify integrations. 

**REVARX AI** serves as the **proactive outbound reactivation layer** that sits beside a standard Steps AI deployment. It automatically wakes up a business's cold "lead graveyard" (trials expired, webinar attendees, old form submissions) by:
1. Crafting **hyper-personalized re-engagement messages** using **Gemini 2.0 Flash** (no generic templates).
2. Coordinating **automated A/B message variants** to learn which copywriting tone performs best.
3. intercepting incoming customer replies via **Telegram bot webhooks** and transcribing voice notes using **Groq Whisper**.
4. Sentiment classifying user intent using **Groq LLaMA-3.1** (`hot`, `warm`, `cold`, `unsubscribe`).
5. **Escalating hot leads instantly** to the business owner's personal Telegram so they can close the deal immediately.

---

## 🏗️ System Architecture

```
                 ┌────────────────────────────────────────────────────────┐
                 │                       UI LAYER                         │
                 │              Streamlit Interface Dashboard             │
                 │      - CSV Uploads       - Campaign Previews           │
                 │      - Plotly Analytics  - Lead Board Sentiment Tags   │
                 └───────┬────────────────────────────────────────▲───────┘
                         │ (HTTP / JSON API)                      │ (Plotly chart updates)
                         ▼                                        │
                 ┌────────────────────────────────────────────────┴───────┐
                 │                      API GATEWAY                       │
                 │                 FastAPI Backend Server                 │
                 │       - Upload Leads      - Generate Previews          │
                 │       - Run Campaigns     - Simulate Replies           │
                 └───────┬────────────────────────────────────────┬───────┘
                         │                                        │
                         ▼                                        ▼
      ┌────────────────────────────────────┐            ┌────────────────────────────────────┐
      │            AGENT CORE              │            │             INTEGRATIONS           │
      │  orchestrator.py (LangGraph Flow)  │            │  telegram_webhook.py (Webhooks)    │
      │  message_generator.py (Gemini 2.0) │            │  telegram_sender.py (Outbound)     │
      │  email_sender.py (SendGrid)        │            │  whisper_transcriber.py (Whisper)  │
      │  reply_classifier.py (Groq LLaMA)  │            │  apscheduler (Background Daemons)  │
      └────────────────────────────────────┘            └────────────────────────────────────┘
```

---

## 🛠️ The Modern Tech Stack (100% Free Tiers)

| Layer | Technology | Rationale |
|---|---|---|
| **LLM - Message Gen** | Gemini 2.0 Flash | Rich personalization quality, high rate-limit free tier |
| **LLM - Classifier** | Groq LLaMA 3.1 8B | Instant inference latency, high accuracy |
| **Voice Transcriber** | Groq Whisper (Whisper-large-v3) | Fast, highly accurate audio transcribing |
| **Agent Orchestrator** | LangGraph (open source) | Stateful multi-step graph campaign orchestration |
| **Backend Framework** | FastAPI | Async, high performance python web server |
| **Database** | SQLite + SQLAlchemy | Zero-configuration file database |
| **Delivery Channels** | Telegram Bot API & SendGrid | Real phone testing & free standard SMTP email |
| **Frontend UI** | Streamlit | Rapid development, premium tailorable custom components |
| **Visual Charts** | Plotly | Vibrant, premium interactive dashboard visualizers |
| **Task Daemon** | APScheduler | In-process queue runner |

---

## 🚀 Step-by-Step Setup & Launch Guide

### 1. Project Initialization & Setup
Clone the repository and set up a virtual python environment:
```bash
# Clone
git clone https://github.com/mbvb1312/REVARX.git
cd REVARX

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Keys
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_OWNER_CHAT_ID=your_personal_chat_id_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_sender@email.com
DATABASE_URL=sqlite:///./leads.db
```

### 3. Seed Database
Execute the database seeder to create the SQLite schemas and populate 50 realistic historical re-engagement leads, campaign variant histories, and response sentiment records:
```bash
python seed_data.py
```

### 4. Start the Application Server
Run the FastAPI backend server that handles data streams and integrations:
```bash
uvicorn main:app --reload --port 8000
```

### 5. Launch the Streamlit Interface
In a separate terminal window, boot the modern web dashboard interface:
```bash
streamlit run frontend/app.py
```
Streamlit will automatically open a local web page at **`http://localhost:8501`**.

---

## 🧪 Verification & Sandbox Simulation Mode

REVARX AI comes built with a robust **Outbound Sandbox Simulator** on the homepage so that hackathon judges can test the LLaMA sentiment tagging, voice Whisper transcribing, and analytics graphs instantly **without requiring any API keys configured**:

1. **Sandbox Testing**: Open the Streamlit homepage (`http://localhost:8501`), scroll to the **Sandbox Simulator** at the bottom, select a lead, select a preset text response (or type a custom one), and click **"Simulate Incoming Reply Event"**.
2. **Dynamic Dashboard updates**: The backend will process the message, run the LLaMA classifier, assign status flags, trigger mock Alerts, and immediately update visual charts in the **Analytics Dashboard** and **Lead Status Board** tabs.
3. **Live Campaign Launch**: Once a `GEMINI_API_KEY` is provided, visit the **Launch Campaign** page to review personalized previews written by Gemini and launch a stateful LangGraph campaign.
