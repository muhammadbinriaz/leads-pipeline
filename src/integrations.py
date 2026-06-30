import os
import requests


def send_slack_completion_alert(
    country: str,
    titles: list[str],
    total_leads: int,
    valid_leads: int,
) -> None:
    """
    Sends a completion message to Slack using Incoming Webhook URL.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("Missing SLACK_WEBHOOK_URL")

    roles = ", ".join(titles) if titles else "target roles"
    message = (
        f"🔔 New Leads Ready! Scraped {total_leads} {country} leads for roles: {roles}. "
        f"{valid_leads} verified deliverable emails."
    )

    response = requests.post(webhook_url, json={"text": message}, timeout=15)
    response.raise_for_status()
