from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.database import get_db
from backend.app.jobs import process_campaign
from backend.app.models import Campaign, Lead, User
from backend.app.queue import get_queue
from backend.app.schemas import CampaignCreate, CampaignOut, LeadOut
from src.exporter import leads_to_csv_bytes
from src.templates import get_template

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def _lead_to_csv_row(lead: Lead) -> dict:
    return {
        "Full Name": lead.full_name,
        "Title": lead.title,
        "Email": lead.email,
        "Verification Status": lead.verification_status,
        "Phone": lead.phone,
        "Person LinkedIn": lead.person_linkedin,
        "Company Name": lead.company_name,
        "Company Website": lead.company_website,
        "Company LinkedIn": lead.company_linkedin,
        "Industry": lead.industry,
        "Company Size": lead.company_size,
        "Revenue": lead.revenue,
        "Headquarters": lead.headquarters,
        "Location": lead.location,
        "Source": lead.source,
        "Campaign Name": lead.campaign_name,
        "Company Description": lead.company_description,
    }


@router.get("", response_model=list[CampaignOut])
def list_campaigns(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Campaign)
        .filter(Campaign.organization_id == user.organization_id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return rows


@router.post("", response_model=CampaignOut)
def create_campaign(payload: CampaignCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    template = get_template(payload.template_id)
    if payload.template_id != "custom" and not template:
        raise HTTPException(status_code=400, detail="Unknown ICP template")

    targeting = payload.targeting.model_dump()
    campaign = Campaign(
        organization_id=user.organization_id,
        created_by=user.id,
        name=payload.name.strip(),
        template_id=payload.template_id,
        targeting=targeting,
        status="queued",
        progress_message="Queued",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    get_queue().enqueue(process_campaign, str(campaign.id), job_timeout=60 * 60)
    return campaign


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(campaign_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.organization_id == user.organization_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/leads", response_model=list[LeadOut])
def list_leads(
    campaign_id: UUID,
    verified: bool | None = Query(default=None),
    has_phone: bool | None = Query(default=None),
    has_linkedin: bool | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.organization_id == user.organization_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    query = db.query(Lead).filter(Lead.campaign_id == campaign.id)
    if verified is True:
        query = query.filter(Lead.is_valid_email.is_(True))
    if has_phone is True:
        query = query.filter(Lead.phone != "")
    if has_linkedin is True:
        query = query.filter(Lead.person_linkedin != "")
    return query.order_by(Lead.created_at.desc()).all()


@router.get("/{campaign_id}/export.csv")
def export_csv(campaign_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.organization_id == user.organization_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    leads = db.query(Lead).filter(Lead.campaign_id == campaign.id).all()
    payload = leads_to_csv_bytes([_lead_to_csv_row(lead) for lead in leads])
    filename = f"{campaign.name.replace(' ', '_').lower()}_leads.csv"
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
