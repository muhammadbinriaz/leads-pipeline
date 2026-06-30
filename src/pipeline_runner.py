import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional

from src.scraper import scrape_leads
from src.verifier import verify_lead_email
from src.enricher import process_lead_with_ai, reset_llm_cache
from src.exporter import export_leads_to_csv
from src.integrations import send_slack_completion_alert


ProgressCallback = Callable[[str, str, int, int], None]


@dataclass
class PipelineConfig:
    country: str
    titles: list[str]
    limit: int
    output_dir: str = "output"
    skip_verification: bool = False
    skip_slack: bool = False
    apify_token: Optional[str] = None
    groq_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None


@dataclass
class PipelineResult:
    processed_leads: list[dict] = field(default_factory=list)
    csv_path: Optional[str] = None
    total_leads: int = 0
    valid_leads: int = 0
    slack_sent: bool = False
    warnings: list[str] = field(default_factory=list)


def _notify(on_progress: Optional[ProgressCallback], step: str, message: str, current: int = 0, total: int = 0) -> None:
    if on_progress:
        on_progress(step, message, current, total)


def _apply_credentials(config: PipelineConfig) -> None:
    if config.apify_token:
        os.environ["APIFY_TOKEN"] = config.apify_token.strip()
    if config.groq_api_key:
        os.environ["GROQ_API_KEY"] = config.groq_api_key.strip()
        reset_llm_cache()
    if config.slack_webhook_url:
        os.environ["SLACK_WEBHOOK_URL"] = config.slack_webhook_url.strip()


def _extract_lead_fields(lead: dict) -> dict:
    return {
        "name": lead.get("name") or lead.get("fullName", "Unknown"),
        "email": lead.get("email") or lead.get("emailAddress", "No Email Found"),
        "title": lead.get("title") or lead.get("jobTitle", "No Title"),
        "raw_company": lead.get("companyName") or lead.get("organizationName", "Unknown Company"),
        "description": lead.get("companyDescription") or lead.get("orgDescription", "No description available."),
        "linkedin": lead.get("linkedin") or lead.get("linkedinUrl") or lead.get("personLinkedinUrl") or lead.get("socialUrl", ""),
    }


def run_pipeline(
    config: PipelineConfig,
    on_progress: Optional[ProgressCallback] = None,
) -> PipelineResult:
    result = PipelineResult()
    _apply_credentials(config)

    if not os.getenv("GROQ_API_KEY") or not os.getenv("APIFY_TOKEN"):
        raise ValueError("Missing GROQ_API_KEY or APIFY_TOKEN. Add your API keys to continue.")

    _notify(on_progress, "scrape", f"Scraping up to {config.limit} leads in {config.country}...")
    raw_leads = scrape_leads(config.country, config.titles, config.limit)
    _notify(on_progress, "scrape", f"Scraped {len(raw_leads)} leads.", len(raw_leads), config.limit)

    total = len(raw_leads)
    for idx, lead in enumerate(raw_leads, 1):
        fields = _extract_lead_fields(lead)
        name = fields["name"]
        _notify(on_progress, "process", f"Processing {name} ({idx}/{total})...", idx, total)

        if config.skip_verification:
            verify_status, is_valid_email = "Not Checked", True
        else:
            _notify(on_progress, "verify", f"Verifying email for {name}...", idx, total)
            verify_status, is_valid_email = verify_lead_email(fields["email"])

        _notify(on_progress, "enrich", f"AI enriching {name}...", idx, total)
        ai_data = process_lead_with_ai(name, fields["title"], fields["raw_company"], fields["description"])

        result.processed_leads.append({
            "Full Name": name,
            "Email": fields["email"],
            "Verification Status": verify_status,
            "Is Valid Email": is_valid_email,
            "Title": fields["title"],
            "Original Company Name": fields["raw_company"],
            "Cleaned Company Name": ai_data.clean_company_name,
            "Industry": ai_data.industry,
            "AI Icebreaker": ai_data.personalized_icebreaker,
            "Company Description": fields["description"],
            "LinkedIn URL": fields["linkedin"],
        })

    result.total_leads = len(result.processed_leads)
    result.valid_leads = sum(1 for lead in result.processed_leads if lead["Is Valid Email"])

    _notify(on_progress, "export", "Saving CSV export...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        result.csv_path = export_leads_to_csv(result.processed_leads, config.output_dir, config.country, timestamp)
    except Exception as e:
        result.warnings.append(f"CSV export failed: {e}")

    if not config.skip_slack:
        _notify(on_progress, "slack", "Sending Slack notification...")
        try:
            send_slack_completion_alert(
                country=config.country,
                titles=config.titles,
                total_leads=result.total_leads,
                valid_leads=result.valid_leads,
            )
            result.slack_sent = True
        except Exception as e:
            result.warnings.append(f"Slack alert failed: {e}")

    _notify(on_progress, "done", "Pipeline complete.", result.total_leads, result.total_leads)
    return result
