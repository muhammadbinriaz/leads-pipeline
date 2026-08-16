import os

import requests
from email_validator import EmailNotValidError, validate_email


def _missing(email: str) -> bool:
    return not email or email.strip() == "" or email.lower() in {"no email found", "none", "n/a"}


def _mx_verify(email: str) -> tuple[str, bool]:
    try:
        validate_email(email, check_deliverability=True, timeout=5)
        return "MX Valid", True
    except EmailNotValidError as exc:
        return str(exc), False


def _hunter_verify(email: str, api_key: str) -> tuple[str, bool]:
    response = requests.get(
        "https://api.hunter.io/v2/email-verifier",
        params={"email": email, "api_key": api_key},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json().get("data") or {}
    result = (data.get("result") or data.get("status") or "unknown").lower()
    mapping = {
        "deliverable": ("Verified", True),
        "valid": ("Verified", True),
        "undeliverable": ("Undeliverable", False),
        "invalid": ("Invalid", False),
        "risky": ("Risky", False),
        "accept_all": ("Accept-all", False),
        "webmail": ("Webmail", True),
        "disposable": ("Disposable", False),
        "unknown": ("Unknown", False),
    }
    return mapping.get(result, (result.title(), result in {"deliverable", "valid"}))


def _zerobounce_verify(email: str, api_key: str) -> tuple[str, bool]:
    response = requests.get(
        "https://api.zerobounce.net/v2/validate",
        params={"api_key": api_key, "email": email},
        timeout=20,
    )
    response.raise_for_status()
    status = (response.json().get("status") or "unknown").lower()
    mapping = {
        "valid": ("Verified", True),
        "invalid": ("Invalid", False),
        "catch-all": ("Catch-all", False),
        "unknown": ("Unknown", False),
        "spamtrap": ("Spamtrap", False),
        "abuse": ("Abuse", False),
        "do_not_mail": ("Do not mail", False),
    }
    return mapping.get(status, (status.title(), status == "valid"))


def verify_lead_email(email: str) -> tuple[str, bool]:
    """
    Verifies an email with Hunter or ZeroBounce when configured.
    Falls back to syntax + MX lookup so campaigns still complete without a verify key.
    """
    if _missing(email):
        return "Missing Email", False

    clean_email = email.strip()
    provider = (os.getenv("EMAIL_VERIFY_PROVIDER") or "").strip().lower()
    hunter_key = os.getenv("HUNTER_API_KEY")
    zb_key = os.getenv("ZEROBOUNCE_API_KEY")

    if not provider:
        if hunter_key:
            provider = "hunter"
        elif zb_key:
            provider = "zerobounce"
        else:
            provider = "mx"

    try:
        if provider == "hunter" and hunter_key:
            return _hunter_verify(clean_email, hunter_key)
        if provider == "zerobounce" and zb_key:
            return _zerobounce_verify(clean_email, zb_key)
    except Exception as exc:
        mx_status, mx_valid = _mx_verify(clean_email)
        return f"{mx_status} (provider fallback: {exc})", mx_valid

    return _mx_verify(clean_email)
