# frontend/ — README for AI Coding Agents

## What This Folder Does
This folder contains the entire Streamlit web interface.
- Multi-page Streamlit app
- 4 pages: Upload Leads, Run Campaign, Analytics Dashboard, Lead Status Board
- Calls FastAPI backend via `httpx` or `requests`
- Uses Plotly for charts
- No AI/LLM calls made directly from here

---

## File Structure

```
frontend/
├── app.py                    ← Main Streamlit entrypoint (run this with `streamlit run`)
├── pages/
│   ├── 01_upload.py          ← CSV upload + lead table
│   ├── 02_campaign.py        ← Campaign settings + message preview + send
│   ├── 03_dashboard.py       ← Analytics dashboard (the "wow" screen)
│   └── 04_leads.py           ← Lead status board
└── components/
    └── charts.py             ← Reusable Plotly chart functions
```

---

## How to Run
```bash
# From project root
streamlit run frontend/app.py
```

---

## app.py — Main App

```python
import streamlit as st

st.set_page_config(
    page_title="Dead Lead Reactivation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Dead Lead Reactivation Agent")
st.markdown("**AI-powered outreach to reactivate cold leads — built for Steps AI Hackathon 2026**")

# Key metrics on home page (fetch from API)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Leads", "50")
with col2:
    st.metric("Messages Sent", "38")
with col3:
    st.metric("Hot Leads", "5", delta="↑ from 0")
with col4:
    st.metric("Reply Rate", "34%", delta="A beats B by 13%")

st.info("Use the sidebar to navigate between pages.")
```

---

## pages/01_upload.py — CSV Upload

```python
import streamlit as st
import pandas as pd
import requests

st.title("📥 Upload Leads")
st.markdown("Upload a CSV of cold leads. Required columns: `name`, `email`, `product_interest`, `last_contact_date`, `notes`")

# Sample CSV download
sample_data = pd.DataFrame({
    "name": ["Priya Sharma", "Rahul Verma"],
    "email": ["priya@example.com", "rahul@example.com"],
    "product_interest": ["CRM Software", "Inventory Management"],
    "last_contact_date": ["2024-11-01", "2024-10-15"],
    "notes": ["Attended webinar", "Trial expired"],
    "telegram_chat_id": ["", ""]
})
st.download_button("📄 Download Sample CSV", sample_data.to_csv(index=False), "sample_leads.csv", "text/csv")

uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Preview: {len(df)} leads found")
    st.dataframe(df, use_container_width=True)
    
    if st.button("✅ Import Leads to Database"):
        # Call FastAPI: POST /upload-leads
        files = {"file": uploaded_file.getvalue()}
        response = requests.post("http://localhost:8000/upload-leads", files=files)
        if response.ok:
            data = response.json()
            st.success(f"Imported {data['inserted']} leads. Skipped {data['skipped']} duplicates.")
        else:
            st.error("Import failed. Is the FastAPI server running?")
```

---

## pages/02_campaign.py — Campaign Settings

Key UI elements to build:
```python
# Tone selector
tone = st.selectbox("Message Tone", ["friendly", "professional", "urgent"])

# Channel selector
channel = st.selectbox("Send Channel", ["telegram", "email"])

# Campaign name
campaign_name = st.text_input("Campaign Name", "Reactivation Campaign Q2 2026")

# Generate previews
if st.button("🔍 Generate Message Previews (first 5 leads)"):
    # Call POST /generate-previews
    # Show 5 expandable cards, each with Variant A and Variant B side by side
    pass

# Launch campaign
if st.button("🚀 Launch Campaign", type="primary"):
    # Call POST /run-campaign
    # Show progress bar
    # Show success summary
    pass
```

**Message Preview Card Design:**
```python
# For each preview lead:
with st.expander(f"Lead: {lead['name']} — {lead['product_interest']}"):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Variant A**")
        st.text_area("", value=variant_a['message'], height=150, key=f"a_{lead['id']}", disabled=True)
    with col_b:
        st.markdown("**Variant B**")
        st.text_area("", value=variant_b['message'], height=150, key=f"b_{lead['id']}", disabled=True)
```

---

## pages/03_dashboard.py — Analytics (THE MOST IMPORTANT PAGE)

This page wins the demo. Make it look polished.

