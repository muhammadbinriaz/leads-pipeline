import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from src.enricher import fallback_clean_company, reset_llm_cache
from src.exporter import export_leads_to_csv, leads_to_csv_bytes
from src.integrations import send_client_completion_email, send_slack_completion_alert
from src.scraper import scrape_leads
from src.verifier import verify_lead_email


ProgressCallback = Callable[[str, str, int, int], None]


def _first(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"none", "null", "n/a"}:
            return text
    return default


def _dict_get(obj: Any, *keys: str) -> Any:
    if not isinstance(obj, dict):
        return None
    for key in keys:
        if obj.get(key) not in (None, ""):
            return obj.get(key)
    return None


@dataclass
class PipelineConfig:
    country: str
    titles: list[str]
    limit: int
    output_dir: str = "output"
    skip_verification: bool = False
    skip_slack: bool = False
    skip_client_email: bool = False
    campaign_name: str = ""
    countries: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    cities: list[str] = field(default_factory=list)
    industries: list[str] = field(default_factory=list)
    company_sizes: list[str] = field(default_factory=list)
    revenue_bands: list[str] = field(default_factory=list)
    seniority: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    has_email: bool = True
    has_phone: bool = False
    apify_token: Optional[str] = None
    groq_api_key: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    app_url: Optional[str] = None
    client_email: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None


@dataclass
class PipelineResult:
    processed_leads: list[dict] = field(default_factory=list)
    csv_path: Optional[str] = None
    total_leads: int = 0
    valid_leads: int = 0
    slack_sent: bool = False
    email_sent: bool = False
    csv_filename: Optional[str] = None
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


def extract_lead_fields(lead: dict) -> dict:
    organization = lead.get("organization") or lead.get("company") or {}
    if not isinstance(organization, dict):
        organization = {}

    first_name = _first(lead.get("firstName"), lead.get("first_name"))
    last_name = _first(lead.get("lastName"), lead.get("last_name"))
    full_name = _first(
        lead.get("name"),
        lead.get("fullName"),
        lead.get("full_name"),
        f"{first_name} {last_name}".strip(),
        default="Unknown",
    )

    city = _first(
        lead.get("city"),
        lead.get("personCity"),
        _dict_get(organization, "city"),
    )
    state = _first(
        lead.get("state"),
        lead.get("personState"),
        _dict_get(organization, "state"),
    )
    country = _first(
        lead.get("country"),
        lead.get("personCountry"),
        lead.get("personLocationCountry"),
        _dict_get(organization, "country"),
    )
    location = ", ".join(part for part in [city, state, country] if part)
    headquarters = _first(
        _dict_get(organization, "headquarters", "hq", "rawAddress", "address"),
        lead.get("companyAddress"),
        lead.get("headquarters"),
        location,
    )

    result = {
        "name": full_name,
        "email": _first(lead.get("email"), lead.get("emailAddress"), lead.get("workEmail"), default="No Email Found"),
        "title": _first(lead.get("title"), lead.get("jobTitle"), lead.get("headline"), default="No Title"),
        "phone": _first(
            lead.get("phone"),
            lead.get("phoneNumber"),
            lead.get("mobilePhone"),
            lead.get("directPhone"),
            lead.get("corporatePhone"),
        ),
        "raw_company": _first(
            lead.get("companyName"),
            lead.get("organizationName"),
            lead.get("company"),
            _dict_get(organization, "name"),
            default="Unknown Company",
        ),
        "website": "",
        "description": _first(
            lead.get("companyDescription"),
            lead.get("orgDescription"),
            _dict_get(organization, "shortDescription", "description"),
            default="No description available.",
        ),
        "linkedin": _first(
            lead.get("linkedin"),
            lead.get("linkedinUrl"),
            lead.get("personLinkedinUrl"),
            lead.get("linkedin_url"),
            lead.get("socialUrl"),
        ),
        "company_linkedin": _first(
            lead.get("companyLinkedin"),
            lead.get("companyLinkedinUrl"),
            lead.get("organizationLinkedinUrl"),
            _dict_get(organization, "linkedinUrl", "linkedin_url"),
        ),
        "industry": _first(
            lead.get("industry"),
            _dict_get(organization, "industry"),
        ),
        "company_size": _first(
            lead.get("companySize"),
            lead.get("employees"),
            lead.get("estimatedNumEmployees"),
            _dict_get(organization, "estimatedNumEmployees", "employees", "size"),
        ),
        "revenue": _first(
            lead.get("revenue"),
            lead.get("annualRevenue"),
            _dict_get(organization, "annualRevenue", "revenue"),
        ),
        "headquarters": headquarters,
        "location": location,
        "source": _first(lead.get("source"), default="apify"),
    }

    website = _first(
        lead.get("website"),
        lead.get("companyWebsite"),
        lead.get("organizationWebsite"),
        lead.get("domain"),
        lead.get("companyDomain"),
        lead.get("primaryDomain"),
        _dict_get(organization, "websiteUrl", "website", "primaryDomain", "domain"),
    )
    if not website:
        email = result["email"]
        if "@" in email and email.lower() != "no email found":
            domain = email.split("@", 1)[1].strip().lower()
            if domain and domain not in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}:
                website = domain
    result["website"] = website
    return result


