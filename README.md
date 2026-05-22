# 🤖 REVARX AI — Dead Lead Reactivation Agent
### PS3 (Open Track) — Autonomous Multi-Channel Re-Engagement & A/B Learning Agent
*Organized by Steps AI*

[![GitHub License](https://img.shields.ly/badge/license-MIT-blue.svg)](LICENSE)
[![FastAPI Backend](https://img.shields.ly/badge/backend-FastAPI-green.svg)](main.py)
[![Streamlit UI](https://img.shields.ly/badge/frontend-Streamlit-orange.svg)](frontend/app.py)

---

## 💡 The Executive Pitch: Resurrecting the Lead Graveyard

Every sales team, marketer, and small business owner shares a frustrating bottleneck: **The Lead Graveyard**. 

These are the hundreds of people who filled out a form, attended a webinar, or signed up for a trial, only to go silent. These leads are *warm in intent* but went cold due to lack of timely, high-touch follow-up. 
* **The Cost of Manual Follow-Up**: Writing a bespoke, highly personalized re-engagement message for 500 cold contacts is operationally impossible.
* **The Failure of Mass Emailing**: Sending generic, template-driven spam emails leads to massive unsubscribe rates and domain reputation damage.

### 🌟 The Solution: REVARX AI
**REVARX AI** is an autonomous outbound sales agent that acts as a 24/7 dedicated re-engagement representative. It connects directly to your databases, ingests cold records, and converts them back into active sales conversations across **WhatsApp, Telegram, and Email**.

```
  [COLD LEAD GRAVEYARD] 
          │
          ▼
   [REVARX AGENT] ➔ Personalized Variant Generation (Gemini 2.0)
          │
          ▼
   [MULTI-CHANNEL DISPATCH] ➔ WhatsApp (Twilio) | Telegram | Email (SendGrid)
          │
          ▼
   [sentiment classifier] ➔ Groq LLaMA-3.1 Sentiment Analysis
          │
          ├── HOT 🔥 ➔ Push Notification Alert to Owner + Immediate Pipeline Handoff
          ├── WARM 🟡 ➔ Scheduled Follow-Up Task Created
          ├── COLD 🔵 ➔ Retained in Database
          └── UNSUBSCRIBE 🚫 ➔ Instantly Suppressed
```

By automatically running localized, context-driven re-engagement campaigns and testing different tones in real-time, **REVARX AI turns dead databases back into active pipelines without a single click from your sales reps.**

---

## 📡 Multi-Channel Re-Engagement Architecture

Instead of locking you into a single inbox, REVARX AI deploys your brand voice consistently across three key channels:

1. **Telegram (Live BOT Interface)**: Perfect for immediate, zero-friction local tests. Leads receive stylized Markdown messages, and their text or **voice note** replies are parsed instantly.
2. **WhatsApp Business (Twilio Hook Ready)**: The highest open-rate messaging channel globally. Directly integrated to send outbound check-ins and receive instant replies.
3. **SendGrid Email API**: Handles formal corporate outreach, writing custom subject lines and email copy that naturally references the lead's historical product interest and notes.

---

## 🧠 Technical Deep-Dive: Stateful AI Orchestration

REVARX AI is not a collection of static prompts; it is a **state-driven autonomous agent** designed to represent production-grade agentic engineering.

### 1. Stateful Campaign Graph (LangGraph)
Outbound execution is governed by a **LangGraph StateGraph** pipeline. Rather than executing disjointed API calls, the campaign maintains state integrity as it steps through nodes:
* `load_leads` node: Queries SQLite, filters cold records, and constructs context.
* `generate_messages` node: Invokes **Gemini 2.0 Flash** to compose personalized, context-aware variant pairs.
* `send_messages` node: Alternates between Variant A and B for strict statistical A/B isolation, sending them over the configured channel.
* `update_status` node: Transitions the database states to update pipelines.

### 2. Automatic A/B Testing & Optimization Loop
For every cold lead, the agent generates two unique personalized drafts (Variant A and Variant B). It alternates delivery to measure performance scientifically:
* **The Optimization Loop**: The analytics engine tracks the conversion funnel of Variant A vs. Variant B.
* **Auto-Tuning**: If the agent detects Variant A has a significantly higher reply rate, future campaign runs dynamically shift delivery weights to prioritize the winning style—minimizing human intervention.

### 3. sentiment analysis & Audio Transcription (Groq Pipeline)
When a prospect replies, REVARX AI reacts in milliseconds:
* **Voice Note Transcription**: If the customer replies with a voice note, the audio is routed to **Groq Whisper (whisper-large-v3)** for instant, near-flawless text transcription.
* **Groq LLaMA-3.1 Classifier**: The text (or transcript) is evaluated by LLaMA-3.1 to classify sentiment into four discrete categories: `hot` (high-intent), `warm` (later follow-up), `cold` (not interested), or `unsubscribe` (suppression).
* **Owner Alerts**: When a **Hot** lead is detected, a Markdown alert is pushed to the business owner's personal Telegram chat instantly so they can hop into the chat while the lead is active.

---

## 🚀 Setup & Deployment Guide

REVARX AI is built to be run easily by evaluators. It features a complete **Sandbox Simulation Mode** that allows you to test the entire application, database transitions, classifiers, and charts **100% locally with zero API key configuration**.

### Local Installation
```bash
# 1. Clone repository
git clone https://github.com/mbvb1312/REVARX.git
cd REVARX

# 2. Initialize environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# 3. Install packages
pip install -r requirements.txt

# 4. Seed sample data (Pre-populates SQLite with 50 realistic historical leads)
python seed_data.py
```

### Launching the Application

1. **Start the FastAPI Backend**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
2. **Start the Streamlit Frontend** (In a new terminal window):
   ```bash
   streamlit run frontend/app.py
   ```
   Open your browser to **`http://localhost:8501`**.

---

## 🧪 Testing and Verification

### Option A: Zero-Setup Sandbox Testing (No API Keys Needed)
We have added a custom **Outbound Sandbox Simulator** on the homepage:
1. Select a seeded lead (e.g. `Priya Sharma`) and select or type a mock reply.
2. Click **"Simulate Incoming Reply Event"**.
3. A balloon celebration will trigger. The FastAPI server will automatically classify the sentiment locally, update the SQLite DB, shift the lead status to `HOT`, and simulate owner alerts.
4. Browse the **`📊 Analytics Dashboard`** and **`👥 Lead Status Board`** tabs to observe the Plotly charts and conversation inspectors updating dynamically in real-time.

### Option B: Production Integration (Active Keys)
To enable live AI generation and real messenger hooks, configure the `.env` file in the root folder:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_OWNER_CHAT_ID=your_personal_chat_id_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
FROM_EMAIL=your_verified_sender@email.com
DATABASE_URL=sqlite:///./leads.db
```

#### Live Webhook Setup for Telegram:
To allow real Telegram messages to trigger live webhooks during local testing:
1. Expose your port 8000 using Ngrok:
   ```bash
   ngrok http 8000
   ```
2. Register the endpoint with Telegram (replace `<TOKEN>` and `<NGROK_URL>`):
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<NGROK_URL>/webhook"
   ```
3. Text your bot directly or send a voice note. The webhook will download the voice note, transcribe it using Groq Whisper, run LLaMA sentiment tagging, update the SQLite database, and push a live Markdown card to your personal phone!

---

## 🚢 Cloud Deployment Guidelines

For deployment to a cloud environment, REVARX AI is configured to scale easily:

### 1. Dockerized Containerization
A standard `Dockerfile` can package the FastAPI backend and Streamlit frontend in minutes:
```dockerfile
# Dockerfile snippet for unified demo container
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000 8501
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"]
```

### 2. PaaS Deployments (Render / Fly.io / AWS)
* **Backend Hosting**: Deploy the FastAPI server to Render or Fly.io as a web service. Expose port 8000 and ensure the disk persists the `leads.db` file (or connect to a PostgreSQL database by modifying `DATABASE_URL` in env).
* **Frontend Hosting**: Deploy the Streamlit app as a separate static/web service pointing its API fetch URLs to your live backend domain.
* **Persistent Webhooks**: Ensure your backend domain uses HTTPS (Render/Fly.io provide this automatically) so that Telegram and Twilio webhook registries successfully deliver payload posts.
