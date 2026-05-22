import requests
import streamlit as st

st.set_page_config(
    page_title="Dead Lead Reactivation Agent",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Dead Lead Reactivation Agent")
st.markdown("AI-powered outreach to reactivate cold leads.")


def _safe_get(url: str, fallback: dict) -> dict:
    try:
        response = requests.get(url, timeout=5)
        if response.ok:
            return response.json()
    except Exception:
        pass
    return fallback


funnel = _safe_get(
    "http://localhost:8000/analytics/funnel",
    {"sent": 0, "replied": 0, "hot": 0, "reply_rate": 0.0},
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Leads", "50")
col2.metric("Messages Sent", str(funnel.get("sent", 0)))
col3.metric("Hot Leads", str(funnel.get("hot", 0)))
col4.metric("Reply Rate", f"{funnel.get('reply_rate', 0)}%")

st.info("Use the sidebar to navigate between pages.")
