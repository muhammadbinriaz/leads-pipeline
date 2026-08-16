from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import UUID

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.models import HubSpotConnection, Lead

HUBSPOT_AUTH = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN = "https://api.hubapi.com/oauth/v1/token"
HUBSPOT_BATCH = "https://api.hubapi.com/crm/v3/objects/contacts/batch/upsert"


def is_configured() -> bool:
    settings = get_settings()
    return bool(settings.hubspot_client_id and settings.hubspot_client_secret)


def authorization_url(state: str) -> str:
    settings = get_settings()
    if not is_configured():
        raise HTTPException(status_code=400, detail="HubSpot OAuth is not configured on the server.")
    query = urlencode({
        "client_id": settings.hubspot_client_id,
        "redirect_uri": settings.hubspot_redirect_uri,
        "scope": settings.hubspot_scopes,
        "state": state,
    })
    return f"{HUBSPOT_AUTH}?{query}"


def exchange_code(code: str) -> dict:
    settings = get_settings()
    response = requests.post(
        HUBSPOT_TOKEN,
        data={
            "grant_type": "authorization_code",
            "client_id": settings.hubspot_client_id,
            "client_secret": settings.hubspot_client_secret,
            "redirect_uri": settings.hubspot_redirect_uri,
            "code": code,
        },
        timeout=30,
    )
    if not response.ok:
        raise HTTPException(status_code=400, detail=f"HubSpot token exchange failed: {response.text}")
    return response.json()


def refresh_access_token(connection: HubSpotConnection) -> HubSpotConnection:
    settings = get_settings()
    if not connection.refresh_token:
        return connection
    response = requests.post(
        HUBSPOT_TOKEN,
        data={
            "grant_type": "refresh_token",
            "client_id": settings.hubspot_client_id,
            "client_secret": settings.hubspot_client_secret,
            "refresh_token": connection.refresh_token,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    connection.access_token = payload["access_token"]
    connection.refresh_token = payload.get("refresh_token") or connection.refresh_token
    expires_in = int(payload.get("expires_in") or 1800)
    connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)
    return connection


def ensure_token(db: Session, connection: HubSpotConnection) -> HubSpotConnection:
    expires = connection.expires_at
    if expires and expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires and expires <= datetime.now(timezone.utc) + timedelta(minutes=2):
        refresh_access_token(connection)
        db.add(connection)
        db.commit()
        db.refresh(connection)
    return connection


def _contact_properties(lead: Lead) -> dict:
    first, _, last = (lead.full_name or "").partition(" ")
    properties = {
        "email": lead.email,
        "firstname": first,
        "lastname": last,
        "jobtitle": lead.title,
        "phone": lead.phone,
        "company": lead.company_name,
        "website": lead.company_website,
        "industry": lead.industry,
        "city": lead.location,
        "hs_linkedin_url": lead.person_linkedin,
    }
    return {key: value for key, value in properties.items() if value}


def push_leads(db: Session, organization_id: UUID, leads: list[Lead]) -> tuple[int, int, list[str]]:
    connection = (
        db.query(HubSpotConnection)
        .filter(HubSpotConnection.organization_id == organization_id)
        .first()
    )
    if not connection:
        raise HTTPException(status_code=400, detail="HubSpot is not connected.")

    connection = ensure_token(db, connection)
    pushed = 0
    failed = 0
    errors: list[str] = []
    headers = {"Authorization": f"Bearer {connection.access_token}", "Content-Type": "application/json"}

    batch: list[Lead] = []
    for lead in leads:
        if not lead.email or lead.email.lower() in {"no email found", "n/a"}:
            failed += 1
            errors.append(f"{lead.full_name}: missing email")
            continue
        batch.append(lead)
        if len(batch) == 100:
            ok, bad, msgs = _upsert_batch(headers, batch)
            pushed += ok
            failed += bad
            errors.extend(msgs)
            _store_ids(db, batch, ok > 0)
            batch = []
    if batch:
        ok, bad, msgs = _upsert_batch(headers, batch)
        pushed += ok
        failed += bad
        errors.extend(msgs)
        _store_ids(db, batch, ok > 0)
    db.commit()
    return pushed, failed, errors[:20]


def _upsert_batch(headers: dict, batch: list[Lead]) -> tuple[int, int, list[str]]:
    inputs = []
    for lead in batch:
        inputs.append({
            "idProperty": "email",
            "id": lead.email,
            "properties": _contact_properties(lead),
        })
    response = requests.post(
        HUBSPOT_BATCH,
        headers=headers,
        json={"inputs": inputs},
        timeout=60,
    )
    if not response.ok:
        return 0, len(batch), [response.text[:300]]

    results = (response.json().get("results") or [])
    by_email = {item.get("properties", {}).get("email"): item.get("id") for item in results}
    for lead in batch:
        hubspot_id = by_email.get(lead.email)
        if hubspot_id:
            lead.hubspot_id = str(hubspot_id)
    return len(results), max(0, len(batch) - len(results)), []


def _store_ids(db: Session, batch: list[Lead], _ok: bool) -> None:
    for lead in batch:
        db.add(lead)
