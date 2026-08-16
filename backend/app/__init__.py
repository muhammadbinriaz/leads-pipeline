from backend.app.database import Base, engine
from backend.app.models import Campaign, HubSpotConnection, Lead, Organization, User  # noqa: F401

Base.metadata.create_all(bind=engine)
