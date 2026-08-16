from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    role: str
    organization_id: UUID
    organization_name: str

    model_config = {"from_attributes": True}


class TargetingIn(BaseModel):
    titles: list[str] = Field(default_factory=list)
    country: str = "United States"
    countries: list[str] = Field(default_factory=list)
    states: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    company_sizes: list[str] = Field(default_factory=list)
    revenue_bands: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    functions: list[str] = Field(default_factory=list)
    has_email: bool = True
    has_phone: bool = False
    limit: int = Field(default=25, ge=1, le=5000)


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    template_id: str = "custom"
    targeting: TargetingIn


class CampaignOut(BaseModel):
    id: UUID
    name: str
    template_id: str
    targeting: dict
    status: str
    progress_step: str
    progress_message: str
    progress_current: int
    progress_total: int
    total_leads: int
    valid_leads: int
    skipped_dupes: int
    error_message: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeadOut(BaseModel):
    id: UUID
    campaign_id: UUID
    full_name: str
    title: str
    email: str
    verification_status: str
    is_valid_email: bool
    phone: str
    person_linkedin: str
    company_name: str
    company_website: str
    company_linkedin: str
    industry: str
    company_size: str
    revenue: str
    headquarters: str
    location: str
    source: str
    campaign_name: str
    icebreaker: str
    company_description: str
    hubspot_id: str

    model_config = {"from_attributes": True}


class HubSpotStatus(BaseModel):
    connected: bool
    portal_id: str = ""
    configured: bool = False


class HubSpotPushResult(BaseModel):
    pushed: int
    failed: int
    errors: list[str] = Field(default_factory=list)
