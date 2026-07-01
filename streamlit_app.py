import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.campaign_suggestions import suggest_campaign_targeting
from src.constants import COUNTRIES, EMAIL_PROVIDERS
from src.exporter import leads_to_csv_bytes
from src.pipeline_runner import PipelineConfig, run_pipeline

load_dotenv()

DEFAULT_APP_URL = "https://ai-leads-pipeline.streamlit.app/"

st.set_page_config(
    page_title="Signal — Lead Pipeline",
    page_icon="◎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design system
#
# Concept: "Signal" — the app finds leads the way a radar finds contacts.
# A pipeline is a straight line with real stages (scrape -> verify -> enrich
# -> export -> notify), so a vertical "signal rail" of connected nodes is the
# signature element, and it doubles as the live progress indicator when a
# campaign runs.
#
# Palette   bg #0B0E14 · surface #131826 · surface-2 #1B2233 · line #232C3D
#           text #ECF1F8 · text-dim #8996AA · accent (signal) #FF6A3D
#           accent-2 (verified) #33D6A6 · warn #FFC857 · danger #FF5C7A
# Type      Display: Space Grotesk · Body: Inter · Data/Mono: JetBrains Mono
# ---------------------------------------------------------------------------

FONT_IMPORT = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
</style>
"""

BRANDING_HIDE_CSS = """
<style>
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background-color: rgba(0, 0, 0, 0) !important; }
    .stAppDeployButton, [data-testid="stStatusWidget"] { display: none; }
    a[href*="github.com"], .viewerBadge_container__r5tak { display: none !important; }

    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapsedControl"] button,
    button[data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
    }
