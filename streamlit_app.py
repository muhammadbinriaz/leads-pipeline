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

DEFAULT_APP_URL = "https://leads-pipeline-8oblh2wh9zf7frv8jyhfyp.streamlit.app/"

st.set_page_config(
    page_title="Lead Pipeline",
    page_icon="LP",
    layout="wide",
    initial_sidebar_state="expanded",
)

BRANDING_HIDE_CSS = """
<style>
    #MainMenu, footer, header { visibility: hidden; }
    .stAppDeployButton, [data-testid="stToolbar"], [data-testid="stStatusWidget"] { display: none; }
    a[href*="github.com"], .viewerBadge_container__r5tak { display: none !important; }
</style>
"""

LIGHT_THEME_CSS = """
<style>
    .stApp { background-color: #f1f5f9 !important; }
    [data-testid="stAppViewContainer"] { background-color: #f1f5f9 !important; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] * { color: #1e293b !important; }
    .stApp, .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6, .stMarkdown, .stMarkdown p,
    [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] p, [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"] { color: #0f172a !important; }
    [data-testid="stMetricValue"] { color: #0f172a !important; }
    .page-title { font-size: 1.75rem; font-weight: 700; color: #0f172a !important; margin: 0; }
    .page-subtitle { color: #475569 !important; margin-top: 0.25rem; margin-bottom: 1.25rem; }
    .section-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #64748b !important; margin-bottom: 0.5rem; }
    div[data-baseweb="input"] input, div[data-baseweb="textarea"] textarea,
    div[data-baseweb="select"] > div { background-color: #ffffff !important; color: #0f172a !important; }
    [data-testid="stExpander"] summary p { color: #0f172a !important; }
</style>
"""

DARK_THEME_CSS = """
<style>
    .stApp { background-color: #0f172a !important; }
    [data-testid="stAppViewContainer"] { background-color: #0f172a !important; }
    [data-testid="stSidebar"] { background-color: #0b1220 !important; }
    .stApp, .stApp p, .stApp label, .stApp span, .stMarkdown p,
    [data-testid="stWidgetLabel"] p, [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] p { color: #e2e8f0 !important; }
    .page-title { font-size: 1.75rem; font-weight: 700; color: #f8fafc !important; margin: 0; }
    .page-subtitle { color: #94a3b8 !important; margin-top: 0.25rem; margin-bottom: 1.25rem; }
    .section-label { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #64748b !important; margin-bottom: 0.5rem; }
</style>
"""


def apply_theme() -> None:
    st.markdown(BRANDING_HIDE_CSS, unsafe_allow_html=True)
    css = LIGHT_THEME_CSS if st.session_state.get("theme") == "light" else DARK_THEME_CSS
    st.markdown(css, unsafe_allow_html=True)


