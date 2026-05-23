import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="REVARX AI",
    page_icon="RX",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
    .rx-panel {
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 8px;
        padding: 16px;
        background: rgba(15, 23, 42, 0.56);
    }
    .rx-kpi {
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 8px;
        padding: 14px;
        background: rgba(2, 6, 23, 0.38);
        min-height: 118px;
    }
    .rx-kpi p { margin: 0; color: #94A3B8; font-size: 0.78rem; text-transform: uppercase; }
    .rx-kpi h2 { margin: 6px 0 0 0; font-size: 1.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## REVARX AI")
    st.caption("E-commerce recovery agent")
    st.divider()
    st.page_link("app.py", label="Executive Summary")
    st.page_link("pages/01_upload.py", label="Live Demo: Add Customers")
    st.page_link("pages/02_campaign.py", label="Recovery Campaigns")
    st.page_link("pages/03_dashboard.py", label="Analytics")
    st.page_link("pages/04_leads.py", label="Live Customer Board")


def get_json(path: str, fallback):
    try:
        response = requests.get(f"{API_URL}{path}", timeout=3)
        if response.ok:
            return response.json(), False
    except Exception:
        pass
    return fallback, True


fallback_funnel = {
    "tracked": 50,
    "sent": 42,
    "replied": 18,
    "recovered": 10,
    "hot": 5,
    "reply_rate": 42.9,
    "estimated_revenue_recovered": 45000,
}
funnel, is_mock = get_json("/analytics/funnel", fallback_funnel)

st.title("REVARX AI")
st.markdown("### E-commerce browse and cart abandonment recovery for small and medium businesses.")

mode_col, summary_col = st.columns([1, 2])
with mode_col:
    st.markdown('<div class="rx-panel">', unsafe_allow_html=True)
    st.subheader("Demo modes")
    st.write("Mock mode shows seeded e-commerce customers and analytics.")
    st.write("Live mode lets you upload customers or add one manually, then sends recovery emails.")
    st.markdown("</div>", unsafe_allow_html=True)
with summary_col:
    st.markdown('<div class="rx-panel">', unsafe_allow_html=True)
    st.subheader("The problem")
    st.write(
        "Businesses lose warm intent when shoppers click ads, view products, add to cart, or chat once and then disappear. "
        "REVARX AI follows up with personalized email, tests professional vs friendly copy, tracks replies, and learns what works by demographic and product category."
    )
    st.markdown("</div>", unsafe_allow_html=True)

if is_mock:
    st.info("Backend is offline or not seeded yet, so this screen is showing mock recovery metrics.")

st.divider()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="rx-kpi"><p>Abandoned sessions tracked</p><h2>{funnel.get("tracked", 0)}</h2></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="rx-kpi"><p>Recovery emails sent</p><h2>{funnel.get("sent", 0)}</h2></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="rx-kpi"><p>Customers re-engaged</p><h2>{funnel.get("recovered", 0)}</h2></div>', unsafe_allow_html=True)
with col4:
    st.markdown(
        f'<div class="rx-kpi"><p>Estimated revenue recovered</p><h2>Rs {funnel.get("estimated_revenue_recovered", 0):,}</h2></div>',
        unsafe_allow_html=True,
    )

st.divider()

st.subheader("Live reply simulator")
st.caption("Use this after sending a live or seeded recovery email to update the customer status and A/B learning history.")

leads, leads_mock = get_json("/leads", [],)
if leads:
    lead_map = {f"{lead['id']} - {lead['name']} - {lead.get('product_viewed') or lead.get('product_interest')}": lead["id"] for lead in leads}
    selected = st.selectbox("Customer", list(lead_map.keys()))
    preset = st.selectbox(
        "Reply",
        [
            "Yes, is there a discount available if I buy today?",
            "Maybe next week. Please remind me again.",
            "Already bought from Amazon.",
            "Stop emailing me.",
            "Type my own reply",
        ],
    )
    reply_text = st.text_area("Custom reply", "" if preset != "Type my own reply" else "Can you send the checkout link again?")
    content = reply_text if preset == "Type my own reply" else preset

    if st.button("Simulate reply", type="primary"):
        payload = {"lead_id": lead_map[selected], "content": content, "is_voice_note": False}
        try:
            response = requests.post(f"{API_URL}/simulate-reply", json=payload, timeout=20)
            if response.ok:
                data = response.json()
                st.success(f"Reply classified as {data.get('reply_classification')} using {data.get('classifier_llm_used')}.")
            else:
                st.error(response.text)
        except Exception as exc:
            st.error(f"Could not reach API: {exc}")
else:
    st.warning("No live customers available yet. Seed data or add a customer from the Live Demo page.")
