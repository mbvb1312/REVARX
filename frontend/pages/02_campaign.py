import requests
import streamlit as st

st.title("Run Campaign")

campaign_name = st.text_input("Campaign Name", "Reactivation Campaign Q2 2026")
tone = st.selectbox("Message Tone", ["friendly", "professional", "urgent"])
channel = st.selectbox("Send Channel", ["telegram", "email"])
st.caption("WhatsApp delivery will be added via a provider integration in a later phase.")

if "previews" not in st.session_state:
    st.session_state.previews = []

if st.button("Generate Message Previews (first 5 leads)"):
    payload = {"campaign_name": campaign_name, "tone": tone, "channel": channel}
    response = requests.post("http://localhost:8000/generate-previews", json=payload, timeout=30)
    if response.ok:
        st.session_state.previews = response.json().get("previews", [])
        st.success("Previews generated.")
    else:
        st.error("Preview generation failed. Is the FastAPI server running?")

for preview in st.session_state.previews:
    lead = preview.get("lead", {})
    with st.expander(f"Lead: {lead.get('name', '')} - {lead.get('product_interest', '')}"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("Variant A")
            st.text_area(
                "",
                value=preview.get("variant_a", {}).get("message", ""),
                height=150,
                key=f"a_{lead.get('id', '')}",
                disabled=True,
            )
            st.caption(f"⚡ **Generated via:** `{preview.get('variant_a', {}).get('llm_used', 'Google Gemini 2.0 Flash')}`")
        with col_b:
            st.markdown("Variant B")
            st.text_area(
                "",
                value=preview.get("variant_b", {}).get("message", ""),
                height=150,
                key=f"b_{lead.get('id', '')}",
                disabled=True,
            )
            st.caption(f"⚡ **Generated via:** `{preview.get('variant_b', {}).get('llm_used', 'Google Gemini 2.0 Flash')}`")

if st.button("Launch Campaign", type="primary"):
    payload = {"campaign_name": campaign_name, "tone": tone, "channel": channel}
    response = requests.post("http://localhost:8000/run-campaign", json=payload, timeout=60)
    if response.ok:
        data = response.json()
        st.success(f"Sent {data.get('sent', 0)} messages. Failed: {data.get('failed', 0)}")
    else:
        st.error("Campaign launch failed. Is the FastAPI server running?")
