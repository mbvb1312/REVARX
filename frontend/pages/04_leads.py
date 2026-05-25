import sys
import time
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.ui import (
    API_URL,
    escape,
    get_json,
    hero,
    inject_global_css,
    latest_lead_options,
    render_sidebar,
    status_badge,
    status_label,
)

inject_global_css()
render_sidebar()

hero(
    "Customer Board",
    "Follow every abandoned shopper from capture to outcome.",
    "Use this board for monitoring. Reply simulation now lives in Recovery Studio, right after add or upload, so testing stays in the same workflow.",
)


def fetch_timeline(lead_id: int):
    try:
        response = requests.get(f"{API_URL}/leads/{lead_id}/timeline", timeout=5)
        if response.ok:
            return response.json()
    except Exception:
        pass
    return None


fallback_leads = [
    {
        "id": 1,
        "name": "Priya Nair",
        "email": "priya@example.com",
        "age": 28,
        "gender": "female",
        "state": "Kerala",
        "product_viewed": "Nike Air Max 270",
        "product_category": "footwear",
        "status": "hot",
        "variant": "B",
        "message_status": "sent",
        "latest_reply": "Yes, is there a discount available?",
        "classification": "hot",
        "msg_llm": "Groq llama-3.1-8b-instant",
        "reply_llm": "Groq llama-3.1-8b-instant",
        "notes": "Viewed 3 times in the last week",
    },
    {
        "id": 2,
        "name": "Rahul Verma",
        "email": "rahul@example.com",
        "age": 34,
        "gender": "male",
        "state": "Maharashtra",
        "product_viewed": "Samsung Galaxy S24 Ultra",
        "product_category": "electronics",
        "status": "pending",
        "variant": "A",
        "message_status": "sent",
        "latest_reply": None,
        "classification": None,
        "msg_llm": "SambaNova Meta-Llama-3.3-70B-Instruct",
        "reply_llm": None,
        "notes": "Added to cart and abandoned at checkout",
    },
]

auto_refresh = st.toggle("Auto refresh every 10 seconds", value=False)
leads, is_mock = get_json("/leads", fallback_leads)
df = pd.DataFrame(leads)

if is_mock:
    st.info("Showing fallback customer data because the API is offline.")

if df.empty:
    st.warning("No customers found yet.")
    st.stop()

status_counts = df["status"].fillna("new").value_counts().to_dict()
metric_cols = st.columns(7)
for col, status in zip(metric_cols, ["new", "pending", "hot", "warm", "cold", "no_response", "unsubscribed"]):
    col.metric(status_label(status), status_counts.get(status, 0))

st.divider()

filter_col, search_col, refresh_col = st.columns([1.2, 1.8, 0.6])
with filter_col:
    statuses = sorted(df["status"].fillna("new").unique().tolist())
    selected_statuses = st.multiselect("Status", statuses, default=statuses)
with search_col:
    query = st.text_input("Search customer, email, product, state")
with refresh_col:
    if st.button("Refresh", width="stretch"):
        st.rerun()

filtered = df[df["status"].fillna("new").isin(selected_statuses)]
if query:
    query_lower = query.lower()
    filtered = filtered[
        filtered.apply(lambda row: query_lower in " ".join(str(value).lower() for value in row.values), axis=1)
    ]

table_df = filtered.copy()
table_df["status_label"] = table_df["status"].map(status_label)
table_df["product"] = table_df.apply(
    lambda row: row.get("product_viewed") or row.get("product_interest") or "",
    axis=1,
)
show_cols = ["id", "name", "email", "age", "gender", "state", "product", "product_category", "status_label", "variant", "msg_llm"]
existing_cols = [col for col in show_cols if col in table_df.columns]

st.subheader("Live roster")
st.dataframe(table_df[existing_cols], width="stretch", hide_index=True)

st.divider()
st.subheader("Customer inspector")

options = latest_lead_options(filtered.to_dict("records"))
if not options:
    st.warning("No customers match the current filters.")
    st.stop()

selected_label = st.selectbox("Select customer", list(options.keys()))
selected_id = options[selected_label]
selected = next((lead for lead in leads if int(lead.get("id")) == selected_id), {})

summary_left, summary_right = st.columns([0.85, 1.15])
with summary_left:
    st.markdown(
        f"""
        <div class="rx-card">
            <h3>{escape(selected.get('name'))}</h3>
            {status_badge(selected.get('status'))}
            <div style="height:10px"></div>
            <div class="rx-mini-label">Email</div>
            <div class="rx-mini-value">{escape(selected.get('email'))}</div>
            <div class="rx-mini-label">Demographics</div>
            <div class="rx-mini-value">{escape(selected.get('age'))} | {escape(selected.get('gender'))} | {escape(selected.get('state'))}</div>
            <div class="rx-mini-label">Product</div>
            <div class="rx-mini-value">{escape(selected.get('product_viewed') or selected.get('product_interest'))}</div>
            <div class="rx-mini-label">Category</div>
            <div class="rx-mini-value">{escape(selected.get('product_category'))}</div>
            <div class="rx-mini-label">Variant and model</div>
            <div class="rx-mini-value">{escape(selected.get('variant') or selected.get('ab_preference') or 'NA')} | {escape(selected.get('msg_llm') or 'NA')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if selected.get("latest_reply"):
        st.markdown(
            f"""
            <div class="rx-card-tight">
                <h3>Latest reply</h3>
                <p>{escape(selected.get('latest_reply'))}</p>
                <div class="rx-mini-label">Classification</div>
                <div class="rx-mini-value">{escape(selected.get('classification'))} via {escape(selected.get('reply_llm') or 'NA')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="rx-card-tight">
                <h3>No reply yet</h3>
                <p>Use Recovery Studio to simulate a reply or mark no response.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with summary_right:
    timeline = fetch_timeline(selected_id)
    if timeline:
        st.markdown('<div class="rx-card">', unsafe_allow_html=True)
        st.subheader("Journey timeline")
        for event in timeline.get("events", []):
            st.markdown(
                f"""
                <div class="rx-timeline-row">
                    <strong>{escape(event.get('label'))}</strong><br>
                    <span>{escape(event.get('timestamp') or 'current')} | {escape(event.get('status'))}</span>
                    <p>{escape(event.get('details') or '')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("Timeline API unavailable for this customer.")

st.page_link("pages/01_upload.py", label="Open Recovery Studio to test a reply")

if auto_refresh:
    time.sleep(10)
    st.rerun()
