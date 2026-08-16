import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app.auth import hash_password
from backend.app.config import get_settings
from backend.app.database import Base, SessionLocal, engine
from backend.app.models import Organization, User
from backend.app.routers import auth, campaigns, hubspot, meta

settings = get_settings()
app = FastAPI(title="Signal Lead Workspace", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(meta.router)
app.include_router(campaigns.router)
app.include_router(hubspot.router)


def seed() -> None:
    db: Session = SessionLocal()
    try:
        org = db.query(Organization).first()
        if not org:
            org = Organization(name=settings.org_name)
            db.add(org)
            db.flush()
        else:
            org.name = settings.org_name

        admin = db.query(User).filter(User.email == settings.admin_email.lower()).first()
        password_hash = hash_password(settings.admin_password)
        if not admin:
            admin = User(
                organization_id=org.id,
                email=settings.admin_email.lower(),
                password_hash=password_hash,
                role="admin",
            )
            db.add(admin)
        else:
            # Keep demo/prod login in sync with ADMIN_PASSWORD in env.
            admin.password_hash = password_hash
            admin.organization_id = org.id
            admin.role = "admin"
        db.commit()
    finally:
        db.close()


def apply_runtime_env() -> None:
    if settings.apify_token:
        os.environ["APIFY_TOKEN"] = settings.apify_token
    if settings.groq_api_key:
        os.environ["GROQ_API_KEY"] = settings.groq_api_key
    if settings.hunter_api_key:
        os.environ["HUNTER_API_KEY"] = settings.hunter_api_key
    if settings.zerobounce_api_key:
        os.environ["ZEROBOUNCE_API_KEY"] = settings.zerobounce_api_key
    if settings.email_verify_provider:
        os.environ["EMAIL_VERIFY_PROVIDER"] = settings.email_verify_provider


@app.on_event("startup")
def on_startup() -> None:
    apply_runtime_env()
    Base.metadata.create_all(bind=engine)
    seed()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "signal-api"}