def init_session_state() -> None:
    defaults = {
        "theme": "dark",
        "apify_token": os.getenv("APIFY_TOKEN", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "app_url": os.getenv("APP_URL", DEFAULT_APP_URL),
        "campaign_name": "",
        "industry": "",
        "campaign_goal": "",
        "country": "United States",
        "country_search": "",
        "titles_text": "CEO, Founder, VP of Sales",
        "outreach_angle": "",
        "client_email": os.getenv("CLIENT_EMAIL", ""),
        "email_provider": "Gmail",
        "sender_email": "",
        "email_password": "",
        "last_result": None,
        "suggested_limit": 10,
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


def render_header() -> None:
    left, right = st.columns([6, 1])
    with left:
        st.markdown('<p class="page-title">Lead Generation Pipeline</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="page-subtitle">Scrape, verify, enrich, and deliver B2B lead lists.</p>',
            unsafe_allow_html=True,
        )
    with right:
        label = "Light mode" if st.session_state.theme == "dark" else "Dark mode"
        if st.button(label, use_container_width=True, key="theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()


def render_sidebar() -> dict:
    st.sidebar.markdown('<p class="section-label">API credentials</p>', unsafe_allow_html=True)
    st.sidebar.caption("Stored in your browser session only.")

    apify_token = st.sidebar.text_input("Apify token", value=st.session_state.apify_token, type="password")
    groq_api_key = st.sidebar.text_input("Groq API key", value=st.session_state.groq_api_key, type="password")

    st.session_state.apify_token = apify_token
    st.session_state.groq_api_key = groq_api_key

    st.sidebar.markdown("---")
    st.sidebar.caption("Use a low lead limit (1–3) when testing to control Apify spend.")

    return {
        "apify_token": apify_token.strip(),
        "groq_api_key": groq_api_key.strip(),
    }


def render_campaign_tab(credentials: dict) -> dict:
    st.markdown('<p class="section-label">Campaign details</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        campaign_name = st.text_input(
            "Campaign name",
            value=st.session_state.campaign_name,
            placeholder="e.g. US SaaS Founders Q2",
        )
        industry = st.text_input(
            "Industry / niche",
            value=st.session_state.industry,
            placeholder="e.g. B2B SaaS, Real Estate, E-commerce",
        )
        campaign_goal = st.text_area(
            "Campaign goal (optional)",
            value=st.session_state.campaign_goal,
            placeholder="e.g. Outreach list for cold email to marketing leaders",
            height=80,
        )

    with c2:
        country_search = st.text_input("Search country", value=st.session_state.country_search, placeholder="Type to filter...")
        filtered = [c for c in COUNTRIES if country_search.lower() in c.lower()] if country_search else COUNTRIES
        default_idx = filtered.index(st.session_state.country) if st.session_state.country in filtered else 0
        country = st.selectbox("Target country", filtered, index=default_idx)
        outreach_angle = st.text_area(
            "Outreach angle (optional)",
            value=st.session_state.outreach_angle,
            placeholder="AI can suggest this, or write your own positioning.",
            height=80,
        )

    st.markdown('<p class="section-label">Targeting</p>', unsafe_allow_html=True)
    col_titles, col_ai = st.columns([4, 1])
    with col_titles:
        titles_text = st.text_area(
            "Job titles (comma-separated)",
            value=st.session_state.titles_text,
            height=100,
            placeholder="CEO, Founder, Head of Marketing",
        )
    with col_ai:
        st.write("")
        st.write("")
        ai_disabled = not credentials["groq_api_key"] or not industry.strip()
        if st.button("AI suggest", use_container_width=True, disabled=ai_disabled, help="Requires Groq key and industry"):
            try:
                with st.spinner("Generating suggestions..."):
                    suggestions = suggest_campaign_targeting(
                        groq_api_key=credentials["groq_api_key"],
                        industry=industry,
                        country=country,
                        campaign_goal=campaign_goal,
                    )
                st.session_state.titles_text = ", ".join(suggestions.job_titles)
                st.session_state.outreach_angle = suggestions.outreach_angle
                st.session_state.suggested_limit = suggestions.recommended_limit
                st.success("Suggestions applied.")
                st.rerun()
            except Exception as e:
                st.error(f"Suggestion failed: {e}")
        if ai_disabled:
            st.caption("Add Groq key + industry to enable.")

    st.markdown('<p class="section-label">Volume</p>', unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        limit_mode = st.radio("Limit type", ["Preset", "Custom"], horizontal=True, label_visibility="collapsed")
        if limit_mode == "Preset":
            limit = st.select_slider(
                "Lead count",
                options=[1, 3, 5, 10, 25, 50, 100],
                value=min(st.session_state.suggested_limit, 100),
            )
        else:
            limit = st.number_input("Custom lead count", min_value=1, max_value=5000, value=100)
    with v2:
        skip_verification = st.checkbox("Skip email verification", value=False)
        st.caption("Verification checks format and mail server — it does not send emails to leads.")

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


def render_delivery_tab() -> dict:
    st.markdown('<p class="section-label">Client delivery</p>', unsafe_allow_html=True)

    d1, d2 = st.columns(2)
    with d1:
        client_email = st.text_input(
            "Send results to (client email)",
            value=st.session_state.client_email,
            placeholder="client@company.com",
        )
        skip_client_email = st.checkbox("Do not email client", value=False)
        email_provider = st.selectbox(
            "Your email provider",
            list(EMAIL_PROVIDERS.keys()),
            index=list(EMAIL_PROVIDERS.keys()).index(st.session_state.email_provider),
        )
        provider_cfg = EMAIL_PROVIDERS[email_provider]
        if provider_cfg.get("use_email_as_username", True):
            sender_email = st.text_input("Your email address", value=st.session_state.sender_email, placeholder="you@gmail.com")
        else:
            sender_email = st.text_input("From email (verified sender)", value=st.session_state.sender_email)
        email_password = st.text_input(
            provider_cfg["password_hint"],
            value=st.session_state.email_password,
            type="password",
        )
        st.caption(provider_cfg["password_help"])

    with d2:
        st.markdown('<p class="section-label">Team alerts</p>', unsafe_allow_html=True)
        slack_webhook_url = st.text_input(
            "Slack webhook URL (optional)",
            value=st.session_state.slack_webhook_url,
            type="password",
            help="Posts a summary with dashboard link to your Slack channel.",
        )
        skip_slack = st.checkbox("Do not send Slack alert", value=False)
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


def render_results(result) -> None:
    st.markdown('<p class="section-label">Run summary</p>', unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total leads", result.total_leads)
    m2.metric("Valid emails", result.valid_leads)
    m3.metric("Slack", "Sent" if result.slack_sent else "—")
    m4.metric("Client email", "Sent" if result.email_sent else "—")
    m5.metric("Export", "Ready" if result.csv_filename else "—")

    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)

    if not result.processed_leads:
        st.info("No leads returned for this run.")
        return

    display_df = pd.DataFrame(result.processed_leads).drop(columns=["Is Valid Email"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="Download CSV",
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

    tab_campaign, tab_delivery, tab_results = st.tabs(["Campaign", "Delivery", "Results"])

    with tab_campaign:
        campaign = render_campaign_tab(credentials)
    with tab_delivery:
        delivery = render_delivery_tab()

    st.markdown("---")
    run_clicked = st.button("Run campaign", type="primary", use_container_width=True)

    if run_clicked:
        if not credentials["apify_token"] or not credentials["groq_api_key"]:
            st.error("Apify token and Groq API key are required in the sidebar.")
            return
        if not campaign["titles"]:
            st.error("Enter at least one job title.")
            return
        if (
            not delivery["skip_client_email"]
            and delivery["client_email"]
            and not delivery.get("smtp_host")
        ):
            st.error("Client email is set. Complete your email provider settings in the Delivery tab.")
            return

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
            with st.spinner("Processing campaign..."):
                result = run_pipeline(config, on_progress=on_progress)
            st.session_state.last_result = result
            progress_bar.progress(1.0, text="Complete")
            st.success("Campaign completed.")
        except Exception as e:
            progress_bar.empty()
            st.error(f"Campaign failed: {e}")
            return

    with tab_results:
        if st.session_state.last_result:
            render_results(st.session_state.last_result)
        else:
            st.info("Results will appear here after you run a campaign.")


if __name__ == "__main__":
    main()
