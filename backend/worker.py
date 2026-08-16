import os
import sys
from pathlib import Path

from redis import Redis
from rq import Worker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import get_settings  # noqa: E402
from backend.app.database import Base, engine  # noqa: E402
from backend.app.models import Campaign, HubSpotConnection, Lead, Organization, User  # noqa: F401,E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    os.environ.setdefault("APIFY_TOKEN", settings.apify_token)
    os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)
    os.environ.setdefault("HUNTER_API_KEY", settings.hunter_api_key)
    os.environ.setdefault("ZEROBOUNCE_API_KEY", settings.zerobounce_api_key)
    os.environ.setdefault("EMAIL_VERIFY_PROVIDER", settings.email_verify_provider)
    connection = Redis.from_url(settings.redis_url)
    Worker(["campaigns"], connection=connection).work(with_scheduler=True)


if __name__ == "__main__":
    main()
