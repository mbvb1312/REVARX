import requests
import streamlit as st
import pandas as pd

st.title("👥 Lead Status Board")
st.markdown("Monitor individual re-engagement stages, sentiment classifications, and full conversation histories.")

# Robust lead data fetcher with high-fidelity mock fallbacks
def fetch_leads_data():
    try:
        res = requests.get("http://localhost:8000/leads", timeout=2)
        if res.ok:
            return res.json(), False
    except Exception:
        pass
    
    # Beautiful mock data aligned with seed_data.py
    mock_leads = [
        {
            "id": 1,
            "name": "Priya Sharma",
            "email": "priya.sharma@example.com",
            "product_interest": "CRM Software",
            "status": "hot",
            "last_contact_date": "2026-03-12",
            "latest_reply": "Yes, I'm interested. Let's schedule a call this week.",
            "classification": "hot",
            "outreach_sent": "Hi Priya Sharma, just checking in about our CRM Software. We noticed you registered for our webinar a few months back. Would you be open to a quick 5-minute chat this Thursday?",
            "variant": "A",
            "notes": "Attended webinar",
            "msg_llm": "Google Gemini 2.0 Flash",
            "reply_llm": "Groq LLaMA-3.1 8B"
        },
        {
            "id": 2,
            "name": "Rahul Verma",
            "email": "rahul.verma@example.com",
            "product_interest": "Inventory Management",
            "status": "warm",
            "last_contact_date": "2026-04-05",
            "latest_reply": "Maybe next month. Please check back later.",
            "classification": "warm",
            "outreach_sent": "Hi Rahul, following up on your inquiry about our Inventory Management suite. Has your team had a chance to look over the trial?",
            "variant": "B",
            "notes": "Trial expired",
            "msg_llm": "Groq LLaMA-3.1 8B",
            "reply_llm": "Google Gemini 2.0 Flash"
        },
        {
            "id": 3,
            "name": "Ananya Rao",
            "email": "ananya.rao@example.com",
            "product_interest": "HR Platform",
            "status": "cold",
            "last_contact_date": "2026-02-18",
            "latest_reply": "Not interested right now.",
            "classification": "cold",
            "outreach_sent": "Hi Ananya, hope you are doing well! Just wanted to share our new automated HR features that integrate with your pipeline. Do you have a quick minute?",
            "variant": "A",
            "notes": "Requested pricing",
            "msg_llm": "Google Gemini 2.0 Flash",
            "reply_llm": "Steps AI Local Heuristics"
        },
        {
            "id": 4,
            "name": "Arjun Iyer",
            "email": "arjun.iyer@example.com",
            "product_interest": "E-commerce Enablement",
            "status": "unsubscribed",
            "last_contact_date": "2026-01-22",
            "latest_reply": "Please stop reaching out for now.",
            "classification": "unsubscribe",
            "outreach_sent": "Hi Arjun, wanted to check if you are still looking to launch your online Shopify store?",
            "variant": "B",
            "notes": "Asked about integration",
            "msg_llm": "Steps AI Local Sandbox",
            "reply_llm": "Steps AI Local Sandbox"
        },
        {
            "id": 5,
            "name": "Meera Nair",
            "email": "meera.nair@example.com",
            "product_interest": "Productivity Suite",
            "status": "hot",
            "last_contact_date": "2026-03-29",
            "latest_reply": "This looks great. Can you share pricing and next steps?",
            "classification": "hot",
            "outreach_sent": "Hi Meera, checking in on our Productivity Suite. Let me know if you would like me to set up a personalized demo.",
            "variant": "A",
            "notes": "Requested demo call",
            "msg_llm": "Google Gemini 2.0 Flash",
            "reply_llm": "Groq LLaMA-3.1 8B"
        }
    ]
    # Expand to make up 50 dummy leads for metric display
    for i in range(6, 51):
        status = "cold"
        if i % 7 == 0:
            status = "unsubscribed"
        elif i % 5 == 0:
            status = "warm"
        mock_leads.append({
            "id": i,
            "name": f"Lead {i}",
            "email": f"lead{i}@example.com",
            "product_interest": "Productivity Suite" if i % 2 == 0 else "CRM Software",
            "status": status,
            "last_contact_date": "2026-04-10",
            "latest_reply": None,
            "classification": None,
            "outreach_sent": "Hi there, just following up!",
            "variant": "A" if i % 2 == 0 else "B",
            "notes": "Imported via CSV"
        })
    return mock_leads, True

