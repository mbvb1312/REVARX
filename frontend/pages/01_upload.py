import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"

INDIAN_STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
]

PRODUCTS = [
    "MacBook Air M3",
    "Samsung Galaxy S24 Ultra",
    "Sony WH-1000XM5 Headphones",
    "Dell Inspiron 14 Laptop",
    "Nike Air Max 270",
    "Adidas Ultraboost Light",
    "Puma RS-X Sneakers",
    "Levi's 501 Jeans",
    "Fossil Gen 6 Smartwatch",
    "Philips Air Fryer XL",
]

CATEGORIES = ["electronics", "fashion", "footwear", "accessories", "home_appliances"]

st.title("Live Demo: Add Abandoned Customers")
st.markdown("Add one customer for an instant recovery email, or upload CSV/TXT files for a bulk live campaign.")
st.info(
    "Evaluation workflow: add a customer, send a recovery email, trigger WhatsApp or Telegram opt-in, "
    "simulate or receive a reply, and review status plus A/B learning on the dashboard."
)

st.markdown(
    """
    <style>
    .wa-panel {
        background: #0b3d2e;
        border: 1px solid #1f6f54;
        border-radius: 10px;
        padding: 12px 14px;
    }
    .wa-title { color: #ecfdf3; font-weight: 600; margin-bottom: 6px; }
    .wa-note { color: #a7f3d0; font-size: 0.86rem; margin-bottom: 8px; }
    .wa-btn {
        display: inline-block;
        background: #22c55e;
        color: #0b3d2e;
        padding: 8px 14px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

tab_single, tab_bulk = st.tabs(["Single customer instant test", "Bulk CSV/TXT upload"])

with tab_single:
    st.subheader("Single customer check")
    st.caption("Enter customer and product details. The API picks A or B, generates copy, sends email, and starts tracking.")

    with st.form("single_customer_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            name = st.text_input("Name", "Vicky Demo")
            email = st.text_input("Email", "mbvb1312@gmail.com")
            phone = st.text_input("Phone (for WhatsApp opt-in)", "+91")
            age = st.number_input("Age", min_value=10, max_value=90, value=24, step=1)
            gender = st.selectbox("Gender", ["male", "female", "other"])
            state = st.selectbox("State", INDIAN_STATES, index=12)
        with col_b:
            suggested_product = st.selectbox("Product suggestion", PRODUCTS)
            product_viewed = st.text_input("Product viewed", suggested_product)
            product_category = st.selectbox("Product category", CATEGORIES)
            notes = st.text_area("Browse/cart context", "Added to cart and abandoned at checkout")

        submitted = st.form_submit_button("Send recovery email now", type="primary")

    if submitted:
        payload = {
            "name": name,
            "email": email,
            "phone": phone,
            "age": int(age),
            "gender": gender,
            "state": state,
            "product_viewed": product_viewed,
            "product_interest": product_viewed,
            "product_category": product_category,
            "notes": notes,
        }
        try:
            response = requests.post(f"{API_URL}/leads", json=payload, timeout=90)
            if response.ok:
                data = response.json()
                st.success(
                    f"Customer added. Variant {data.get('variant_used')} ({data.get('variant_label')}) selected. "
                    f"Email sent: {data.get('email_sent')}."
                )
                st.info(f"LLM used: {data.get('llm_used')} | Reason: {data.get('selection_reason')}")

                whatsapp_link = data.get("whatsapp_link")
                telegram_link = data.get("telegram_link")
                if whatsapp_link or telegram_link:
                    st.subheader("Continue conversation")
                    st.caption("These channels require the user to click the link and start the chat.")
                    col_w, col_t = st.columns(2)
                    with col_w:
                        if whatsapp_link:
                            st.markdown(
                                f"""
                                <div class="wa-panel">
                                    <div class="wa-title">WhatsApp opt-in</div>
                                    <div class="wa-note">
                                        To automate WhatsApp messaging, link a WhatsApp Business account. For now, click below
                                        to open WhatsApp with a prefilled message and send it manually.
                                    </div>
                                    <a class="wa-btn" href="{whatsapp_link}" target="_blank">Continue on WhatsApp</a>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        else:
                            st.info("WhatsApp link not configured.")
                    with col_t:
                        if telegram_link:
                            st.link_button("Continue on Telegram", telegram_link)
                            st.caption(
                                "Click Start to opt in. If the bot does not respond, set the webhook (local dev needs ngrok)."
                            )
                        else:
                            st.info("Telegram link not configured.")
            else:
                st.error(response.text)
        except Exception as exc:
            st.error(f"Could not reach API: {exc}")

with tab_bulk:
    st.subheader("Bulk abandoned customer upload")
    st.caption("CSV and TXT uploads are queued in the background so large campaigns do not time out.")

    sample_data = pd.DataFrame(
        {
            "name": ["Priya Nair", "Rahul Verma"],
            "email": ["priya@example.com", "rahul@example.com"],
            "age": [28, 34],
            "gender": ["female", "male"],
            "state": ["Kerala", "Maharashtra"],
            "product_viewed": ["Nike Air Max 270", "Samsung Galaxy S24 Ultra"],
            "product_category": ["footwear", "electronics"],
            "notes": ["Viewed 3 times in the last week", "Added to cart and abandoned at checkout"],
        }
    )

    st.download_button(
        "Download sample CSV",
        sample_data.to_csv(index=False),
        "revarx_abandoned_customers.csv",
        "text/csv",
    )

    st.code(
        "TXT format examples:\n"
        "Priya Nair, priya@example.com, 28, female, Kerala, Nike Air Max 270, footwear, Viewed 3 times\n"
        "Rahul Verma, rahul@example.com, Samsung Galaxy S24 Ultra, Added to cart",
        language="text",
    )

    uploaded_file = st.file_uploader("Upload CSV or TXT", type=["csv", "txt"])
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.name.lower().endswith(".csv"):
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.dataframe(preview_df, width="stretch")
            except Exception:
                st.warning("Could not preview CSV, but upload can still be attempted.")
        else:
            st.text_area("TXT preview", file_bytes.decode("utf-8", errors="ignore"), height=180)

        if st.button("Import and queue recovery emails", type="primary"):
            files = {"file": (uploaded_file.name, file_bytes, "text/plain" if uploaded_file.name.lower().endswith(".txt") else "text/csv")}
            try:
                response = requests.post(f"{API_URL}/upload-leads", files=files, timeout=60)
                if response.ok:
                    data = response.json()
                    st.success(
                        f"Inserted {data.get('inserted', 0)} customers, skipped {data.get('skipped', 0)}, "
                        f"queued {data.get('emails_queued', 0)} recovery emails."
                    )
                    st.info(data.get("message", "Emails queued."))
                else:
                    st.error(response.text)
            except Exception as exc:
                st.error(f"Upload failed: {exc}")
