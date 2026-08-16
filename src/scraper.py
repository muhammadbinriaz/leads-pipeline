import os
from typing import Any, Optional

from apify_client import ApifyClient

from src.templates import normalize_industries

APIFY_ACTOR_ID = "pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe"


def _clean_list(values: Optional[list[str]]) -> list[str]:
    if not values:
        return []
    return [str(v).strip() for v in values if v and str(v).strip()]


def build_actor_input(
    country: str,
    titles: list[str],
    limit: int,
    *,
    countries: Optional[list[str]] = None,
    states: Optional[list[str]] = None,
    cities: Optional[list[str]] = None,
    industries: Optional[list[str]] = None,
    company_sizes: Optional[list[str]] = None,
    revenue_bands: Optional[list[str]] = None,
    seniority: Optional[list[str]] = None,
    functions: Optional[list[str]] = None,
    has_email: bool = True,
    has_phone: bool = False,
    include_title_variants: bool = True,
    reset_progress: bool = False,
) -> dict[str, Any]:
    person_countries = _clean_list(countries) or ([country] if country else ["United States"])
    run_input: dict[str, Any] = {
        "personLocationCountryIncludes": person_countries,
        "personTitleIncludes": _clean_list(titles) or ["CEO", "Founder"],
        "totalResults": max(1, min(int(limit), 50000)),
        "includeTitleVariants": include_title_variants,
        "resetProgress": reset_progress,
        "hasEmail": bool(has_email),
        "hasPhone": bool(has_phone),
    }
    if has_email:
        run_input["emailStatusIncludes"] = ["verified"]

    optional_filters = {
        "personLocationStateIncludes": _clean_list(states),
        "personLocationCityIncludes": _clean_list(cities),
        "companyIndustryIncludes": normalize_industries(industries),
        "companySizeIncludes": _clean_list(company_sizes),
        "annualRevenueIncludes": _clean_list(revenue_bands),
        "seniorityIncludes": _clean_list(seniority),
        "functionIncludes": _clean_list(functions),
    }
    for key, value in optional_filters.items():
        if value:
            run_input[key] = value
    return run_input


def scrape_leads(
    country: str,
    titles: list[str],
    limit: int,
    *,
    countries: Optional[list[str]] = None,
    states: Optional[list[str]] = None,
    cities: Optional[list[str]] = None,
    industries: Optional[list[str]] = None,
    company_sizes: Optional[list[str]] = None,
    revenue_bands: Optional[list[str]] = None,
    seniority: Optional[list[str]] = None,
    functions: Optional[list[str]] = None,
    has_email: bool = True,
    has_phone: bool = False,
    include_title_variants: bool = True,
    reset_progress: bool = False,
) -> list[dict]:
    """Triggers the Apify B2B lead actor and returns raw lead dicts."""
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        raise ValueError("Missing APIFY_TOKEN")

    apify_client = ApifyClient(apify_token)
    run_input = build_actor_input(
        country,
        titles,
        limit,
        countries=countries,
        states=states,
        cities=cities,
        industries=industries,
        company_sizes=company_sizes,
        revenue_bands=revenue_bands,
        seniority=seniority,
        functions=functions,
        has_email=has_email,
        has_phone=has_phone,
        include_title_variants=include_title_variants,
        reset_progress=reset_progress,
    )

    print("⏳ Step 1: Triggering the Apify lead scraper...")
    run = apify_client.actor(APIFY_ACTOR_ID).call(run_input=run_input)
    print("✅ Scraping complete! Pulling raw dataset...")

    dataset_id = run.get("defaultDatasetId") if isinstance(run, dict) else getattr(run, "default_dataset_id", None)
    if not dataset_id:
        return []

    items: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        page = apify_client.dataset(dataset_id).list_items(offset=offset, limit=page_size)
        batch = page.items if hasattr(page, "items") else page.get("items", [])
        items.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return items