</style>
"""

BASE_CSS = """
<style>
    html, body, .stApp, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp { background: var(--sg-bg) !important; }
    [data-testid="stAppViewContainer"] { background: var(--sg-bg) !important; }
    .block-container { padding-top: 1.6rem !important; padding-bottom: 4rem !important; max-width: 1180px; }

    .stApp, .stApp p, .stApp label, .stApp span, .stApp li,
    .stMarkdown, .stMarkdown p, [data-testid="stWidgetLabel"] p,
    [data-testid="stMarkdownContainer"] p, [data-testid="stCaptionContainer"] p,
    [data-testid="stMetricLabel"] p, [data-testid="stMetricValue"] {
        color: var(--sg-text) !important;
    }
    h1, h2, h3, h4, .page-title, .card-title {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--sg-text) !important;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: var(--sg-sidebar) !important;
        border-right: 1px solid var(--sg-line);
    }
    [data-testid="stSidebar"] * { color: var(--sg-text) !important; }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: var(--sg-text-dim) !important; }

    /* ---- Header ---- */
    .brand-row { display: flex; align-items: center; gap: 0.65rem; }
    .brand-mark {
        width: 38px; height: 38px; border-radius: 10px;
        background: radial-gradient(circle at 35% 30%, var(--sg-accent), #b8431c 75%);
        display: flex; align-items: center; justify-content: center;
        font-family: 'Space Grotesk', sans-serif; font-weight: 700; color: #0B0E14 !important;
        font-size: 1.1rem; box-shadow: 0 0 0 1px var(--sg-line), 0 6px 16px rgba(255,106,61,0.28);
        flex-shrink: 0;
    }
    .page-title { font-size: 1.55rem; font-weight: 700; margin: 0; line-height: 1.1; letter-spacing: -0.01em; }
    .page-subtitle { color: var(--sg-text-dim) !important; margin: 0.15rem 0 0 0; font-size: 0.92rem; }

    /* ---- Section labels ---- */
    .section-label {
        font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase; color: var(--sg-accent) !important;
        margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem;
    }
    .section-label::before { content: ""; width: 6px; height: 6px; border-radius: 50%;
        background: var(--sg-accent); box-shadow: 0 0 8px var(--sg-accent); }
    .stage-num {
        font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--sg-text-dim) !important;
        border: 1px solid var(--sg-line); border-radius: 6px; padding: 0.1rem 0.45rem; margin-right: 0.5rem;
    }
    .card-title { font-size: 1.05rem; font-weight: 600; margin: 0 0 0.15rem 0; }
    .card-desc { color: var(--sg-text-dim) !important; font-size: 0.85rem; margin: 0 0 1.1rem 0; }

    /* ---- Cards (bordered containers) ---- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--sg-surface) !important;
        border: 1px solid var(--sg-line) !important;
        border-radius: 14px !important;
        padding: 0.4rem 0.2rem !important;
        box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { background: transparent !important; }

    /* ---- Inputs ---- */
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] {
        background: var(--sg-surface-2) !important;
        border: 1px solid var(--sg-line) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] > div, div[data-baseweb="select"] span {
        background: transparent !important; color: var(--sg-text) !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="select"]:focus-within {
        border-color: var(--sg-accent) !important;
        box-shadow: 0 0 0 1px var(--sg-accent) !important;
    }
    ::placeholder { color: var(--sg-text-dim) !important; opacity: 0.8 !important; }

    div[data-baseweb="popover"] { background: var(--sg-surface-2) !important; border: 1px solid var(--sg-line) !important; }
    div[data-baseweb="popover"] ul { background: var(--sg-surface-2) !important; }
    div[data-baseweb="popover"] li { background: var(--sg-surface-2) !important; color: var(--sg-text) !important; }
    div[data-baseweb="popover"] li:hover { background: var(--sg-line) !important; }

    /* ---- Buttons ---- */
    .stButton button, .stDownloadButton button {
        border-radius: 8px !important; font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important; transition: all 0.15s ease;
    }
    button[kind="secondary"], [data-testid="stBaseButton-secondary"] {
        background: var(--sg-surface-2) !important; color: var(--sg-text) !important;
        border: 1px solid var(--sg-line) !important;
    }
    button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover {
        border-color: var(--sg-accent) !important; color: var(--sg-accent) !important;
    }
    [data-testid="stBaseButton-primary"], button[kind="primary"] {
        background: var(--sg-accent) !important; border: 1px solid var(--sg-accent) !important;
        box-shadow: 0 6px 18px rgba(255,106,61,0.25) !important;
    }
    [data-testid="stBaseButton-primary"] *, button[kind="primary"] * { color: #0B0E14 !important; }
    [data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover { filter: brightness(1.08); }

    /* ---- Toggles / checkboxes / sliders ---- */
    [data-testid="stCheckbox"] label p { color: var(--sg-text) !important; }
    [data-baseweb="slider"] div[role="slider"] { background: var(--sg-accent) !important; }

    /* ---- Tabs ---- */
    div[data-baseweb="tab-list"] { gap: 0.25rem; border-bottom: 1px solid var(--sg-line); }
    div[data-baseweb="tab-list"] button { color: var(--sg-text-dim) !important; font-weight: 600; }
    div[data-baseweb="tab-list"] button[aria-selected="true"] {
        color: var(--sg-accent) !important; border-bottom: 2px solid var(--sg-accent) !important;
    }

    /* ---- Alerts ---- */
    div[data-testid="stAlert"] { border-radius: 10px !important; }
    div[data-testid="stAlert"] * { color: inherit !important; }
    div[data-testid="stAlert"][data-test-alerttype="info"] { background: rgba(77,168,232,0.12) !important; color: #7cc4f5 !important; border: 1px solid rgba(77,168,232,0.3) !important; }
    div[data-testid="stAlert"][data-test-alerttype="success"] { background: rgba(51,214,166,0.12) !important; color: #33D6A6 !important; border: 1px solid rgba(51,214,166,0.3) !important; }
    div[data-testid="stAlert"][data-test-alerttype="warning"] { background: rgba(255,200,87,0.12) !important; color: #FFC857 !important; border: 1px solid rgba(255,200,87,0.3) !important; }
    div[data-testid="stAlert"][data-test-alerttype="error"] { background: rgba(255,92,122,0.12) !important; color: #FF5C7A !important; border: 1px solid rgba(255,92,122,0.3) !important; }

    /* ---- Progress bar ---- */
    div[data-testid="stProgress"] div[role="progressbar"] > div { background: var(--sg-accent) !important; }
    div[data-testid="stProgress"] div[role="progressbar"] { background: var(--sg-surface-2) !important; }

    /* ---- Dataframe ---- */
    [data-testid="stDataFrame"] { border: 1px solid var(--sg-line) !important; border-radius: 10px !important; overflow: hidden; }

    /* ---- Code / logs ---- */
    code { background: var(--sg-surface-2) !important; color: var(--sg-text) !important; }
    pre { background: var(--sg-surface-2) !important; border: 1px solid var(--sg-line) !important; border-radius: 10px !important; }
    pre code { background: transparent !important; color: #9fe6c9 !important; font-family: 'JetBrains Mono', monospace !important; }

    hr { border-color: var(--sg-line) !important; }

    /* ---- Metric cards ---- */
    .metric-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .metric-card {
        flex: 1; min-width: 130px; background: var(--sg-surface-2); border: 1px solid var(--sg-line);
        border-radius: 12px; padding: 0.85rem 1rem;
    }
    .metric-card .m-label { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; letter-spacing: 0.08em;
        text-transform: uppercase; color: var(--sg-text-dim); margin-bottom: 0.3rem; }
    .metric-card .m-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--sg-text); }
    .metric-card.ok .m-value { color: var(--sg-accent-2); }
    .metric-card.pending .m-value { color: var(--sg-text-dim); }

    /* ---- Signal rail (signature element) ---- */
    .rail { display: flex; align-items: center; gap: 0; margin: 0.2rem 0 1.6rem 0; }
    .rail-node { display: flex; align-items: center; gap: 0.55rem; }
    .rail-dot { width: 12px; height: 12px; border-radius: 50%; border: 2px solid var(--sg-line);
        background: var(--sg-surface-2); flex-shrink: 0; }
    .rail-node.done .rail-dot { background: var(--sg-accent-2); border-color: var(--sg-accent-2); }
    .rail-node.active .rail-dot { background: var(--sg-accent); border-color: var(--sg-accent);
        box-shadow: 0 0 0 4px rgba(255,106,61,0.18); animation: pulse 1.6s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { box-shadow: 0 0 0 4px rgba(255,106,61,0.18); } 50% { box-shadow: 0 0 0 8px rgba(255,106,61,0.05); } }
    .rail-label { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: var(--sg-text-dim); white-space: nowrap; }
    .rail-node.active .rail-label { color: var(--sg-text); }
    .rail-node.done .rail-label { color: var(--sg-accent-2); }
    .rail-line { flex: 1; height: 1px; background: var(--sg-line); margin: 0 0.6rem; }
    .rail-line.done { background: var(--sg-accent-2); }

    /* ---- Checklist ---- */
    .check-item { display: flex; align-items: center; gap: 0.55rem; padding: 0.3rem 0; font-size: 0.88rem; }
    .check-icon { width: 18px; height: 18px; border-radius: 50%; display: flex; align-items: center;
        justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
    .check-icon.pass { background: rgba(51,214,166,0.15); color: var(--sg-accent-2); }
    .check-icon.fail { background: rgba(255,92,122,0.15); color: var(--sg-danger); }
    .check-text.pass { color: var(--sg-text) !important; }
    .check-text.fail { color: var(--sg-text-dim) !important; }

    /* ---- Sidebar status pill ---- */
    .cred-pill { display: inline-flex; align-items: center; gap: 0.4rem; font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem; padding: 0.2rem 0.55rem; border-radius: 999px; border: 1px solid var(--sg-line); margin-top: 0.3rem; }
    .cred-pill.on { color: var(--sg-accent-2); border-color: rgba(51,214,166,0.4); background: rgba(51,214,166,0.08); }
    .cred-pill.off { color: var(--sg-text-dim); }
    .cred-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
</style>
"""

DARK_VARS = """
<style>
:root {
    --sg-bg: #0B0E14; --sg-sidebar: #0E1219; --sg-surface: #131826; --sg-surface-2: #1B2233;
    --sg-line: #262F42; --sg-text: #ECF1F8; --sg-text-dim: #8996AA;
    --sg-accent: #FF6A3D; --sg-accent-2: #33D6A6; --sg-danger: #FF5C7A;
}
</style>
"""

LIGHT_VARS = """
<style>
:root {
    --sg-bg: #F4F5F8; --sg-sidebar: #FFFFFF; --sg-surface: #FFFFFF; --sg-surface-2: #F1F2F6;
    --sg-line: #E1E4EC; --sg-text: #10131C; --sg-text-dim: #5C6478;
    --sg-accent: #E85B2C; --sg-accent-2: #0FA37C; --sg-danger: #E13A5C;
}
</style>
"""

STAGES = ["Target", "Delivery", "Launch", "Results"]


def apply_theme() -> None:
    st.markdown(FONT_IMPORT, unsafe_allow_html=True)
    st.markdown(BRANDING_HIDE_CSS, unsafe_allow_html=True)
    st.markdown(LIGHT_VARS if st.session_state.get("theme") == "light" else DARK_VARS, unsafe_allow_html=True)
    st.markdown(BASE_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    # SECURITY: Credentials are NEVER pre-filled from server environment variables.
    # Every visitor starts with empty credential fields and must enter their own keys.
    # This prevents API keys from leaking across users/sessions/devices.
    defaults = {
        "theme": "dark",
        "apify_token": "",
        "groq_api_key": "",
        "slack_webhook_url": "",
        "app_url": DEFAULT_APP_URL,
        "campaign_name": "",
        "industry": "",
        "campaign_goal": "",
        "country": "United States",
        "country_search": "",
        "titles_text": "CEO, Founder, VP of Sales",
        "outreach_angle": "",
        "client_email": "",
        "email_provider": "Gmail",
        "sender_email": "",
        "email_password": "",
        "last_result": None,
        "suggested_limit": 10,
        "is_running": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def resolve_smtp_settings(provider: str, sender_email: str, email_password: str) -> dict:
    cfg = EMAIL_PROVIDERS[provider]
    username = cfg.get("fixed_username") or sender_email.strip()
    return {
        "smtp_host": cfg["host"],
        "smtp_port": cfg["port"],
        "smtp_user": username,
        "smtp_password": email_password.strip(),
        "smtp_from": sender_email.strip(),
    }


def render_rail(active_index: int) -> None:
    """Signature element: a signal rail showing the four real stages of a run."""
    nodes = []
    for i, label in enumerate(STAGES):
        state = "done" if i < active_index else ("active" if i == active_index else "")
        nodes.append(f'<div class="rail-node {state}"><div class="rail-dot"></div>'
                      f'<span class="rail-label">{i+1:02d} · {label}</span></div>')
        if i < len(STAGES) - 1:
            line_state = "done" if i < active_index else ""
            nodes.append(f'<div class="rail-line {line_state}"></div>')
    st.markdown(f'<div class="rail">{"".join(nodes)}</div>', unsafe_allow_html=True)


def render_header() -> None:
    left, right = st.columns([6, 1])
    with left:
        st.markdown(
            '<div class="brand-row"><div class="brand-mark">◎</div><div>'
            '<p class="page-title">Signal</p>'
            '<p class="page-subtitle">Scrape, verify, enrich, and deliver B2B lead lists — end to end.</p>'
            '</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        label = "☀ Light" if st.session_state.theme == "dark" else "☾ Dark"
        if st.button(label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()


def render_sidebar() -> dict:
    st.sidebar.markdown('<p class="section-label">Connections</p>', unsafe_allow_html=True)
    st.sidebar.caption("Kept in your browser session only — never stored server-side.")

    apify_token = st.sidebar.text_input("Apify token", value=st.session_state.apify_token, type="password", placeholder="apify_api_...")
    apify_state = "on" if apify_token.strip() else "off"
    st.sidebar.markdown(
        f'<span class="cred-pill {apify_state}"><span class="cred-dot"></span>'
        f'{"Apify connected" if apify_state == "on" else "Apify token missing"}</span>',
        unsafe_allow_html=True,
    )

    groq_api_key = st.sidebar.text_input("Groq API key", value=st.session_state.groq_api_key, type="password", placeholder="gsk_...")
    groq_state = "on" if groq_api_key.strip() else "off"
    st.sidebar.markdown(
        f'<span class="cred-pill {groq_state}"><span class="cred-dot"></span>'
        f'{"Groq connected" if groq_state == "on" else "Groq key missing"}</span>',
        unsafe_allow_html=True,
    )

    st.session_state.apify_token = apify_token
    st.session_state.groq_api_key = groq_api_key

    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="section-label">Field notes</p>', unsafe_allow_html=True)
    st.sidebar.caption("Start with a limit of 1–3 leads while you dial in targeting — it keeps Apify spend low during test runs.")
    st.sidebar.caption("Apollo-style job titles work best: plain seniority + function, e.g. \"VP of Sales\" rather than full descriptions.")

    return {
        "apify_token": apify_token.strip(),
        "groq_api_key": groq_api_key.strip(),
    }


def render_campaign_card(credentials: dict) -> dict:
    with st.container(border=True):
        st.markdown(
            '<p class="section-label"><span class="stage-num">01</span>Target</p>'
            '<p class="card-title">Who are you trying to reach?</p>'
            '<p class="card-desc">Set the campaign context, then confirm the country and job titles to scrape.</p>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            campaign_name = st.text_input(
                "Campaign name", value=st.session_state.campaign_name, placeholder="e.g. US SaaS Founders Q2",
            )
            industry = st.text_input(
                "Industry / niche", value=st.session_state.industry,
                placeholder="e.g. B2B SaaS, Real Estate, E-commerce",
            )
            campaign_goal = st.text_area(
                "Campaign goal (optional)", value=st.session_state.campaign_goal,
                placeholder="e.g. Outreach list for cold email to marketing leaders", height=80,
            )
        with c2:
            country_search = st.text_input("Search country", value=st.session_state.country_search, placeholder="Type to filter...")
            filtered = [c for c in COUNTRIES if country_search.lower() in c.lower()] if country_search else COUNTRIES
            default_idx = filtered.index(st.session_state.country) if st.session_state.country in filtered else 0
            country = st.selectbox("Target country", filtered, index=default_idx)
            outreach_angle = st.text_area(
                "Outreach angle (optional)", value=st.session_state.outreach_angle,
                placeholder="AI can suggest this, or write your own positioning.", height=80,
            )

        st.divider()
        st.markdown('<p class="section-label">Targeting</p>', unsafe_allow_html=True)
        col_titles, col_ai = st.columns([4, 1.2])
        with col_titles:
            titles_text = st.text_area(
                "Job titles (comma-separated)", value=st.session_state.titles_text,
                height=100, placeholder="CEO, Founder, Head of Marketing",
            )
        with col_ai:
            st.write("")
            st.write("")
            ai_disabled = not credentials["groq_api_key"] or not industry.strip()
            if st.button("✦ AI suggest", use_container_width=True, disabled=ai_disabled,
                         help="Requires a Groq key and an industry"):
                try:
                    with st.spinner("Reading the market..."):
                        suggestions = suggest_campaign_targeting(
                            groq_api_key=credentials["groq_api_key"],
                            industry=industry, country=country, campaign_goal=campaign_goal,
                        )
                    st.session_state.titles_text = ", ".join(suggestions.job_titles)
                    st.session_state.outreach_angle = suggestions.outreach_angle
                    st.session_state.suggested_limit = suggestions.recommended_limit
                    st.success("Suggestions applied.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Suggestion failed: {e}")
            if ai_disabled:
                st.caption("Add a Groq key + industry to enable.")

        st.divider()
        st.markdown('<p class="section-label">Volume</p>', unsafe_allow_html=True)
        v1, v2 = st.columns(2)
        with v1:
            limit_mode = st.radio("Limit type", ["Preset", "Custom"], horizontal=True, label_visibility="collapsed")
            if limit_mode == "Preset":
                limit = st.select_slider(
                    "Lead count", options=[1, 3, 5, 10, 25, 50, 100],
                    value=min(st.session_state.suggested_limit, 100),
                )
            else:
                limit = st.number_input("Custom lead count", min_value=1, max_value=5000, value=100)
        with v2:
            skip_verification = st.toggle("Skip email verification", value=False)
            st.caption("Verification checks format and mail server — it never emails your leads.")

    st.session_state.campaign_name = campaign_name
    st.session_state.industry = industry
    st.session_state.campaign_goal = campaign_goal
    st.session_state.country = country
    st.session_state.country_search = country_search
    st.session_state.titles_text = titles_text
    st.session_state.outreach_angle = outreach_angle

    return {
        "campaign_name": campaign_name.strip(),
        "country": country,
        "titles": [t.strip() for t in titles_text.split(",") if t.strip()],
        "limit": int(limit),
        "skip_verification": skip_verification,
    }


def render_delivery_card() -> dict:
    with st.container(border=True):
        st.markdown(
            '<p class="section-label"><span class="stage-num">02</span>Delivery</p>'
            '<p class="card-title">Where should results land?</p>'
            '<p class="card-desc">Optionally email the finished list to a client and post a summary to Slack.</p>',
            unsafe_allow_html=True,
        )

        d1, d2 = st.columns(2)
        with d1:
            st.markdown('<p class="section-label">Client email</p>', unsafe_allow_html=True)
            client_email = st.text_input(
                "Send results to (client email)", value=st.session_state.client_email,
                placeholder="client@company.com",
            )
            skip_client_email = st.toggle("Do not email client", value=False)
            email_provider = st.selectbox(
                "Your email provider", list(EMAIL_PROVIDERS.keys()),
                index=list(EMAIL_PROVIDERS.keys()).index(st.session_state.email_provider),
            )
            provider_cfg = EMAIL_PROVIDERS[email_provider]
            if provider_cfg.get("use_email_as_username", True):
                sender_email = st.text_input("Your email address", value=st.session_state.sender_email, placeholder="you@gmail.com")
            else:
                sender_email = st.text_input("From email (verified sender)", value=st.session_state.sender_email)
            email_password = st.text_input(
                provider_cfg["password_hint"], value=st.session_state.email_password, type="password",
            )
            st.caption(provider_cfg["password_help"])

        with d2:
            st.markdown('<p class="section-label">Team alerts</p>', unsafe_allow_html=True)
            slack_webhook_url = st.text_input(
                "Slack webhook URL (optional)", value=st.session_state.slack_webhook_url, type="password",
                help="Posts a summary with a dashboard link to your Slack channel.",
            )
            skip_slack = st.toggle("Do not send Slack alert", value=False)
            app_url = st.text_input("Dashboard URL (for Slack link)", value=st.session_state.app_url)

    st.session_state.client_email = client_email
    st.session_state.email_provider = email_provider
    st.session_state.sender_email = sender_email
    st.session_state.email_password = email_password
    st.session_state.slack_webhook_url = slack_webhook_url
    st.session_state.app_url = app_url

    smtp = {}
    if not skip_client_email and client_email.strip() and sender_email.strip() and email_password.strip():
        smtp = resolve_smtp_settings(email_provider, sender_email, email_password)

    return {
        "client_email": client_email.strip() or None,
        "skip_client_email": skip_client_email,
        "skip_slack": skip_slack,
        "slack_webhook_url": slack_webhook_url.strip(),
        "app_url": app_url.strip() or None,
        **smtp,
    }


def render_launch_card(credentials: dict, campaign: dict, delivery: dict) -> bool:
    checks = [
        ("Apify token added", bool(credentials["apify_token"])),
        ("Groq API key added", bool(credentials["groq_api_key"])),
        ("At least one job title", bool(campaign["titles"])),
        (
            "Client email settings complete",
            delivery["skip_client_email"] or not delivery["client_email"] or bool(delivery.get("smtp_host")),
        ),
    ]
    ready = all(passed for _, passed in checks)

    with st.container(border=True):
        st.markdown(
            '<p class="section-label"><span class="stage-num">03</span>Launch</p>'
            '<p class="card-title">Ready when you are.</p>'
            f'<p class="card-desc">Targeting <b>{len(campaign["titles"]) or 0}</b> title(s) in '
            f'<b>{campaign["country"]}</b> · up to <b>{campaign["limit"]}</b> leads.</p>',
            unsafe_allow_html=True,
        )

        cols = st.columns(2)
        for i, (text, passed) in enumerate(checks):
            icon_cls = "pass" if passed else "fail"
            icon = "✓" if passed else "!"
            cols[i % 2].markdown(
                f'<div class="check-item"><span class="check-icon {icon_cls}">{icon}</span>'
                f'<span class="check-text {icon_cls}">{text}</span></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        run_clicked = st.button(
            "▶  Run campaign", type="primary", use_container_width=True, disabled=not ready,
        )
        if not ready:
            st.caption("Resolve the items above to enable launch.")

    return run_clicked


def render_results(result) -> None:
    with st.container(border=True):
        st.markdown(
            '<p class="section-label"><span class="stage-num">04</span>Results</p>'
            '<p class="card-title">Campaign summary</p>',
            unsafe_allow_html=True,
        )

        m = [
            ("Total leads", result.total_leads, ""),
            ("Valid emails", result.valid_leads, "ok"),
            ("Slack", "Sent" if result.slack_sent else "—", "ok" if result.slack_sent else "pending"),
            ("Client email", "Sent" if result.email_sent else "—", "ok" if result.email_sent else "pending"),
            ("Export", "Ready" if result.csv_filename else "—", "ok" if result.csv_filename else "pending"),
        ]
        cards = "".join(
            f'<div class="metric-card {cls}"><div class="m-label">{label}</div><div class="m-value">{value}</div></div>'
            for label, value, cls in m
        )
        st.markdown(f'<div class="metric-row">{cards}</div>', unsafe_allow_html=True)

        if result.warnings:
            for warning in result.warnings:
                st.warning(warning)

        if not result.processed_leads:
            st.info("No leads returned for this run. Try a broader country or title list.")
            return

        display_df = pd.DataFrame(result.processed_leads).drop(columns=["Is Valid Email"], errors="ignore")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="⬇  Download CSV",
            data=leads_to_csv_bytes(result.processed_leads),
            file_name=f"campaign_leads_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )


def main() -> None:
    init_session_state()
    apply_theme()
    credentials = render_sidebar()
    render_header()

    active_stage = 3 if st.session_state.last_result else 0
    render_rail(active_stage)

    campaign = render_campaign_card(credentials)
    st.write("")
    delivery = render_delivery_card()
    st.write("")
    run_clicked = render_launch_card(credentials, campaign, delivery)

    if run_clicked:
        render_rail(2)
        progress_bar = st.progress(0, text="Starting...")
        log_area = st.empty()
        logs: list[str] = []

        def on_progress(step, message, current=0, total=0):
            logs.append(message)
            log_area.code("\n".join(logs[-14:]), language=None)
            if total > 0:
                progress_bar.progress(min(current / total, 1.0), text=message)
            else:
                progress_bar.progress(0.05, text=message)

        config = PipelineConfig(
            country=campaign["country"],
            titles=campaign["titles"],
            limit=campaign["limit"],
            skip_verification=campaign["skip_verification"],
            skip_slack=delivery["skip_slack"] or not delivery["slack_webhook_url"],
            skip_client_email=delivery["skip_client_email"] or not delivery["client_email"],
            apify_token=credentials["apify_token"],
            groq_api_key=credentials["groq_api_key"],
            slack_webhook_url=delivery["slack_webhook_url"] or None,
            app_url=delivery["app_url"],
            client_email=delivery["client_email"],
            smtp_host=delivery.get("smtp_host"),
            smtp_port=delivery.get("smtp_port"),
            smtp_user=delivery.get("smtp_user"),
            smtp_password=delivery.get("smtp_password"),
            smtp_from=delivery.get("smtp_from"),
        )

        try:
            result = run_pipeline(config, on_progress=on_progress)
            st.session_state.last_result = result
            progress_bar.progress(1.0, text="Complete")
            st.success("Campaign completed.")
            st.rerun()
        except Exception as e:
            progress_bar.empty()
            st.error(f"Campaign failed: {e}")
            return

    if st.session_state.last_result:
        st.write("")
        render_results(st.session_state.last_result)


if __name__ == "__main__":
    main()