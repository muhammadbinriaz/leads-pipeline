from sqlalchemy.exc import IntegrityError

from backend.app.config import get_settings
from backend.app.database import SessionLocal
from backend.app.models import Campaign, Lead
from src.pipeline_runner import PipelineConfig, run_pipeline


def _norm_email(value: str) -> str | None:
    text = (value or "").strip().lower()
    if not text or text in {"no email found", "none", "n/a"}:
        return None
    return text


def _norm_linkedin(value: str) -> str | None:
    text = (value or "").strip().lower().rstrip("/")
    if not text:
        return None
    return text


def _lead_from_item(campaign: Campaign, item: dict, email_key: str | None, linkedin_key: str | None) -> Lead:
    return Lead(
        organization_id=campaign.organization_id,
        campaign_id=campaign.id,
        full_name=item.get("Full Name") or "",
        title=item.get("Title") or "",
        email=item.get("Email") or "",
        email_key=email_key,
        verification_status=item.get("Verification Status") or "",
        is_valid_email=bool(item.get("Is Valid Email")),
        phone=item.get("Phone") or "",
        person_linkedin=item.get("Person LinkedIn") or item.get("LinkedIn URL") or "",
        linkedin_key=linkedin_key,
        company_name=item.get("Company Name") or item.get("Cleaned Company Name") or "",
        company_website=item.get("Company Website") or "",
        company_linkedin=item.get("Company LinkedIn") or "",
        industry=item.get("Industry") or "",
        company_size=str(item.get("Company Size") or ""),
        revenue=str(item.get("Revenue") or ""),
        headquarters=item.get("Headquarters") or "",
        location=item.get("Location") or "",
        source=item.get("Source") or "apify",
        campaign_name=campaign.name,
        icebreaker="",
        company_description=item.get("Company Description") or "",
    )


def process_campaign(campaign_id: str) -> None:
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        db.close()
        return

    campaign.status = "running"
    campaign.progress_step = "scrape"
    campaign.progress_message = "Starting campaign..."
    campaign.error_message = ""
    db.commit()

    targeting = campaign.targeting or {}

    def on_progress(step: str, message: str, current: int = 0, total: int = 0) -> None:
        inner = SessionLocal()
        try:
            row = inner.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not row:
                return
            row.progress_step = step
            row.progress_message = message
            row.progress_current = current
            row.progress_total = total
            inner.commit()
        finally:
            inner.close()

    try:
        settings = get_settings()
        titles = targeting.get("titles") or ["CEO", "Founder"]
        country = targeting.get("country") or "United States"
        config = PipelineConfig(
            country=country,
            titles=titles,
            limit=int(targeting.get("limit") or 10),
            skip_slack=True,
            skip_client_email=True,
            campaign_name=campaign.name,
            countries=targeting.get("countries") or [],
            states=targeting.get("states") or [],
            cities=targeting.get("cities") or [],
            industries=targeting.get("industries") or [],
            company_sizes=targeting.get("company_sizes") or [],
            revenue_bands=targeting.get("revenue_bands") or [],
            seniority=targeting.get("seniority") or [],
            functions=targeting.get("functions") or [],
            has_email=bool(targeting.get("has_email", True)),
            has_phone=bool(targeting.get("has_phone", False)),
            apify_token=settings.apify_token or None,
            groq_api_key=settings.groq_api_key or None,
            app_url=settings.app_url,
        )

        existing_emails = {
            row[0]
            for row in db.query(Lead.email_key)
            .filter(Lead.organization_id == campaign.organization_id, Lead.email_key.isnot(None))
            .all()
        }
        existing_linkedin = {
            row[0]
            for row in db.query(Lead.linkedin_key)
            .filter(Lead.organization_id == campaign.organization_id, Lead.linkedin_key.isnot(None))
            .all()
        }

        result = run_pipeline(config, on_progress=on_progress)
        inserted = 0
        skipped = 0
        valid = 0

        for item in result.processed_leads:
            email_key = _norm_email(item.get("Email", ""))
            linkedin_key = _norm_linkedin(item.get("Person LinkedIn") or item.get("LinkedIn URL", ""))
            if email_key and email_key in existing_emails:
                skipped += 1
                continue
            if linkedin_key and linkedin_key in existing_linkedin:
                skipped += 1
                continue

            lead = _lead_from_item(campaign, item, email_key, linkedin_key)
            try:
                with db.begin_nested():
                    db.add(lead)
                    db.flush()
            except IntegrityError:
                skipped += 1
                continue

            inserted += 1
            if lead.is_valid_email:
                valid += 1
            if email_key:
                existing_emails.add(email_key)
            if linkedin_key:
                existing_linkedin.add(linkedin_key)

        campaign.total_leads = inserted
        campaign.valid_leads = valid
        campaign.skipped_dupes = skipped
        campaign.status = "ready"
        campaign.progress_step = "done"
        campaign.progress_message = f"Ready — {inserted} new leads, {skipped} duplicates skipped."
        campaign.progress_current = inserted
        campaign.progress_total = inserted
        if result.warnings:
            campaign.error_message = "; ".join(result.warnings)
        db.commit()
    except Exception as exc:
        db.rollback()
        failed = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if failed:
            failed.status = "failed"
            failed.error_message = str(exc)
            failed.progress_step = "failed"
            failed.progress_message = str(exc)
            db.commit()
        raise
    finally:
        db.close()
