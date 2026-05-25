import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.ui import (
    API_URL,
    escape,
    get_json,
    hero,
    inject_global_css,
    latest_lead_options,
    post_json,
    render_sidebar,
    status_badge,
)

inject_global_css()
render_sidebar()

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

REPLY_PRESETS = [
    "Yes, is there a discount available if I buy today?",
    "Can you send the checkout link again? I want to purchase.",
    "Maybe next week. Please remind me again.",
    "I am comparing options. Keep me posted if the price drops.",
    "Already bought from Amazon.",
    "The price is too high for me.",
    "Stop emailing me.",
    "Type my own reply",
]

hero(
    "Recovery Studio",
    "Add customers, send recovery emails, then test the outcome loop.",
    "This is the live demo workspace. Add one shopper or upload many, then simulate replies or no response from the same page to verify the board, dashboard, and A/B learning updates.",
)

if "last_lead_id" not in st.session_state:
    st.session_state.last_lead_id = None
if "last_action_summary" not in st.session_state:
    st.session_state.last_action_summary = None
if "last_lead_summary" not in st.session_state:
    st.session_state.last_lead_summary = None


def render_result_card(data: dict) -> None:
    st.markdown(
        f"""
        <div class="rx-card">
            <h3>Recovery email result</h3>
            <div class="rx-two-col">
                <div>
                    <div class="rx-mini-label">Variant selected</div>
                    <div class="rx-mini-value">{escape(data.get("variant_used"))} - {escape(data.get("variant_label"))}</div>
                    <div class="rx-mini-label">Email sent</div>
                    <div class="rx-mini-value">{escape(data.get("email_sent"))}</div>
                </div>
                <div>
                    <div class="rx-mini-label">LLM used</div>
                    <div class="rx-mini-value">{escape(data.get("llm_used"))}</div>
                    <div class="rx-mini-label">Reason</div>
                    <div class="rx-mini-value">{escape(data.get("selection_reason"))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    links = []
    if data.get("whatsapp_link"):
        links.append(("Continue on WhatsApp", data["whatsapp_link"]))
    if data.get("telegram_link"):
        links.append(("Continue on Telegram", data["telegram_link"]))
    if links:
        st.caption("Optional channel links for future WhatsApp/Telegram testing. Email remains the active channel.")
        for label, url in links:
            st.link_button(label, url)


def render_reply_lab(leads: list[dict], forced_lead_id: int | None = None) -> None:
    if not leads:
        st.warning("No customers available for reply testing yet.")
        return

    options = latest_lead_options(leads)
    option_keys = list(options.keys())
    default_index = 0
    if forced_lead_id:
        for idx, label in enumerate(option_keys):
            if options[label] == forced_lead_id:
                default_index = idx
                break

    st.markdown('<div class="rx-card">', unsafe_allow_html=True)
    st.subheader("Reply and no-response simulator")
    st.caption("Use this right after sending a recovery email to verify classification, customer status, dashboard changes, and A/B learning.")

    selected_label = st.selectbox("Customer", option_keys, index=default_index, key="reply_lab_customer")
    selected_id = options[selected_label]
    selected_lead = next((lead for lead in leads if int(lead.get("id")) == selected_id), {})

    detail_cols = st.columns(4)
    detail_cols[0].markdown(status_badge(selected_lead.get("status")), unsafe_allow_html=True)
    detail_cols[1].metric("Variant", selected_lead.get("variant") or selected_lead.get("ab_preference") or "NA")
    detail_cols[2].metric("Product", selected_lead.get("product_category") or "NA")
    detail_cols[3].metric("State", selected_lead.get("state") or "NA")

    preset = st.selectbox("Customer reply", REPLY_PRESETS, key="reply_lab_preset")
    custom_reply = st.text_area(
        "Custom reply",
        value="" if preset != "Type my own reply" else "Can you send the checkout link again?",
        height=92,
        key="reply_lab_custom",
    )
    content = custom_reply if preset == "Type my own reply" else preset

    action_col1, action_col2 = st.columns([1, 1])
    with action_col1:
        if st.button("Classify reply and update learning", type="primary", key="reply_lab_classify"):
            data, error = post_json(
                "/simulate-reply",
                {"lead_id": selected_id, "content": content, "is_voice_note": False},
                timeout=30,
            )
            if error:
                st.error(error)
            else:
                st.success(
                    f"Classified as {data.get('reply_classification')} using {data.get('classifier_llm_used')}. "
                    "Analytics and A/B selection history are updated."
                )
                st.session_state.last_lead_id = selected_id
    with action_col2:
        if st.button("Mark as no response", key="reply_lab_no_response"):
            try:
                response = requests.post(f"{API_URL}/leads/{selected_id}/mark-no-response", timeout=10)
                if response.ok:
                    st.success("Marked as no response. This lowers confidence for the sent variant.")
                    st.session_state.last_lead_id = selected_id
                else:
                    st.error(response.text)
            except Exception as exc:
                st.error(f"Request failed: {exc}")

    st.markdown("</div>", unsafe_allow_html=True)


st.markdown(
    """
    <div class="rx-info-band">
        <div class="rx-info-1">Single customer<span>Immediate A/B email test</span></div>
        <div class="rx-info-2">Bulk CSV/TXT<span>Import hundreds or thousands</span></div>
        <div class="rx-info-3">Reply simulator<span>Update dashboard and learning</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

single_col, bulk_col = st.columns([1, 1.08], gap="large")

with single_col:
    st.markdown(
        """
        <div class="rx-card">
            <div class="rx-panel-title">
                <h3>Single customer instant test</h3>
                <span class="rx-pill rx-pill-blue">Live email</span>
            </div>
            <p>Enter one abandoned shopper. The API chooses Professional or Friendly, generates the recovery email, sends it, and opens reply testing below.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("single_customer_form"):
        name = st.text_input("Name", "Vicky Demo")
        email = st.text_input("Email", "mbvb1312@gmail.com")
        phone = st.text_input("Phone", "+91")

        form_col_a, form_col_b = st.columns(2)
        with form_col_a:
            age = st.number_input("Age", min_value=10, max_value=90, value=24, step=1)
            gender = st.selectbox("Gender", ["male", "female", "other"])
        with form_col_b:
            state = st.selectbox("State", INDIAN_STATES, index=12)
            product_category = st.selectbox("Product category", CATEGORIES)

        suggested_product = st.selectbox("Product suggestion", PRODUCTS)
        product_viewed = st.text_input("Product viewed", suggested_product)
        notes = st.text_area("Browse/cart context", "Added to cart and abandoned at checkout")
        submitted = st.form_submit_button("Send recovery email", type="primary")

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
        data, error = post_json("/leads", payload, timeout=90)
        if error:
            st.error(error)
        else:
            st.session_state.last_lead_id = int(data.get("lead_id"))
            st.session_state.last_action_summary = data
            st.session_state.last_lead_summary = {
                "name": name,
                "product": product_viewed,
                "time": pd.Timestamp.utcnow(),
            }
            render_result_card(data)
            last_lead = st.session_state.last_lead_summary
            if last_lead:
                timestamp = last_lead["time"].strftime("%Y-%m-%d %H:%M UTC")
                st.success(f"Last lead submitted: {last_lead['name']} — {last_lead['product']} ({timestamp})")

with bulk_col:
    st.markdown(
        """
        <div class="rx-card rx-bulk-panel">
            <div class="rx-panel-title">
                <h3>Bulk CSV/TXT recovery import</h3>
                <span class="rx-pill rx-pill-orange">Visible bulk mode</span>
            </div>
            <p>Upload structured CSV or messy TXT. Name + phone + product is enough to track a customer; email rows also queue recovery emails immediately.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    sample_data = pd.DataFrame(
        {
            "name": ["Priya Nair", "Rahul Verma", "Ananya Sharma"],
            "email": ["priya@example.com", "rahul@example.com", ""],
            "phone": ["+919988776655", "+919876543210", "+919123456789"],
            "age": [28, 34, 22],
            "gender": ["female", "male", "female"],
            "state": ["Kerala", "Maharashtra", "Delhi"],
            "product_viewed": ["Nike Air Max 270", "Samsung Galaxy S24 Ultra", "MacBook Air M3"],
            "product_category": ["footwear", "electronics", "electronics"],
            "notes": ["Viewed 3 times in the last week", "Added to cart and abandoned at checkout", "Asked about student discount"],
        }
    )

    st.download_button(
        "Download sample CSV",
        sample_data.to_csv(index=False),
        "revarx_abandoned_customers.csv",
        "text/csv",
    )

    with st.expander("Messy TXT examples that now work", expanded=True):
        st.code(
            "Ravi Kumar, 9876543210, Nike Air Max 270\n"
            "Priya Nair | +91 9988776655 | Samsung Galaxy S24 Ultra | asked about discount\n"
            "Ananya 9123456789 looking at MacBook Air M3\n"
            "Rahul Verma, rahul@example.com, 34, male, Maharashtra, Sony WH-1000XM5, electronics",
            language="text",
        )

    uploaded_file = st.file_uploader("Upload CSV or TXT customer file", type=["csv", "txt"])
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if uploaded_file.name.lower().endswith(".csv"):
            try:
                preview_df = pd.read_csv(BytesIO(file_bytes))
                st.dataframe(preview_df, width="stretch", hide_index=True)
            except Exception:
                st.warning("Could not preview CSV, but upload can still be attempted.")
        else:
            st.text_area("TXT preview", file_bytes.decode("utf-8", errors="ignore"), height=180)

        if st.button("Import customers and start recovery", type="primary"):
            mime = "text/plain" if uploaded_file.name.lower().endswith(".txt") else "text/csv"
            files = {"file": (uploaded_file.name, file_bytes, mime)}
            try:
                response = requests.post(f"{API_URL}/upload-leads", files=files, timeout=60)
                if response.ok:
                    data = response.json()
                    st.session_state.last_action_summary = data
                    tracked = data.get("customers_tracked", data.get("inserted", 0))
                    st.success(
                        f"Tracked {tracked} customers, skipped {data.get('skipped', 0)}, "
                        f"queued {data.get('emails_queued', 0)} recovery emails."
                    )
                    if data.get("phone_only", 0):
                        st.warning(
                            f"{data.get('phone_only')} imported customers only had phone numbers. "
                            "They are tracked for analytics and future WhatsApp/Telegram, but email needs an email address."
                        )
                    st.info("Use the simulator below to test replies or no response for imported customers.")
                else:
                    st.error(response.text)
            except Exception as exc:
                st.error(f"Upload failed: {exc}")

st.divider()

fallback_leads = []
leads, is_mock = get_json("/leads", fallback_leads)
if is_mock:
    st.info("Backend is offline, so reply testing is unavailable until the API is running.")

render_reply_lab(leads, st.session_state.last_lead_id)
