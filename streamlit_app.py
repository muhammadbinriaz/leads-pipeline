import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.exporter import leads_to_csv_bytes
from src.pipeline_runner import PipelineConfig, run_pipeline

load_dotenv()

DEFAULT_APP_URL = "https://leads-pipeline-8oblh2wh9zf7frv8jyhfyp.streamlit.app/"

st.set_page_config(
    page_title="AI Lead Pipeline",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

BRANDING_HIDE_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    a[href*="github.com"] {display: none !important;}
    .viewerBadge_container__r5tak {display: none !important;}
    .viewerBadge_link__qRIco {display: none !important;}
</style>
"""

THEME_CSS = {
    "dark": """
    <style>
        .stApp { background-color: #0f172a; color: #f8fafc; }
        [data-testid="stAppViewContainer"] { background-color: #0f172a; }
        [data-testid="stSidebar"] { background-color: #0b1220; }
        .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem; color: #f8fafc; }
        .sub-header { color: #94a3b8; margin-bottom: 1.5rem; }
        [data-testid="stMetricValue"] { color: #f8fafc; }
    </style>
    """,
    "light": """
    <style>
        .stApp { background-color: #f8fafc; color: #0f172a; }
        [data-testid="stAppViewContainer"] { background-color: #f8fafc; }
        [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        .main-header { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem; color: #0f172a; }
        .sub-header { color: #475569; margin-bottom: 1.5rem; }
        [data-testid="stMetricValue"] { color: #0f172a; }
        [data-testid="stMetricLabel"] { color: #475569; }
    </style>
    """,
}


def apply_theme() -> None:
    theme = st.session_state.get("theme", "dark")
    st.markdown(BRANDING_HIDE_CSS, unsafe_allow_html=True)
    st.markdown(THEME_CSS.get(theme, THEME_CSS["dark"]), unsafe_allow_html=True)


def init_session_state() -> None:
    defaults = {
        "theme": "dark",
        "apify_token": os.getenv("APIFY_TOKEN", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "app_url": os.getenv("APP_URL", DEFAULT_APP_URL),
        "client_email": os.getenv("CLIENT_EMAIL", ""),
        "use_sendgrid": False,
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_from": os.getenv("SMTP_FROM", ""),
        "last_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    col_title, col_theme = st.columns([5, 1])
    with col_title:
        st.markdown('<p class="main-header">🚀 AI Lead Generation Pipeline</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sub-header">Scrape, verify, enrich, and export B2B leads — no terminal required.</p>',
            unsafe_allow_html=True,
        )
    with col_theme:
        label = "☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark"
        if st.button(label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()


def render_sidebar() -> dict:
    st.sidebar.markdown("## 🔐 API Credentials")
    st.sidebar.caption("Keys stay in your browser session only. They are not saved to disk.")

    apify_token = st.sidebar.text_input("Apify Token", value=st.session_state.apify_token, type="password")
    groq_api_key = st.sidebar.text_input("Groq API Key", value=st.session_state.groq_api_key, type="password")

    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔔 Notifications")

    app_url = st.sidebar.text_input(
        "Dashboard URL (for Slack link)",
        value=st.session_state.app_url,
        help="Included in Slack alerts so your team can open the app and download CSV.",
    )
    slack_webhook_url = st.sidebar.text_input(
        "Slack Webhook URL (optional)",
        value=st.session_state.slack_webhook_url,
        type="password",
        help="Posts a completion alert with a dashboard link to your Slack channel.",
    )

    client_email = st.sidebar.text_input(
        "Client email (optional)",
        value=st.session_state.client_email,
        help="Receives a summary email with the CSV attached when a run completes.",
    )

    use_sendgrid = st.sidebar.checkbox(
        "Use SendGrid SMTP preset",
        value=st.session_state.use_sendgrid,
        help="Sets host to smtp.sendgrid.net and username to apikey. Paste your SendGrid API key as SMTP password.",
    )

    if use_sendgrid:
        smtp_host = "smtp.sendgrid.net"
        smtp_port = 587
        smtp_user = "apikey"
        smtp_password = st.sidebar.text_input("SendGrid API Key", value=st.session_state.smtp_password, type="password")
        smtp_from = st.sidebar.text_input("From email (verified in SendGrid)", value=st.session_state.smtp_from)
    else:
        smtp_host = st.sidebar.text_input("SMTP Host", value=st.session_state.smtp_host or "smtp.gmail.com")
        smtp_port = st.sidebar.number_input("SMTP Port", min_value=1, max_value=65535, value=st.session_state.smtp_port)
        smtp_user = st.sidebar.text_input("SMTP Username", value=st.session_state.smtp_user)
        smtp_password = st.sidebar.text_input("SMTP Password", value=st.session_state.smtp_password, type="password")
        smtp_from = st.sidebar.text_input("From email", value=st.session_state.smtp_from or st.session_state.smtp_user)

    st.session_state.apify_token = apify_token
    st.session_state.groq_api_key = groq_api_key
    st.session_state.slack_webhook_url = slack_webhook_url
    st.session_state.app_url = app_url
    st.session_state.client_email = client_email
    st.session_state.use_sendgrid = use_sendgrid
    st.session_state.smtp_host = smtp_host
    st.session_state.smtp_port = int(smtp_port)
    st.session_state.smtp_user = smtp_user
    st.session_state.smtp_password = smtp_password
    st.session_state.smtp_from = smtp_from

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "**Lead email verification** checks scraped addresses (format + mail server). "
        "It does not email leads.\n\n"
        "**Client email** sends the finished CSV to the address above.\n\n"
        "**Slack** alerts your team with stats + dashboard link."
    )
    st.sidebar.info("Start with limit **1–3** when testing to save Apify credits.")

    return {
        "apify_token": apify_token.strip(),
        "groq_api_key": groq_api_key.strip(),
        "slack_webhook_url": slack_webhook_url.strip(),
        "app_url": app_url.strip() or None,
        "client_email": client_email.strip() or None,
        "smtp_host": smtp_host.strip() or None,
        "smtp_port": int(smtp_port),
        "smtp_user": smtp_user.strip() or None,
        "smtp_password": smtp_password.strip() or None,
        "smtp_from": smtp_from.strip() or None,
    }


def render_campaign_form() -> dict:
    col1, col2 = st.columns(2)

    with col1:
        country = st.selectbox(
            "Target Country",
            ["United States", "United Kingdom", "Canada", "Australia", "Germany", "France", "India", "Pakistan"],
            index=0,
        )
        titles = st.text_input("Target Job Titles", value="CEO, Founder, VP of Sales")

    with col2:
        limit_mode = st.radio("Lead limit mode", ["Quick select (slider)", "Custom number"], horizontal=True)
        if limit_mode == "Quick select (slider)":
            limit = st.slider("Lead Limit", min_value=1, max_value=100, value=5, step=1)
        else:
            limit = st.number_input("Custom Lead Limit", min_value=1, max_value=5000, value=100, step=1)

        skip_verification = st.checkbox("Skip email verification", value=False)
        skip_slack = st.checkbox("Skip Slack notification", value=False)
        skip_client_email = st.checkbox("Skip client email", value=False)

    return {
        "country": country,
        "titles": [t.strip() for t in titles.split(",") if t.strip()],
        "limit": int(limit),
        "skip_verification": skip_verification,
        "skip_slack": skip_slack,
        "skip_client_email": skip_client_email,
    }


def render_results(result) -> None:
    st.markdown("### 📊 Campaign Results")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Leads", result.total_leads)
    m2.metric("Valid Emails", result.valid_leads)
    m3.metric("Slack Sent", "Yes" if result.slack_sent else "No")
    m4.metric("Email Sent", "Yes" if result.email_sent else "No")
    m5.metric("CSV Ready", "Yes" if result.csv_filename else "No")

    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)

    if not result.processed_leads:
        st.info("No leads were returned for this run.")
        return

    display_df = pd.DataFrame(result.processed_leads).drop(columns=["Is Valid Email"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️ Download CSV",
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

    campaign = render_campaign_form()
    st.markdown("---")

    if st.button("▶️ Run Pipeline", type="primary", use_container_width=True):
        if not credentials["apify_token"] or not credentials["groq_api_key"]:
            st.error("Please enter both Apify Token and Groq API Key in the sidebar.")
            return
        if not campaign["titles"]:
            st.error("Please enter at least one job title.")
            return
        if (
            not campaign["skip_client_email"]
            and credentials["client_email"]
            and not all([credentials["smtp_host"], credentials["smtp_user"], credentials["smtp_password"], credentials["smtp_from"]])
        ):
            st.error("Client email is set but SMTP settings are incomplete. Fill SMTP fields or check Skip client email.")
            return

        progress_bar = st.progress(0, text="Starting pipeline...")
        log_area = st.empty()
        logs: list[str] = []

        def on_progress(step, message, current=0, total=0):
            logs.append(message)
            log_area.code("\n".join(logs[-12:]), language=None)
            if total > 0:
                progress_bar.progress(min(current / total, 1.0), text=message)
            else:
                progress_bar.progress(0.05, text=message)

        config = PipelineConfig(
            country=campaign["country"],
            titles=campaign["titles"],
            limit=campaign["limit"],
            skip_verification=campaign["skip_verification"],
            skip_slack=campaign["skip_slack"] or not credentials["slack_webhook_url"],
            skip_client_email=campaign["skip_client_email"] or not credentials["client_email"],
            apify_token=credentials["apify_token"],
            groq_api_key=credentials["groq_api_key"],
            slack_webhook_url=credentials["slack_webhook_url"] or None,
            app_url=credentials["app_url"],
            client_email=credentials["client_email"],
            smtp_host=credentials["smtp_host"],
            smtp_port=credentials["smtp_port"],
            smtp_user=credentials["smtp_user"],
            smtp_password=credentials["smtp_password"],
            smtp_from=credentials["smtp_from"],
        )

        try:
            with st.spinner("Running pipeline... this may take a few minutes."):
                result = run_pipeline(config, on_progress=on_progress)
            st.session_state.last_result = result
            progress_bar.progress(1.0, text="Pipeline complete!")
            st.success("Campaign finished successfully.")
        except Exception as e:
            progress_bar.empty()
            st.error(f"Pipeline failed: {e}")
            return

    if st.session_state.last_result:
        render_results(st.session_state.last_result)


if __name__ == "__main__":
    main()
