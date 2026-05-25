import html
import sys
from pathlib import Path
from typing import Any

import requests
import streamlit as st

API_URL = "http://localhost:8000"
ROOT_DIR = Path(__file__).resolve().parents[2]


def ensure_root_path() -> None:
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --rx-bg: #f3f6fb;
            --rx-surface: #ffffff;
            --rx-surface-2: #eef2f7;
            --rx-border: #8fa1b7;
            --rx-text: #06111f;
            --rx-muted: #334155;
            --rx-blue: #124fd8;
            --rx-green: #007a52;
            --rx-amber: #9a5a00;
            --rx-red: #b42318;
            --rx-orange: #c2410c;
            --rx-cyan: #0369a1;
            --rx-magenta: #be185d;
        }
        .stApp {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.98), rgba(243,246,251,0.98));
            color: var(--rx-text);
        }
        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .stApp h1, .stApp h2, .stApp h3, .stApp h4,
        .stApp p, .stApp li, .stApp label,
        [data-testid="stWidgetLabel"] p,
        [data-testid="stMarkdownContainer"] > p {
            color: var(--rx-text) !important;
        }
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        .stMarkdown small {
            color: var(--rx-muted) !important;
        }
        section[data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 2px solid var(--rx-border);
        }
        section[data-testid="stSidebar"] * {
            color: var(--rx-text) !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            background: #ffffff !important;
            color: #06111f !important;
            border: 2px solid #64748b !important;
            border-radius: 8px !important;
            caret-color: #124fd8 !important;
        }
        .stTextInput input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus,
        div[data-baseweb="input"] input:focus,
        div[data-baseweb="textarea"] textarea:focus {
            border-color: #124fd8 !important;
            box-shadow: 0 0 0 3px rgba(18, 79, 216, 0.18) !important;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #64748b !important;
            opacity: 1 !important;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="select"] input {
            background: #ffffff !important;
            color: #06111f !important;
            border-color: #64748b !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] svg {
            color: #06111f !important;
            fill: #06111f !important;
        }
        div[data-baseweb="popover"],
        ul[role="listbox"],
        div[role="listbox"] {
            background: #ffffff !important;
            color: #06111f !important;
            border: 1px solid #334155 !important;
        }
        li[role="option"],
        div[role="option"] {
            color: #06111f !important;
            background: #ffffff !important;
        }
        li[role="option"]:hover,
        div[role="option"]:hover {
            background: #dbeafe !important;
            color: #06111f !important;
        }
        [data-testid="stFileUploader"] section {
            background: #fff7ed !important;
            border: 2px dashed #c2410c !important;
            border-radius: 8px !important;
        }
        [data-testid="stFileUploader"] section *,
        [data-testid="stFileUploader"] label,
        [data-testid="stFileUploader"] p,
        [data-testid="stFileUploader"] span {
            color: #431407 !important;
        }
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px !important;
            border: 2px solid #06111f !important;
            background: #ffffff !important;
            color: #06111f !important;
            font-weight: 750 !important;
        }
        .stButton > button[kind="primary"],
        .stFormSubmitButton > button {
            background: #124fd8 !important;
            color: #ffffff !important;
            border-color: #124fd8 !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: #be185d !important;
            box-shadow: 0 0 0 3px rgba(190, 24, 93, 0.14) !important;
        }
        button[data-baseweb="tab"] {
            background: #ffffff !important;
            color: #06111f !important;
            border: 1px solid #8fa1b7 !important;
            border-radius: 8px 8px 0 0 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: #06111f !important;
            color: #ffffff !important;
            border-color: #06111f !important;
        }
        button[data-baseweb="tab"] p {
            color: inherit !important;
        }
        [data-testid="stAlert"] {
            background: #ffffff !important;
            color: #06111f !important;
            border: 2px solid #334155 !important;
        }
        [data-testid="stAlert"] * {
            color: #06111f !important;
        }
        [data-testid="stDataFrame"],
        [data-testid="stTable"] {
            background: #ffffff !important;
            color: #06111f !important;
            border: 1px solid #64748b !important;
        }
        [data-testid="stMetricValue"],
        [data-testid="stMetricLabel"] {
            color: #06111f !important;
        }
        div[data-testid="stMetric"] {
            background: var(--rx-surface);
            border: 2px solid var(--rx-border);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 10px 28px rgba(31, 41, 55, 0.06);
        }
        div[data-testid="stMetric"] label {
            color: var(--rx-muted);
        }
        .rx-page-kicker {
            color: var(--rx-blue);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            margin-bottom: 4px;
        }
        .rx-hero {
            background: var(--rx-surface);
            border: 1px solid var(--rx-border);
            border-radius: 8px;
            padding: 22px 24px;
            box-shadow: 0 18px 45px rgba(31, 41, 55, 0.07);
            margin-bottom: 18px;
        }
        .rx-hero h1 {
            margin: 0 0 8px 0;
            color: var(--rx-text);
            font-size: 2.25rem;
            line-height: 1.08;
            letter-spacing: 0;
        }
        .rx-hero p {
            margin: 0;
            color: var(--rx-muted);
            font-size: 1rem;
            line-height: 1.55;
            max-width: 980px;
        }
        .rx-card {
            background: var(--rx-surface);
            border: 2px solid var(--rx-border);
            border-radius: 8px;
            padding: 16px;
            box-shadow: 0 12px 30px rgba(31, 41, 55, 0.06);
            margin-bottom: 14px;
        }
        .rx-card-tight {
            background: var(--rx-surface);
            border: 2px solid var(--rx-border);
            border-radius: 8px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .rx-card h3, .rx-card-tight h3 {
            margin: 0 0 6px 0;
            font-size: 1.02rem;
            color: var(--rx-text);
        }
        .rx-card p, .rx-card-tight p {
            margin: 0;
            color: var(--rx-muted);
            line-height: 1.45;
        }
        .rx-flow {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 14px 0 6px 0;
        }
        .rx-flow-step {
            background: #ffffff;
            border: 1px solid var(--rx-border);
            border-radius: 8px;
            padding: 12px;
        }
        .rx-flow-step strong {
            display: block;
            color: var(--rx-text);
            margin-bottom: 4px;
        }
        .rx-flow-step span {
            color: var(--rx-muted);
            font-size: 0.86rem;
        }
        .rx-status {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: 700;
            border: 1px solid rgba(23,32,51,0.12);
            white-space: nowrap;
        }
        .rx-status-new { background: #e9fbf5; color: #087354; }
        .rx-status-pending { background: #fff4dc; color: #8a4d00; }
        .rx-status-hot { background: #e9f9ef; color: #0f7a3b; }
        .rx-status-warm { background: #fff8db; color: #8a6200; }
        .rx-status-cold { background: #eaf0ff; color: #2454d6; }
        .rx-status-no_response { background: #eef1f5; color: #5b6575; }
        .rx-status-email_failed, .rx-status-unsubscribed { background: #fdeceb; color: #a73530; }
        .rx-upload-grid {
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr);
            gap: 16px;
            align-items: start;
            margin-bottom: 14px;
        }
        .rx-panel-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 8px;
        }
        .rx-panel-title h3 {
            margin: 0;
            color: var(--rx-text);
        }
        .rx-pill {
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 800;
            border: 1px solid rgba(6, 17, 31, 0.18);
            white-space: nowrap;
        }
        .rx-pill-blue { background: #dbeafe; color: #0f3b9f; }
        .rx-pill-orange { background: #ffedd5; color: #9a3412; }
        .rx-pill-green { background: #dcfce7; color: #166534; }
        .rx-pill-magenta { background: #fce7f3; color: #9d174d; }
        .rx-bulk-panel {
            border-color: #c2410c;
            box-shadow: 0 16px 34px rgba(194, 65, 12, 0.1);
        }
        .rx-info-band {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin: 10px 0 14px 0;
        }
        .rx-info-band div {
            border-radius: 8px;
            padding: 10px;
            font-weight: 750;
        }
        .rx-info-band span {
            display: block;
            font-size: 0.78rem;
            font-weight: 650;
            margin-top: 4px;
        }
        .rx-info-1 { background: #dbeafe; color: #0f3b9f; }
        .rx-info-2 { background: #dcfce7; color: #166534; }
        .rx-info-3 { background: #fce7f3; color: #9d174d; }
        .rx-note {
            border-left: 3px solid var(--rx-blue);
            background: #f2f5ff;
            padding: 10px 12px;
            border-radius: 8px;
            color: #334155;
            margin: 10px 0 16px 0;
        }
        .rx-two-col {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
        }
        .rx-mini-label {
            color: var(--rx-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 3px;
        }
        .rx-mini-value {
            color: var(--rx-text);
            font-size: 0.95rem;
            font-weight: 650;
            margin-bottom: 8px;
        }
        .rx-timeline-row {
            border-left: 2px solid #cbd5e1;
            padding-left: 14px;
            margin-bottom: 12px;
        }
        .rx-timeline-row strong {
            color: var(--rx-text);
        }
        .rx-timeline-row span {
            color: var(--rx-muted);
            font-size: 0.84rem;
        }
        .rx-timeline-row p {
            color: #334155;
            margin: 4px 0 0 0;
        }
        @media (max-width: 900px) {
            .rx-flow, .rx-two-col, .rx-upload-grid, .rx-info-band {
                grid-template-columns: 1fr;
            }
            .rx-hero h1 {
                font-size: 1.8rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### REVARX AI")
        st.caption("Browse and cart recovery")
        st.divider()
        st.page_link("app.py", label="Overview")
        st.page_link("pages/01_upload.py", label="Recovery Studio")
        st.page_link("pages/02_campaign.py", label="Campaign Lab")
        st.page_link("pages/03_dashboard.py", label="Analytics")
        st.page_link("pages/04_leads.py", label="Customer Board")


def hero(kicker: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="rx-hero">
            <div class="rx-page-kicker">{html.escape(kicker)}</div>
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="rx-card">
            <h3>{html.escape(title)}</h3>
            <p>{html.escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def flow(steps: list[tuple[str, str]]) -> None:
    step_html = "".join(
        f'<div class="rx-flow-step"><strong>{html.escape(title)}</strong><span>{html.escape(body)}</span></div>'
        for title, body in steps
    )
    st.markdown(f'<div class="rx-flow">{step_html}</div>', unsafe_allow_html=True)


def get_json(path: str, fallback: Any, timeout: int = 4) -> tuple[Any, bool]:
    try:
        response = requests.get(f"{API_URL}{path}", timeout=timeout)
        if response.ok:
            return response.json(), False
    except Exception:
        pass
    return fallback, True


def post_json(path: str, payload: dict, timeout: int = 30) -> tuple[dict | None, str | None]:
    try:
        response = requests.post(f"{API_URL}{path}", json=payload, timeout=timeout)
        if response.ok:
            return response.json(), None
        return None, response.text
    except Exception as exc:
        return None, str(exc)


def status_label(status: str | None) -> str:
    labels = {
        "new": "New",
        "pending": "Email sent / waiting",
        "hot": "Replied - hot",
        "warm": "Replied - warm",
        "cold": "Replied - cold",
        "no_response": "No response",
        "email_failed": "Email failed",
        "unsubscribed": "Unsubscribed",
    }
    return labels.get(status or "new", status or "new")


def status_badge(status: str | None) -> str:
    status = status or "new"
    return f'<span class="rx-status rx-status-{html.escape(status)}">{html.escape(status_label(status))}</span>'


def lead_title(lead: dict) -> str:
    product = lead.get("product_viewed") or lead.get("product_interest") or "Unknown product"
    return f"{lead.get('id')} - {lead.get('name')} - {product}"


def latest_lead_options(leads: list[dict]) -> dict[str, int]:
    return {lead_title(lead): int(lead["id"]) for lead in leads if lead.get("id")}


def escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))