def _extract_lead_fields(lead: dict) -> dict:
    return extract_lead_fields(lead)


def run_pipeline(
    config: PipelineConfig,
    on_progress: Optional[ProgressCallback] = None,
) -> PipelineResult:
    result = PipelineResult()
    _apply_credentials(config)

    if not os.getenv("APIFY_TOKEN"):
        raise ValueError("Missing APIFY_TOKEN. Add your API key to continue.")

    _notify(on_progress, "scrape", f"Scraping up to {config.limit} leads in {config.country}...")
    raw_leads = scrape_leads(
        config.country,
        config.titles,
        config.limit,
        countries=config.countries or None,
        states=config.states or None,
        cities=config.cities or None,
        industries=config.industries or None,
        company_sizes=config.company_sizes or None,
        revenue_bands=config.revenue_bands or None,
        seniority=config.seniority or None,
        functions=config.functions or None,
        has_email=config.has_email,
        has_phone=config.has_phone,
    )
    _notify(on_progress, "scrape", f"Scraped {len(raw_leads)} leads.", len(raw_leads), config.limit)

    total = len(raw_leads)
    for idx, lead in enumerate(raw_leads, 1):
        fields = extract_lead_fields(lead)
        name = fields["name"]
        _notify(on_progress, "process", f"Processing {name} ({idx}/{total})...", idx, total)

        if config.skip_verification:
            verify_status, is_valid_email = "Not Checked", True
        else:
            _notify(on_progress, "verify", f"Verifying email for {name}...", idx, total)
            verify_status, is_valid_email = verify_lead_email(fields["email"])

        clean_company = fallback_clean_company(fields["raw_company"])
        if clean_company == "Your Company":
            clean_company = fields["raw_company"]

        result.processed_leads.append({
            "Full Name": name,
            "Title": fields["title"],
            "Email": fields["email"],
            "Verification Status": verify_status,
            "Is Valid Email": is_valid_email,
            "Phone": fields["phone"],
            "Person LinkedIn": fields["linkedin"],
            "LinkedIn URL": fields["linkedin"],
            "Original Company Name": fields["raw_company"],
            "Cleaned Company Name": clean_company,
            "Company Name": clean_company or fields["raw_company"],
            "Company Website": fields["website"],
            "Company LinkedIn": fields["company_linkedin"],
            "Industry": fields["industry"],
            "Company Size": fields["company_size"],
            "Revenue": fields["revenue"],
            "Headquarters": fields["headquarters"],
            "Location": fields["location"],
            "Source": fields["source"],
            "Campaign Name": config.campaign_name,
            "Company Description": fields["description"],
        })

    result.total_leads = len(result.processed_leads)
    result.valid_leads = sum(1 for lead in result.processed_leads if lead["Is Valid Email"])

    _notify(on_progress, "export", "Saving CSV export...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_bytes: Optional[bytes] = None
    try:
        result.csv_path = export_leads_to_csv(result.processed_leads, config.output_dir, config.country, timestamp)
        result.csv_filename = os.path.basename(result.csv_path)
        csv_bytes = leads_to_csv_bytes(result.processed_leads)
    except Exception as exc:
        result.warnings.append(f"CSV export failed: {exc}")

    if not config.skip_slack:
        _notify(on_progress, "slack", "Sending Slack notification...")
        try:
            send_slack_completion_alert(
                country=config.country,
                titles=config.titles,
                total_leads=result.total_leads,
                valid_leads=result.valid_leads,
                app_url=config.app_url,
                csv_filename=result.csv_filename,
            )
            result.slack_sent = True
        except Exception as exc:
            result.warnings.append(f"Slack alert failed: {exc}")

    if not config.skip_client_email and config.client_email and csv_bytes and result.csv_filename:
        _notify(on_progress, "email", f"Sending completion email to {config.client_email}...")
        try:
            send_client_completion_email(
                to_email=config.client_email,
                country=config.country,
                titles=config.titles,
                total_leads=result.total_leads,
                valid_leads=result.valid_leads,
                csv_bytes=csv_bytes,
                csv_filename=result.csv_filename,
                app_url=config.app_url,
                smtp_host=config.smtp_host,
                smtp_port=config.smtp_port,
                smtp_user=config.smtp_user,
                smtp_password=config.smtp_password,
                smtp_from=config.smtp_from,
            )
            result.email_sent = True
        except Exception as exc:
            result.warnings.append(f"Client email failed: {exc}")

    _notify(on_progress, "done", "Pipeline complete.", result.total_leads, result.total_leads)
    return result
