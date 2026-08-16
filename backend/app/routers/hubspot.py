from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.config import get_settings
from backend.app.database import get_db
from backend.app.hubspot import authorization_url, exchange_code, is_configured, push_leads
from backend.app.models import Campaign, HubSpotConnection, Lead, User
from backend.app.schemas import HubSpotPushResult, HubSpotStatus
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/api/hubspot", tags=["hubspot"])


@router.get("/status", response_model=HubSpotStatus)
def status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(HubSpotConnection)
        .filter(HubSpotConnection.organization_id == user.organization_id)
        .first()
    )
    return HubSpotStatus(
        connected=bool(row),
        portal_id=row.portal_id if row else "",
        configured=is_configured(),
    )


@router.get("/authorize")
def authorize(user: User = Depends(get_current_user)):
    url = authorization_url(state=str(user.organization_id))
    return {"url": url}


@router.get("/callback")
def callback(code: str = Query(...), state: str = Query(...), db: Session = Depends(get_db)):
    settings = get_settings()
    payload = exchange_code(code)
    org_id = UUID(state)
    expires_in = int(payload.get("expires_in") or 1800)
    row = db.query(HubSpotConnection).filter(HubSpotConnection.organization_id == org_id).first()
    if not row:
        row = HubSpotConnection(organization_id=org_id, access_token="")
        db.add(row)
    row.access_token = payload["access_token"]
    row.refresh_token = payload.get("refresh_token") or ""
    row.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
    row.portal_id = str(payload.get("hub_id") or payload.get("hubId") or "")
    db.commit()
    return RedirectResponse(f"{settings.app_url}/settings?hubspot=connected")


@router.delete("")
def disconnect(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = (
        db.query(HubSpotConnection)
        .filter(HubSpotConnection.organization_id == user.organization_id)
        .first()
    )
    if row:
        db.delete(row)
        db.commit()
    return {"ok": True}


@router.post("/campaigns/{campaign_id}/push", response_model=HubSpotPushResult)
def push_campaign(campaign_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == campaign_id, Campaign.organization_id == user.organization_id)
        .first()
    )
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status != "ready":
        raise HTTPException(status_code=400, detail="Campaign is not ready to export")
    leads = db.query(Lead).filter(Lead.campaign_id == campaign.id).all()
    pushed, failed, errors = push_leads(db, user.organization_id, leads)
    return HubSpotPushResult(pushed=pushed, failed=failed, errors=errors)
