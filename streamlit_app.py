import os
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.exporter import leads_to_csv_bytes
from src.pipeline_runner import PipelineConfig, run_pipeline

load_dotenv()

st.set_page_config(
    page_title="AI Lead Pipeline",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .sub-header {
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stSidebar"] {
        background-color: #0b1220;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    defaults = {
        "apify_token": os.getenv("APIFY_TOKEN", ""),
        "groq_api_key": os.getenv("GROQ_API_KEY", ""),
        "slack_webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
        "last_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> dict:
    st.sidebar.markdown("## 🔐 API Credentials")
    st.sidebar.caption("Keys stay in your browser session only. They are not saved to disk.")

    apify_token = st.sidebar.text_input(
        "Apify Token",
        value=st.session_state.apify_token,
        type="password",
        help="Required for lead scraping.",
    )
    groq_api_key = st.sidebar.text_input(
        "Groq API Key",
        value=st.session_state.groq_api_key,
        type="password",
        help="Required for AI enrichment.",
    )
    slack_webhook_url = st.sidebar.text_input(
        "Slack Webhook URL (optional)",
        value=st.session_state.slack_webhook_url,
        type="password",
        help="Posts a completion alert to YOUR Slack channel — not to the scraped leads.",
    )

    st.session_state.apify_token = apify_token
    st.session_state.groq_api_key = groq_api_key
    st.session_state.slack_webhook_url = slack_webhook_url

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ How notifications work")
    st.sidebar.caption(
        "**Email verification** checks each lead's address (format + mail server). "
        "It does **not** send emails to anyone.\n\n"
        "**Slack** sends one summary message to the channel tied to your webhook when a run finishes."
    )
    st.sidebar.markdown("### 💡 Cost tip")
    st.sidebar.info("Start with limit **1–3** leads when testing to save Apify credits.")

    return {
        "apify_token": apify_token.strip(),
        "groq_api_key": groq_api_key.strip(),
        "slack_webhook_url": slack_webhook_url.strip(),
    }


def render_campaign_form() -> dict:
    col1, col2 = st.columns(2)

    with col1:
        country = st.selectbox(
            "Target Country",
            [
                "United States",
                "United Kingdom",
                "Canada",
                "Australia",
                "Germany",
                "France",
                "India",
                "Pakistan",
            ],
            index=0,
        )
        titles = st.text_input(
            "Target Job Titles",
            value="CEO, Founder, VP of Sales",
            help="Comma-separated list of roles to target.",
        )

    with col2:
        limit_mode = st.radio(
            "Lead limit mode",
            ["Quick select (slider)", "Custom number"],
            horizontal=True,
        )
        if limit_mode == "Quick select (slider)":
            limit = st.slider("Lead Limit", min_value=1, max_value=100, value=5, step=1)
        else:
            limit = st.number_input(
                "Custom Lead Limit",
                min_value=1,
                max_value=5000,
                value=100,
                step=1,
                help="Use for larger campaigns. Higher limits use more Apify credits.",
            )

        skip_verification = st.checkbox(
            "Skip email verification",
            value=False,
            help="When enabled, emails are not checked for valid format or mail server (MX).",
        )
        skip_slack = st.checkbox(
            "Skip Slack notification",
            value=False,
            help="When enabled, no completion message is sent to Slack.",
        )

    return {
        "country": country,
        "titles": [t.strip() for t in titles.split(",") if t.strip()],
        "limit": int(limit),
        "skip_verification": skip_verification,
        "skip_slack": skip_slack,
    }


def render_results(result) -> None:
    st.markdown("### 📊 Campaign Results")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Leads", result.total_leads)
    m2.metric("Valid Emails", result.valid_leads, help="Leads that passed email verification (or all if verification was skipped).")
    m3.metric("Slack Sent", "Yes" if result.slack_sent else "No")
    m4.metric("CSV Saved", "Yes" if result.csv_path else "No")

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
    credentials = render_sidebar()

    st.markdown('<p class="main-header">🚀 AI Lead Generation Pipeline</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Scrape, verify, enrich, and export B2B leads — no terminal required.</p>',
        unsafe_allow_html=True,
    )

    campaign = render_campaign_form()
    st.markdown("---")

    run_clicked = st.button("▶️ Run Pipeline", type="primary", use_container_width=True)

    if run_clicked:
        if not credentials["apify_token"] or not credentials["groq_api_key"]:
            st.error("Please enter both Apify Token and Groq API Key in the sidebar.")
            return
        if not campaign["titles"]:
            st.error("Please enter at least one job title.")
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
            apify_token=credentials["apify_token"],
            groq_api_key=credentials["groq_api_key"],
            slack_webhook_url=credentials["slack_webhook_url"] or None,
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
