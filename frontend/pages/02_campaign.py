import sys
from pathlib import Path

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.ui import API_URL, escape, hero, inject_global_css, render_sidebar

inject_global_css()
render_sidebar()

hero(
    "Campaign Lab",
    "Compare the two recovery voices before launching a batch.",
    "Preview professional and friendly variants side by side, then queue unsent customers for background email recovery.",
)

if "previews" not in st.session_state:
    st.session_state.previews = []

control_left, control_right = st.columns([1.2, 0.8])
with control_left:
    st.markdown(
        """
        <div class="rx-card-tight">
            <h3>Campaign controls</h3>
            <p>Use this when you want to send recovery emails to customers who are still new, cold, or previously failed.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    campaign_name = st.text_input("Campaign name", "Live E-commerce Recovery Campaign")
with control_right:
    st.markdown(
        """
        <div class="rx-card-tight">
            <h3>Active channel</h3>
            <p>Email is active. WhatsApp and Telegram links are available only as opt-in future-channel helpers.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

button_left, button_right = st.columns(2)
with button_left:
    if st.button("Generate A/B previews", type="secondary", width="stretch"):
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

with button_right:
    if st.button("Queue campaign for unsent customers", type="primary", width="stretch"):
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
    st.markdown(
        """
        <div class="rx-card">
            <h3>No previews yet</h3>
            <p>Generate previews to inspect the copy. This does not send anything.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

for preview in st.session_state.previews:
    lead = preview.get("lead", {})
    product = lead.get("product_viewed") or lead.get("product_interest") or ""
    with st.expander(f"{lead.get('name', '')} - {product}", expanded=False):
        meta1, meta2, meta3, meta4 = st.columns(4)
        meta1.metric("Age", lead.get("age") or "NA")
        meta2.metric("Gender", lead.get("gender") or "NA")
        meta3.metric("State", lead.get("state") or "NA")
        meta4.metric("Category", lead.get("product_category") or "NA")

        col_a, col_b = st.columns(2)
        with col_a:
            variant = preview.get("variant_a", {})
            st.markdown(
                f"""
                <div class="rx-card-tight">
                    <h3>Variant A: Professional</h3>
                    <p>{escape(variant.get('subject', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text_area(
                "Message A",
                value=variant.get("message", ""),
                height=190,
                disabled=True,
                key=f"a_{lead.get('id')}",
            )
            st.caption(f"LLM: {variant.get('llm_used', 'REVARX Local Template')}")
        with col_b:
            variant = preview.get("variant_b", {})
            st.markdown(
                f"""
                <div class="rx-card-tight">
                    <h3>Variant B: Friendly</h3>
                    <p>{escape(variant.get('subject', ''))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.text_area(
                "Message B",
                value=variant.get("message", ""),
                height=190,
                disabled=True,
                key=f"b_{lead.get('id')}",
            )
            st.caption(f"LLM: {variant.get('llm_used', 'REVARX Local Template')}")
