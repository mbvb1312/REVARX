# TASK TRACKER

## REVARX AI: E-commerce Recovery Agent

## Completed

- [x] Reframed app from generic sales follow-up to e-commerce browse/cart abandonment recovery.
- [x] Added customer demographics: age, gender, state, product category, product viewed.
- [x] Added all 28 Indian states to the live customer form.
- [x] Implemented single-customer instant recovery flow.
- [x] Implemented CSV and TXT bulk upload.
- [x] Queued bulk recovery emails in background.
- [x] Changed A/B test to Variant A professional vs Variant B friendly.
- [x] Implemented weighted A/B recommendation by demographic and product category.
- [x] Made Groq primary LLM.
- [x] Made SambaNova fallback.
- [x] Kept Gemini as optional fallback only.
- [x] Added local template and heuristic fallback.
- [x] Added reply classification: hot, warm, cold, unsubscribe.
- [x] Added no-response marking.
- [x] Added per-customer timeline endpoint.
- [x] Added demographic analytics endpoints.
- [x] Rewrote seed data for e-commerce products and Indian demographics.
- [x] Rewrote Streamlit home page.
- [x] Rewrote live add/upload page.
- [x] Rewrote campaign preview page.
- [x] Rewrote analytics dashboard.
- [x] Rewrote live customer board.
- [x] Updated requirements.
- [x] Updated README and handoff docs.

## Still Future Scope

- [ ] WhatsApp outbound integration.
- [ ] Telegram outbound recovery message integration for production.
- [ ] Real email open tracking via pixel/webhook.
- [ ] Real unsubscribe link/webhook.
- [ ] Revenue attribution from store order events.
- [ ] Production database migration system.

## Verification

- [x] Requirements installed in project venv.
- [x] Python compile check passed.
- [x] Seed data smoke test passed.
- [x] FastAPI smoke test passed.
- [x] Streamlit server started.
- [x] FastAPI server started.
