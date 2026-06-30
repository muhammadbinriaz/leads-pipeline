import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests


def _format_roles(titles: list[str]) -> str:
    return ", ".join(titles) if titles else "target roles"


def build_completion_summary(
    country: str,
    titles: list[str],
    total_leads: int,
    valid_leads: int,
    app_url: Optional[str] = None,
    csv_filename: Optional[str] = None,
) -> str:
    roles = _format_roles(titles)
    lines = [
        f"🔔 *New Leads Ready!*",
        f"Scraped *{total_leads}* leads in *{country}* for roles: {roles}.",
        f"*{valid_leads}* verified deliverable emails.",
    ]
    if csv_filename:
        lines.append(f"📎 Export file: `{csv_filename}`")
    if app_url:
        lines.append(f"🔗 <{app_url}|Open dashboard to preview & download CSV>")
    else:
        lines.append("Open the dashboard to preview and download the CSV export.")
    return "\n".join(lines)


def send_slack_completion_alert(
    country: str,
    titles: list[str],
    total_leads: int,
    valid_leads: int,
    app_url: Optional[str] = None,
    csv_filename: Optional[str] = None,
) -> None:
    """
    Sends a rich completion message to Slack using Incoming Webhook URL.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("Missing SLACK_WEBHOOK_URL")

    summary = build_completion_summary(
        country=country,
        titles=titles,
        total_leads=total_leads,
        valid_leads=valid_leads,
        app_url=app_url,
        csv_filename=csv_filename,
    )

    payload: dict = {"text": summary.replace("*", "").replace("`", "")}
    blocks: list[dict] = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary},
        }
    ]
    if app_url:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Leads Dashboard"},
                    "url": app_url,
                }
            ],
        })
    payload["blocks"] = blocks

    response = requests.post(webhook_url, json=payload, timeout=15)
    response.raise_for_status()


def send_client_completion_email(
    to_email: str,
    country: str,
    titles: list[str],
    total_leads: int,
    valid_leads: int,
    csv_bytes: bytes,
    csv_filename: str,
    app_url: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_user: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_from: Optional[str] = None,
) -> None:
    """
    Emails the client a completion summary with the CSV attached.
    Works with generic SMTP or SendGrid (smtp.sendgrid.net, user: apikey).
    """
    host = smtp_host or os.getenv("SMTP_HOST")
    port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
    user = smtp_user or os.getenv("SMTP_USER")
    password = smtp_password or os.getenv("SMTP_PASSWORD")
    from_email = smtp_from or os.getenv("SMTP_FROM") or user

    if not all([host, user, password, from_email, to_email]):
        raise ValueError("Missing SMTP settings or client email address.")

    roles = _format_roles(titles)
    subject = f"Lead campaign ready — {total_leads} leads ({country})"

    body_lines = [
        "Hello,",
        "",
        "Your lead generation campaign has finished successfully.",
        "",
        f"Country: {country}",
        f"Target roles: {roles}",
        f"Total leads processed: {total_leads}",
        f"Verified deliverable emails: {valid_leads}",
        "",
        f"The CSV export ({csv_filename}) is attached to this email.",
    ]
    if app_url:
        body_lines.extend(["", f"Dashboard: {app_url}"])
    body_lines.extend(["", "— AI Lead Pipeline"])

    message = MIMEMultipart()
    message["From"] = from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText("\n".join(body_lines), "plain"))

    attachment = MIMEApplication(csv_bytes, _subtype="csv")
    attachment.add_header("Content-Disposition", "attachment", filename=csv_filename)
    message.attach(attachment)

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(from_email, [to_email], message.as_string())
