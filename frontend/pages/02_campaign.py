import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.title("Recovery Campaigns")
st.markdown("Preview Professional vs Friendly recovery copy, then queue a background email campaign.")

campaign_name = st.text_input("Campaign name", "Live E-commerce Recovery Campaign")
st.caption("Email is active now. WhatsApp and Telegram are reserved for the next phase.")

if "previews" not in st.session_state:
    st.session_state.previews = []

col_preview, col_launch = st.columns([1, 1])
with col_preview:
    if st.button("Generate A/B previews", type="secondary"):
        payload = {"campaign_name": campaign_name, "tone": "ab-test", "channel": "email"}
        try:
            response = requests.post(f"{API_URL}/generate-previews", json=payload, timeout=90)
            if response.ok:
                st.session_state.previews = response.json().get("previews", [])
                st.success("Generated A/B previews for recent customers.")
            else:
                st.error(response.text)
        except Exception as exc:
            st.error(f"Preview generation failed: {exc}")

with col_launch:
    if st.button("Queue campaign for unsent customers", type="primary"):
        payload = {"campaign_name": campaign_name, "tone": "ab-test", "channel": "email"}
        try:
            response = requests.post(f"{API_URL}/run-campaign", json=payload, timeout=30)
            if response.ok:
                data = response.json()
                st.success(f"Queued {data.get('queued', 0)} customers in campaign #{data.get('campaign_id')}.")
                st.info(data.get("message", "Campaign queued."))
            else:
                st.error(response.text)
        except Exception as exc:
            st.error(f"Campaign launch failed: {exc}")

st.divider()

if not st.session_state.previews:
    st.info("Generate previews to compare how Variant A and Variant B will look.")

for preview in st.session_state.previews:
    lead = preview.get("lead", {})
    title = f"{lead.get('name', '')} - {lead.get('product_viewed') or lead.get('product_interest', '')}"
    with st.expander(title, expanded=False):
        meta1, meta2, meta3 = st.columns(3)
        meta1.metric("Age", lead.get("age") or "NA")
        meta2.metric("Gender", lead.get("gender") or "NA")
        meta3.metric("State", lead.get("state") or "NA")

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Variant A: Professional")
            st.text_input("Subject A", preview.get("variant_a", {}).get("subject", ""), disabled=True, key=f"subject_a_{lead.get('id')}")
            st.text_area(
                "Message A",
                value=preview.get("variant_a", {}).get("message", ""),
                height=190,
                disabled=True,
                key=f"a_{lead.get('id')}",
            )
            st.caption(f"LLM: {preview.get('variant_a', {}).get('llm_used', 'REVARX Local Template')}")
        with col_b:
            st.subheader("Variant B: Friendly")
            st.text_input("Subject B", preview.get("variant_b", {}).get("subject", ""), disabled=True, key=f"subject_b_{lead.get('id')}")
            st.text_area(
                "Message B",
                value=preview.get("variant_b", {}).get("message", ""),
                height=190,
                disabled=True,
                key=f"b_{lead.get('id')}",
            )
            st.caption(f"LLM: {preview.get('variant_b', {}).get('llm_used', 'REVARX Local Template')}")
