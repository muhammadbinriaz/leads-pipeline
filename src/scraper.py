import os
from apify_client import ApifyClient

def scrape_leads(country: str, titles: list[str], limit: int) -> list[dict]:
    """
    Triggers the Apify Apollo Scraper and returns raw lead dicts.
    """
    apify_token = os.getenv("APIFY_TOKEN")
    apify_client = ApifyClient(apify_token)

    run_input = {
        "personLocationCountryIncludes": [country] if country else ["United States"],
        "personTitleIncludes": titles,
        "totalResults": limit,
        "resetProgress": False
    }

    print("⏳ Step 1: Triggering the Apify Apollo Scraper...")
    run = apify_client.actor("pipelinelabs/lead-scraper-apollo-zoominfo-lusha-ppe").call(run_input=run_input)
    print("✅ Scraping complete! Pulling raw dataset...")
    
    # Retrieve items from the default dataset
    raw_leads = apify_client.dataset(run.default_dataset_id).list_items().items
    return raw_leads
