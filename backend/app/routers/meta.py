from fastapi import APIRouter, Depends

from backend.app.auth import get_current_user
from backend.app.models import User
from src.constants import COUNTRIES
from src.templates import (
    COMPANY_SIZE_OPTIONS,
    FUNCTION_OPTIONS,
    ICP_TEMPLATES,
    INDUSTRY_OPTIONS,
    REVENUE_OPTIONS,
    SENIORITY_OPTIONS,
)

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/templates")
def list_templates(_: User = Depends(get_current_user)):
    return ICP_TEMPLATES


@router.get("/meta")
def meta(_: User = Depends(get_current_user)):
    return {
        "countries": COUNTRIES,
        "seniority": SENIORITY_OPTIONS,
        "functions": FUNCTION_OPTIONS,
        "company_sizes": COMPANY_SIZE_OPTIONS,
        "revenue_bands": REVENUE_OPTIONS,
        "industries": INDUSTRY_OPTIONS,
    }
