import time

import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.title("Live Customer Board")
st.markdown("Track each abandoned customer from entry to email, waiting state, reply, classification, and A/B variant.")

st.markdown(
    """
    <style>
    .status-badge {
        display: inline-block;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 0.8rem;
        font-weight: 650;
        border: 1px solid rgba(255,255,255,0.14);
    }
    .s-new { background: rgba(20, 184, 166, .18); color: #5EEAD4; }
    .s-pending { background: rgba(245, 158, 11, .18); color: #FBBF24; }
    .s-hot { background: rgba(22, 163, 74, .18); color: #86EFAC; }
    .s-warm { background: rgba(202, 138, 4, .18); color: #FDE68A; }
    .s-cold { background: rgba(37, 99, 235, .18); color: #93C5FD; }
    .s-no_response { background: rgba(100, 116, 139, .20); color: #CBD5E1; }
    .s-email_failed, .s-unsubscribed { background: rgba(220, 38, 38, .18); color: #FCA5A5; }
    .timeline-row {
        border-left: 2px solid rgba(148, 163, 184, .45);
        padding-left: 14px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def status_label(status: str) -> str:
    labels = {
        "new": "New",
        "pending": "Email sent / waiting",
        "hot": "Replied - hot",
        "warm": "Replied - warm",
        "cold": "Replied - cold",
        "no_response": "No response",
        "email_failed": "Email failed",
        "unsubscribed": "Unsubscribed",
    }
    return labels.get(status or "new", status or "new")


def badge(status: str) -> str:
    status = status or "new"
    return f'<span class="status-badge s-{status}">{status_label(status)}</span>'


def fetch_leads():
    try:
        response = requests.get(f"{API_URL}/leads", timeout=4)
        if response.ok:
            return response.json(), False
    except Exception:
        pass

    return [
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
    ], True


def fetch_timeline(lead_id: int):
    try:
        response = requests.get(f"{API_URL}/leads/{lead_id}/timeline", timeout=5)
        if response.ok:
            return response.json()
    except Exception:
        pass
    return None


auto_refresh = st.toggle("Auto refresh every 10 seconds", value=False)
leads, is_mock = fetch_leads()
df = pd.DataFrame(leads)

if is_mock:
    st.info("Showing mock customer board because the API is offline.")

if df.empty:
    st.warning("No customers found yet.")
    st.stop()

status_counts = df["status"].fillna("new").value_counts().to_dict()
cols = st.columns(6)
for col, status in zip(cols, ["pending", "hot", "warm", "cold", "no_response", "unsubscribed"]):
    col.metric(status_label(status), status_counts.get(status, 0))

st.divider()

filter_col, search_col, refresh_col = st.columns([2, 2, 1])
with filter_col:
    statuses = sorted(df["status"].fillna("new").unique().tolist())
    selected_statuses = st.multiselect("Status", statuses, default=statuses)
with search_col:
    query = st.text_input("Search name, email, product, state")
with refresh_col:
    if st.button("Refresh"):
        st.rerun()

filtered = df[df["status"].fillna("new").isin(selected_statuses)]
if query:
    query_lower = query.lower()
    filtered = filtered[
        filtered.apply(lambda row: query_lower in " ".join(str(value).lower() for value in row.values), axis=1)
    ]

table_df = filtered.copy()
table_df["status_label"] = table_df["status"].map(status_label)
show_cols = [
    "id",
    "name",
    "email",
    "age",
    "gender",
    "state",
    "product_viewed",
    "product_category",
    "status_label",
    "variant",
    "msg_llm",
]
existing_cols = [col for col in show_cols if col in table_df.columns]
st.dataframe(table_df[existing_cols], width="stretch", hide_index=True)

st.divider()
st.subheader("Per-customer timeline")

for _, row in filtered.head(25).iterrows():
    lead_id = int(row["id"])
    title = f"{row.get('name')} - {row.get('product_viewed') or row.get('product_interest')} - {status_label(row.get('status'))}"
    with st.expander(title):
        meta1, meta2, meta3, meta4 = st.columns(4)
        meta1.markdown(badge(row.get("status")), unsafe_allow_html=True)
        meta2.metric("Variant", row.get("variant") or row.get("ab_preference") or "NA")
        meta3.metric("Age", row.get("age") if pd.notna(row.get("age")) else "NA")
        meta4.metric("State", row.get("state") or "NA")

        st.write(f"Email: {row.get('email')}")
        st.write(f"Product: {row.get('product_viewed') or row.get('product_interest')} ({row.get('product_category') or 'unknown'})")
        st.write(f"Notes: {row.get('notes') or 'NA'}")
        st.write(f"Message LLM: {row.get('msg_llm') or 'NA'}")

        if row.get("latest_reply"):
            st.write(f"Latest reply: {row.get('latest_reply')}")
            st.write(f"Reply classification: {row.get('classification')} via {row.get('reply_llm') or 'NA'}")

        timeline = fetch_timeline(lead_id)
        if timeline:
            for event in timeline.get("events", []):
                st.markdown(
                    f"""
                    <div class="timeline-row">
                        <strong>{event.get('label')}</strong><br>
                        <span style="color:#94A3B8;">{event.get('timestamp') or 'current'} | {event.get('status')}</span><br>
                        <span>{event.get('details') or ''}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Timeline API unavailable for this row.")

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            if st.button("Mark no response", key=f"no_response_{lead_id}"):
                try:
                    response = requests.post(f"{API_URL}/leads/{lead_id}/mark-no-response", timeout=10)
                    if response.ok:
                        st.success("Marked as no response.")
                        st.rerun()
                    else:
                        st.error(response.text)
                except Exception as exc:
                    st.error(f"Request failed: {exc}")
        with action_col2:
            reply_text = st.text_input("Simulate reply", key=f"reply_{lead_id}", placeholder="Yes, is there a discount?")
            if st.button("Classify reply", key=f"classify_{lead_id}") and reply_text:
                payload = {"lead_id": lead_id, "content": reply_text, "is_voice_note": False}
                try:
                    response = requests.post(f"{API_URL}/simulate-reply", json=payload, timeout=20)
                    if response.ok:
                        st.success(f"Classified as {response.json().get('reply_classification')}.")
                        st.rerun()
                    else:
                        st.error(response.text)
                except Exception as exc:
                    st.error(f"Request failed: {exc}")

if auto_refresh:
    time.sleep(10)
    st.rerun()
