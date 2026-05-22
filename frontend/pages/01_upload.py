import pandas as pd
import requests
import streamlit as st

st.title("Upload Leads")
st.markdown(
    "Upload a CSV of cold leads. Required columns: name, email, product_interest, "
    "last_contact_date, notes. Optional: telegram_chat_id."
)

sample_data = pd.DataFrame(
    {
        "name": ["Priya Sharma", "Rahul Verma"],
        "email": ["priya@example.com", "rahul@example.com"],
        "product_interest": ["CRM Software", "Inventory Management"],
        "last_contact_date": ["2024-11-01", "2024-10-15"],
        "notes": ["Attended webinar", "Trial expired"],
        "telegram_chat_id": ["", ""],
    }
)

st.download_button(
    "Download Sample CSV",
    sample_data.to_csv(index=False),
    "sample_leads.csv",
    "text/csv",
)

uploaded_file = st.file_uploader("Upload your leads CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Preview: {len(df)} leads found")
    st.dataframe(df, use_container_width=True)

    if st.button("Import Leads to Database"):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "text/csv",
            )
        }
        response = requests.post("http://localhost:8000/upload-leads", files=files, timeout=10)
        if response.ok:
            data = response.json()
            st.success(f"Imported {data['inserted']} leads. Skipped {data['skipped']} duplicates.")
        else:
            st.error("Import failed. Is the FastAPI server running?")

st.divider()

st.subheader("Manual Lead Input")
st.caption(
    "Manual input is for demo use. In production, this will connect to a website form "
    "and leads will sync automatically."
)

PRODUCT_OPTIONS = [
    "CRM Software",
    "Inventory Management",
    "HR Platform",
    "E-commerce Enablement",
    "Productivity Suite",
]

with st.form("manual_lead_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone (for future WhatsApp integration)")
    product_interest = st.selectbox("Product Interest", PRODUCT_OPTIONS)
    last_contact_date = st.date_input("Last Contact Date")
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Add Lead")

if submitted:
    payload = {
        "name": name,
        "email": email,
        "telegram_chat_id": None,
        "product_interest": product_interest,
        "last_contact_date": str(last_contact_date) if last_contact_date else None,
        "notes": (f"Phone: {phone}\n" if phone else "") + notes,
    }
    response = requests.post("http://localhost:8000/leads", json=payload, timeout=10)
    if response.ok:
        st.success("Lead added successfully.")
    else:
        st.error("Failed to add lead. Is the FastAPI server running?")
