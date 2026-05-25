import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.charts import ab_bar_chart, funnel_chart, status_donut
from frontend.components.ui import get_json, hero, inject_global_css, render_sidebar, status_label

st.set_page_config(
    page_title="REVARX AI",
    page_icon="RX",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()
render_sidebar()

fallback_funnel = {
    "tracked": 50,
    "sent": 42,
    "replied": 18,
    "recovered": 10,
    "hot": 5,
    "reply_rate": 42.9,
    "recovery_rate": 23.8,
    "estimated_revenue_recovered": 45000,
}
fallback_ab = {
    "variant_a_rate": 18.2,
    "variant_b_rate": 30.0,
    "variant_a_sent": 22,
    "variant_b_sent": 20,
    "winner": "B",
    "winner_label": "Friendly",
}
fallback_demographics = {
    "status_counts": {
        "pending": 12,
        "hot": 5,
        "warm": 5,
        "cold": 5,
        "no_response": 10,
        "email_failed": 0,
        "unsubscribed": 3,
        "new": 10,
        "total": 50,
    }
}

funnel, mock_funnel = get_json("/analytics/funnel", fallback_funnel)
ab, _ = get_json("/analytics/ab", fallback_ab)
demographics, _ = get_json("/analytics/demographics", fallback_demographics)
leads, leads_mock = get_json("/leads", [])

hero(
    "Overview",
    "Recover abandoned shoppers before the intent goes cold.",
    "REVARX AI sends personalized recovery emails, chooses the best A/B tone for each customer, tracks replies, and learns which style converts across demographics and product categories.",
)

if mock_funnel or leads_mock:
    st.info("The backend is offline or still starting. Showing seeded-style fallback data where needed.")

metric_cols = st.columns(5)
metric_cols[0].metric("Tracked sessions", funnel.get("tracked", 0))
metric_cols[1].metric("Emails sent", funnel.get("sent", 0))
metric_cols[2].metric("Replies", funnel.get("replied", 0), f"{funnel.get('reply_rate', 0)}%")
metric_cols[3].metric("Re-engaged", funnel.get("recovered", 0), f"{funnel.get('recovery_rate', 0)}%")
metric_cols[4].metric("Revenue estimate", f"Rs {funnel.get('estimated_revenue_recovered', 0):,}")

st.markdown("#### Recovery workflow")
st.markdown(
    """
    <div class="rx-flow">
        <div class="rx-flow-step"><strong>1. Capture intent</strong><span>Add one shopper or upload CSV/TXT abandoned sessions.</span></div>
        <div class="rx-flow-step"><strong>2. Pick A/B tone</strong><span>Professional or friendly is selected from weighted history.</span></div>
        <div class="rx-flow-step"><strong>3. Send email</strong><span>Groq, SambaNova, or fallback copy powers personalized recovery.</span></div>
        <div class="rx-flow-step"><strong>4. Learn outcome</strong><span>Reply or no response updates future selection criteria.</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

chart_left, chart_right = st.columns([1.1, 0.9])
with chart_left:
    st.subheader("Recovery funnel")
    st.plotly_chart(
        funnel_chart(funnel.get("sent", 0), funnel.get("replied", 0), funnel.get("recovered", 0)),
        width="stretch",
    )
with chart_right:
    st.subheader("A/B winner")
    st.plotly_chart(ab_bar_chart(ab.get("variant_a_rate", 0), ab.get("variant_b_rate", 0)), width="stretch")
    st.markdown(
        f"""
        <div class="rx-note">
            Current weighted winner: <strong>{ab.get('winner_label', 'Friendly')}</strong>.
            A sent: {ab.get('variant_a_sent', 0)} | B sent: {ab.get('variant_b_sent', 0)}
        </div>
        """,
        unsafe_allow_html=True,
    )

status_left, activity_right = st.columns([0.9, 1.1])
with status_left:
    st.subheader("Customer status mix")
    st.plotly_chart(status_donut(demographics.get("status_counts", {})), width="stretch")
with activity_right:
    st.subheader("Recent recovery activity")
    if leads:
        recent = pd.DataFrame(leads[:8])
        recent["product"] = recent.apply(
            lambda row: row.get("product_viewed") or row.get("product_interest") or "",
            axis=1,
        )
        recent["state_label"] = recent["status"].map(status_label)
        display_cols = ["id", "name", "product", "state", "variant", "state_label"]
        existing_cols = [col for col in display_cols if col in recent.columns]
        st.dataframe(recent[existing_cols], width="stretch", hide_index=True)
    else:
        st.warning("No customers found. Seed data or add a customer in Recovery Studio.")

st.divider()

cta_left, cta_right = st.columns(2)
with cta_left:
    st.markdown(
        """
        <div class="rx-card">
            <h3>Run a live test</h3>
            <p>Add one customer, send the recovery email, then simulate their reply in the same workspace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/01_upload.py", label="Open Recovery Studio")
with cta_right:
    st.markdown(
        """
        <div class="rx-card">
            <h3>Watch the learning loop</h3>
            <p>Review demographic charts and see which tone wins by age, gender, state, and product category.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/03_dashboard.py", label="Open Analytics")
