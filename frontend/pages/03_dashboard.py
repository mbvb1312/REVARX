import requests
import streamlit as st
import sys
from pathlib import Path

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

API_URL = "http://localhost:8000"

st.title("Recovery Analytics")
st.markdown("Track what converts by A/B style, age group, gender, state, and product category.")


def get_json(path: str, fallback):
    try:
        response = requests.get(f"{API_URL}{path}", timeout=4)
        if response.ok:
            return response.json(), False
    except Exception:
        pass
    return fallback, True


fallback_funnel = {"tracked": 50, "sent": 42, "replied": 18, "recovered": 10, "hot": 5, "reply_rate": 42.9, "recovery_rate": 23.8, "estimated_revenue_recovered": 45000}
fallback_ab = {"variant_a_rate": 31.8, "variant_b_rate": 25.0, "winner": "A", "winner_label": "Professional"}
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
    st.info("Showing mock analytics because the API is offline or has no seeded data yet.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Abandoned sessions", funnel.get("tracked", 0))
col2.metric("Emails sent", funnel.get("sent", 0))
col3.metric("Replies", funnel.get("replied", 0), f"{funnel.get('reply_rate', 0)}%")
col4.metric("Re-engaged", funnel.get("recovered", 0), f"Winner: {ab.get('winner_label', 'Professional')}")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Recovery funnel")
    st.plotly_chart(funnel_chart(funnel.get("sent", 0), funnel.get("replied", 0), funnel.get("recovered", 0)), width="stretch")
with right:
    st.subheader("A/B conversion")
    st.plotly_chart(ab_bar_chart(ab.get("variant_a_rate", 0), ab.get("variant_b_rate", 0)), width="stretch")

left2, right2 = st.columns(2)
with left2:
    st.subheader("Customer status")
    st.plotly_chart(status_donut(demographics.get("status_counts", {})), width="stretch")
with right2:
    st.subheader("Tone performance")
    st.plotly_chart(tone_performance_chart(tone), width="stretch")

st.divider()
st.subheader("Demographic A/B learning")

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
