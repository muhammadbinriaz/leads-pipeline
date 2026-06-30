from email_validator import validate_email, EmailNotValidError

def verify_lead_email(email: str) -> tuple[str, bool]:
    """
    Verifies an email address using syntax rules and DNS MX lookup.
    Returns (status_description, is_valid).
    """
    if not email or email.strip() == "" or email.lower() == "no email found":
        return "Missing Email", False
    
    clean_email = email.strip()
    try:
        # validate_email performs syntax validation and checks for valid MX records
        validate_email(clean_email, check_deliverability=True, timeout=5)
        return "Verified", True
    except EmailNotValidError as e:
        return str(e), False