```python
import streamlit as st
import plotly.graph_objects as go
from frontend.components.charts import funnel_chart, ab_bar_chart, hourly_heatmap
import requests

st.title("📊 Analytics Dashboard")

# Fetch data from API
funnel_data = requests.get("http://localhost:8000/analytics/funnel").json()
ab_data = requests.get("http://localhost:8000/analytics/ab").json()

# Row 1: Metric cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Messages Sent", funnel_data["sent"])
col2.metric("Replies Received", funnel_data["replied"])
col3.metric("Hot Leads 🔥", funnel_data["hot"])
col4.metric("Reply Rate", f"{funnel_data['reply_rate']}%")

st.divider()

# Row 2: Funnel + A/B side by side
col1, col2 = st.columns(2)
with col1:
    st.subheader("Campaign Funnel")
    st.plotly_chart(funnel_chart(funnel_data["sent"], funnel_data["replied"], funnel_data["hot"]), use_container_width=True)

with col2:
    st.subheader("A/B Test Results")
    winner = "A" if ab_data["variant_a_rate"] > ab_data["variant_b_rate"] else "B"
    st.success(f"🏆 Variant {winner} is winning!")
    st.plotly_chart(ab_bar_chart(ab_data["variant_a_rate"], ab_data["variant_b_rate"]), use_container_width=True)

# Row 3: Hourly reply distribution
st.subheader("Best Time to Send (when replies come in)")
hourly_data = requests.get("http://localhost:8000/analytics/hourly").json()
st.plotly_chart(hourly_heatmap(hourly_data), use_container_width=True)
```

---

## components/charts.py — Plotly Chart Functions

```python
import plotly.graph_objects as go

def funnel_chart(sent: int, replied: int, hot: int) -> go.Figure:
    fig = go.Figure(go.Funnel(
        y=["Messages Sent", "Replies Received", "Hot Leads"],
        x=[sent, replied, hot],
        textinfo="value+percent initial",
        marker=dict(color=["#636EFA", "#EF553B", "#00CC96"])
    ))
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=300)
    return fig

def ab_bar_chart(a_rate: float, b_rate: float) -> go.Figure:
    fig = go.Figure(data=[
        go.Bar(name="Variant A", x=["Reply Rate"], y=[a_rate], marker_color="#636EFA"),
        go.Bar(name="Variant B", x=["Reply Rate"], y=[b_rate], marker_color="#EF553B")
    ])
    fig.update_layout(
        yaxis_title="Reply Rate (%)",
        barmode="group",
        margin=dict(l=0, r=0, t=0, b=0),
        height=300
    )
    return fig

def hourly_heatmap(hourly_data: list) -> go.Figure:
    hours = [str(h["hour"]) + ":00" for h in hourly_data]
    counts = [h["count"] for h in hourly_data]
    fig = go.Figure(data=[go.Bar(x=hours, y=counts, marker_color="#00CC96")])
    fig.update_layout(
        xaxis_title="Hour of Day",
        yaxis_title="Replies",
        margin=dict(l=0, r=0, t=0, b=0),
        height=300
    )
    return fig
```

---

## pages/04_leads.py — Lead Status Board

```python
import streamlit as st
import requests
import pandas as pd

st.title("👥 Lead Status Board")

leads = requests.get("http://localhost:8000/leads").json()
df = pd.DataFrame(leads)

# Status summary cards
hot = len(df[df["status"] == "hot"])
warm = len(df[df["status"] == "warm"])
cold = len(df[df["status"] == "cold"])
unsub = len(df[df["status"] == "unsubscribed"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔥 Hot", hot)
col2.metric("🟡 Warm", warm)
col3.metric("🔵 Cold", cold)
col4.metric("🚫 Unsubscribed", unsub)

st.divider()

# Filter
status_filter = st.multiselect("Filter by status", ["hot", "warm", "cold", "unsubscribed"], default=["hot", "warm", "cold"])
filtered = df[df["status"].isin(status_filter)]
st.dataframe(filtered[["name", "email", "product_interest", "status", "last_contact_date"]], use_container_width=True)
```

---

## Dependencies Used in This Folder
```
streamlit==1.35.0
plotly==5.22.0
pandas==2.2.2
requests==2.31.0
```

## What NOT to Do Here
- Do NOT call Gemini or Groq APIs directly from Streamlit pages
- All AI operations go through the FastAPI backend
- Do NOT use `st.experimental_rerun()` — deprecated, use `st.rerun()`
- Keep charts in `components/charts.py`, not inline in page files

---

*See `AGENT_HANDOFF.md` for current task status.*
