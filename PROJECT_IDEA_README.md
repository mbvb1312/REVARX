# REVARX AI Project Context

## Product

REVARX AI is an e-commerce browse and cart abandonment recovery agent.

The demo problem is simple: a customer shows product intent on a website, then disappears. They may have clicked an ad, filled a form, chatted once, viewed a laptop, compared sneakers, added headphones to cart, or abandoned checkout. The business already paid for that intent, but follow-up is usually manual, generic, poorly timed, and untracked.

REVARX AI turns that abandoned intent into a live recovery workflow.

## Demo Scope

- Generic e-commerce products for demo: laptops, phones, sneakers, jeans, headphones, watches, bags, and home appliances.
- Email is the active channel now.
- WhatsApp and Telegram remain future integrations.
- Streamlit is the live website.
- FastAPI is the backend.
- SQLite stores customers, messages, replies, and analytics.

## Live Website Modes

### Mock / Seeded Mode

`python seed_data.py` creates 50 Indian e-commerce customers with demographics, product context, recovery emails, replies, and A/B outcomes.

### Live Demo Mode

The user can:

1. Add one abandoned customer manually.
2. Upload CSV or TXT lists of customers.
3. Trigger recovery emails.
4. Simulate replies or no response.
5. Track every customer visually.
6. Watch A/B recommendations improve over time.

## A/B Logic

Variant A is professional and formal.

Variant B is friendly and casual.

The recommender uses weighted historical outcomes for similar customers:

- Age group
- Gender
- Indian state
- Product category

Outcome weights:

- Hot reply: strong positive
- Warm reply: positive
- Cold reply: weak positive
- Unsubscribe: negative
- No response: zero, which lowers the average

## LLM Priority

1. Groq primary
2. SambaNova fallback
3. Gemini optional fallback
4. Local templates and heuristics final fallback

The app must remain demo-safe even when paid/free LLM APIs fail.

## Core API Flow

`POST /leads`

1. Save customer.
2. Recommend A or B.
3. Generate personalized email.
4. Send through Resend.
5. Save message status.
6. Return variant, LLM used, and send result.

`POST /upload-leads`

1. Parse CSV or TXT.
2. Save customers.
3. Queue background email generation/sending.
4. Return inserted/skipped/queued counts.

`POST /simulate-reply`

1. Classify reply as hot, warm, cold, or unsubscribe.
2. Update customer status.
3. Feed outcome back into future A/B selection.

## Required Demo Story

"Every SMB has abandoned intent: people who viewed products, clicked ads, added to cart, or chatted once and then went silent. REVARX AI automatically follows up with personalized recovery emails, tests professional vs friendly messaging, tracks replies, and learns which style converts by demographic and product category."
