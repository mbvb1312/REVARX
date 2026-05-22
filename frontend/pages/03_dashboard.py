import requests
import streamlit as st
from frontend.components.charts import funnel_chart, ab_bar_chart, hourly_heatmap, tone_performance_chart

st.title("📊 Reactivation Analytics Dashboard")
st.markdown("Real-time insights and autonomous learning outcomes for the outbound lead campaigns.")

# Robust helper to fetch analytics with local mock fallback
def fetch_analytics_data():
    try:
        funnel_res = requests.get("http://localhost:8000/analytics/funnel", timeout=2)
        ab_res = requests.get("http://localhost:8000/analytics/ab", timeout=2)
        hourly_res = requests.get("http://localhost:8000/analytics/hourly", timeout=2)
        tone_res = requests.get("http://localhost:8000/analytics/tone", timeout=2)

        if funnel_res.ok and ab_res.ok and hourly_res.ok and tone_res.ok:
            return {
                "funnel": funnel_res.json(),
                "ab": ab_res.json(),
                "hourly": hourly_res.json(),
                "tone": tone_res.json(),
                "is_mock": False
            }
    except Exception:
        pass
    
    # Elegant, realistic seed-data fallback for local sandbox execution
    return {
        "funnel": {"sent": 38, "replied": 13, "hot": 5, "reply_rate": 34.2},
        "ab": {"variant_a_rate": 34.8, "variant_b_rate": 20.0, "winner": "A"},
        "hourly": [
            {"hour": 9, "count": 1},
            {"hour": 10, "count": 5},
            {"hour": 11, "count": 4},
            {"hour": 12, "count": 2},
            {"hour": 13, "count": 0},
            {"hour": 14, "count": 0},
            {"hour": 15, "count": 0},
            {"hour": 16, "count": 0},
            {"hour": 17, "count": 1},
            {"hour": 18, "count": 0}
        ],
        "tone": {
            "friendly": 35.0,
            "professional": 22.0,
            "urgent": 15.0
        },
        "is_mock": True
    }

data = fetch_analytics_data()

if data["is_mock"]:
    st.warning("⚠️ Running in Sandbox/Demo mode (FastAPI backend is offline). Showing high-fidelity seed data.")

# Custom CSS for modern styling
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# Row 1: KPI metrics cards
col1, col2, col3, col4 = st.columns(4)
funnel = data["funnel"]
ab = data["ab"]

col1.metric("Outreach Messages Sent", f"{funnel.get('sent', 0)}")
col2.metric("Replies Received", f"{funnel.get('replied', 0)}")
col3.metric("Hot Leads Escalated 🔥", f"{funnel.get('hot', 0)}", delta="New Alerts Active")
col4.metric("Average Reply Rate", f"{funnel.get('reply_rate', 0)}%", delta=f"Winner A/B: Variant {ab.get('winner', 'A')}")

st.divider()

# Row 2: Funnel & A/B Results side-by-side
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Campaign Conversion Funnel")
    st.caption("Outreach delivery leading to high-intent conversations.")
    st.plotly_chart(
        funnel_chart(funnel.get("sent", 0), funnel.get("replied", 0), funnel.get("hot", 0)), 
        use_container_width=True
    )

with col_right:
    st.subheader("Variant A/B Learning Curve")
    winner_var = ab.get("winner", "A")
    st.success(f"🏆 **Outbound Learning Complete**: Variant {winner_var} is winning! We recommend shifting 80% weight here.")
    st.plotly_chart(
        ab_bar_chart(ab.get("variant_a_rate", 0), ab.get("variant_b_rate", 0)), 
        use_container_width=True
    )

st.divider()

# Row 3: Hourly distribution & Tone efficacy
col_bottom_left, col_bottom_right = st.columns(2)

with col_bottom_left:
    st.subheader("Conversion by Hour of Day")
    st.caption("Visualizing the optimal send-time slot based on response rates.")
    st.plotly_chart(
        hourly_heatmap(data["hourly"]), 
        use_container_width=True
    )

with col_bottom_right:
    st.subheader("Efficacy of Tone styles")
    st.caption("Analyzing reply probability by communication tone style.")
    st.plotly_chart(
        tone_performance_chart(data["tone"]), 
        use_container_width=True
    )
