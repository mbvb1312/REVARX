import sys
from pathlib import Path

import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.charts import (
    ab_bar_chart,
    demographic_ab_chart,
    funnel_chart,
    hourly_heatmap,
    status_donut,
    tone_performance_chart,
)
from frontend.components.ui import API_URL, get_json, hero, inject_global_css, render_sidebar

inject_global_css()
render_sidebar()

hero(
    "Analytics",
    "See which recovery style is actually working.",
    "Track the full funnel and inspect A/B performance by age group, gender, Indian state, and product category.",
)

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
    "variant_a_rate": 31.8,
    "variant_b_rate": 25.0,
    "winner": "A",
    "winner_label": "Professional",
    "variant_a_sent": 22,
    "variant_b_sent": 20,
}
fallback_hourly = [{"hour": hour, "count": 0 if hour not in [10, 11, 18, 20] else hour % 5 + 1} for hour in range(8, 23)]
fallback_tone = {"professional": 31.8, "friendly": 25.0}
fallback_demo = {
    "status_counts": {"pending": 12, "hot": 5, "warm": 5, "cold": 5, "no_response": 10, "email_failed": 0, "unsubscribed": 3, "new": 10, "total": 50},
    "age_group": [
        {"segment": "10-20", "variant_a_rate": 20, "variant_b_rate": 35},
        {"segment": "21-30", "variant_a_rate": 28, "variant_b_rate": 40},
        {"segment": "31-40", "variant_a_rate": 36, "variant_b_rate": 22},
        {"segment": "41-50", "variant_a_rate": 42, "variant_b_rate": 18},
    ],
    "gender": [
        {"segment": "female", "variant_a_rate": 30, "variant_b_rate": 36},
        {"segment": "male", "variant_a_rate": 35, "variant_b_rate": 24},
        {"segment": "other", "variant_a_rate": 25, "variant_b_rate": 25},
    ],
    "state": [
        {"segment": "Maharashtra", "variant_a_rate": 40, "variant_b_rate": 20},
        {"segment": "Karnataka", "variant_a_rate": 28, "variant_b_rate": 35},
        {"segment": "Kerala", "variant_a_rate": 32, "variant_b_rate": 30},
        {"segment": "Tamil Nadu", "variant_a_rate": 25, "variant_b_rate": 38},
    ],
    "product_category": [
        {"segment": "electronics", "variant_a_rate": 42, "variant_b_rate": 22},
        {"segment": "footwear", "variant_a_rate": 25, "variant_b_rate": 40},
        {"segment": "fashion", "variant_a_rate": 22, "variant_b_rate": 35},
    ],
}

funnel, mock_funnel = get_json("/analytics/funnel", fallback_funnel)
ab, mock_ab = get_json("/analytics/ab", fallback_ab)
hourly, _ = get_json("/analytics/hourly", fallback_hourly)
tone, _ = get_json("/analytics/tone", fallback_tone)
demographics, mock_demo = get_json("/analytics/demographics", fallback_demo)

if mock_funnel or mock_ab or mock_demo:
    st.info("Showing fallback analytics because the API is offline or has no seeded data yet.")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Sessions", funnel.get("tracked", 0))
col2.metric("Emails sent", funnel.get("sent", 0))
col3.metric("Reply rate", f"{funnel.get('reply_rate', 0)}%")
col4.metric("Re-engaged", funnel.get("recovered", 0), f"{funnel.get('recovery_rate', 0)}%")
col5.metric("A/B winner", ab.get("winner_label", "Professional"))

st.divider()

top_left, top_right = st.columns([1.05, 0.95])
with top_left:
    st.subheader("Funnel")
    st.plotly_chart(funnel_chart(funnel.get("sent", 0), funnel.get("replied", 0), funnel.get("recovered", 0)), width="stretch")
with top_right:
    st.subheader("Professional vs friendly")
    st.plotly_chart(ab_bar_chart(ab.get("variant_a_rate", 0), ab.get("variant_b_rate", 0)), width="stretch")
    st.markdown(
        f"""
        <div class="rx-note">
            Winner: <strong>{ab.get('winner_label', 'Professional')}</strong>.
            Professional sent: {ab.get('variant_a_sent', 0)}.
            Friendly sent: {ab.get('variant_b_sent', 0)}.
        </div>
        """,
        unsafe_allow_html=True,
    )

mid_left, mid_right = st.columns([0.95, 1.05])
with mid_left:
    st.subheader("Customer states")
    st.plotly_chart(status_donut(demographics.get("status_counts", {})), width="stretch")
with mid_right:
    st.subheader("Tone conversion")
    st.plotly_chart(tone_performance_chart(tone), width="stretch")

st.divider()
st.subheader("Demographic learning")
st.caption("These charts explain why the next customer may get Professional or Friendly copy.")

age_tab, gender_tab, state_tab, category_tab, hour_tab = st.tabs(["Age group", "Gender", "State", "Product category", "Reply hour"])

with age_tab:
    st.plotly_chart(demographic_ab_chart(demographics.get("age_group", []), "A/B by age group"), width="stretch")
with gender_tab:
    st.plotly_chart(demographic_ab_chart(demographics.get("gender", []), "A/B by gender"), width="stretch")
with state_tab:
    st.plotly_chart(demographic_ab_chart(demographics.get("state", []), "A/B by Indian state"), width="stretch")
with category_tab:
    st.plotly_chart(demographic_ab_chart(demographics.get("product_category", []), "A/B by product category"), width="stretch")
with hour_tab:
    st.plotly_chart(hourly_heatmap(hourly), width="stretch")