leads, is_mock = fetch_leads_data()
df = pd.DataFrame(leads)

if is_mock:
    st.warning("⚠️ Running in Sandbox/Demo mode (FastAPI backend is offline). Showing high-fidelity seed lists.")

# Status aggregate cards
hot_count = len(df[df["status"] == "hot"])
warm_count = len(df[df["status"] == "warm"])
cold_count = len(df[df["status"] == "cold"])
unsub_count = len(df[df["status"] == "unsubscribed"])

# Render KPI metric badges
st.markdown("""
<style>
.badge-card {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    text-align: center;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="badge-card" style="background-color: rgba(239, 85, 59, 0.15);"><h3>🔥 Hot Leads</h3><h1>' + str(hot_count) + '</h1></div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="badge-card" style="background-color: rgba(255, 193, 7, 0.15);"><h3>🟡 Warm Leads</h3><h1>' + str(warm_count) + '</h1></div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="badge-card" style="background-color: rgba(99, 110, 250, 0.15);"><h3>🔵 Cold Leads</h3><h1>' + str(cold_count) + '</h1></div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="badge-card" style="background-color: rgba(127, 127, 127, 0.15);"><h3>🚫 Unsubscribed</h3><h1>' + str(unsub_count) + '</h1></div>', unsafe_allow_html=True)

st.write("")
st.divider()

# Interactive Filters
col_search, col_status = st.columns([2, 2])
with col_search:
    search_query = st.text_input("🔍 Search Leads by Name or Email", "")
with col_status:
    status_filter = st.multiselect(
        "Filter by Engagement Status", 
        ["hot", "warm", "cold", "unsubscribed"], 
        default=["hot", "warm", "cold"]
    )

# Filter Dataframe
filtered_df = df[df["status"].isin(status_filter)]
if search_query:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search_query, case=False, na=False) |
        filtered_df["email"].str.contains(search_query, case=False, na=False)
    ]

# Display Data Table
st.subheader("Lead Roster")
st.caption("Click column headers to sort leads. View all active engagement channels.")
display_cols = ["id", "name", "email", "product_interest", "status", "last_contact_date"]
st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

st.divider()

# Rich Expandable Conversation Details
st.subheader("💬 AI Conversation Inspector")
st.caption("Select a lead from the dropdown below to review their full outreach timeline, personalization rules, and sentiment tags.")

conversational_leads = filtered_df[filtered_df["latest_reply"].notna()]
if not conversational_leads.empty:
    selected_lead_name = st.selectbox(
        "Select active lead history to inspect:", 
        conversational_leads["name"].unique()
    )
    
    lead_detail = conversational_leads[conversational_leads["name"] == selected_lead_name].iloc[0]
    
    col_lead, col_conv = st.columns([1, 2])
    with col_lead:
        st.info("📋 Lead Metadata")
        st.markdown(f"**Name:** {lead_detail['name']}")
        st.markdown(f"**Email:** {lead_detail['email']}")
        st.markdown(f"**Product Interest:** {lead_detail['product_interest']}")
        st.markdown(f"**Original Notes:** *{lead_detail['notes']}*")
        st.markdown(f"**Reactivation Status:** `{lead_detail['status'].upper()}`")

    with col_conv:
        st.success("🤖 Re-engagement Outreach Timeline")
        st.markdown(f"**Outreach Message Sent (A/B Variant {lead_detail.get('variant', 'A')}):**")
        st.write(lead_detail.get("outreach_sent", "N/A"))
        st.caption(f"⚡ **Outreach LLM Used:** `{lead_detail.get('msg_llm', 'Google Gemini 2.0 Flash')}`")
        
        st.markdown("---")
        
        st.markdown(f"**Customer Reply Received:**")
        st.write(f"*{lead_detail['latest_reply']}*")
        
        st.markdown("---")
        classification = lead_detail.get("classification", "cold")
        st.markdown(f"**Sentiment Classification:** `{classification.upper()}`")
        st.caption(f"⚡ **Classifier LLM Used:** `{lead_detail.get('reply_llm', 'Google Gemini 2.0 Flash')}`")
else:
    st.write("No leads in the current filtered set have conversations/replies to inspect.")
