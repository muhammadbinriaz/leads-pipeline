# Signal — Client Lead Workspace

Private ICP starter workspace for a sales team: log in, pick an ICP, pull a first-draft prospect list, download CSV, optionally push HubSpot. Final accuracy QA stays a human step — this is **not** a replacement for boutique research VAs.

Pitch line: *Zaryab-style ICP quality at the targeting layer, software speed for the first draft, human QA for the list your sales team actually dials.*

Full referral demo script: [CLIENT_DEMO.md](CLIENT_DEMO.md)

## Local demo (Docker)

You do not need Postgres or pgAdmin installed. Docker runs Postgres, Redis, the API, the worker, and the web app. Postgres and Redis stay on the Docker network (not published to your laptop), so they will not fight with other software on ports 5432/6379.

1. Copy env and add keys:

```powershell
copy .env.example .env
```

Fill at least `APIFY_TOKEN`. Optional: `HUNTER_API_KEY` or `ZEROBOUNCE_API_KEY`, HubSpot OAuth app values.

2. Start everything:

```powershell
docker compose up --build
```

3. Open **http://localhost:3001** (hard-refresh: Ctrl+Shift+R)

   - Email: `admin@signal.local` (or `ADMIN_EMAIL` from `.env`)
   - Password: value of `ADMIN_PASSWORD` in `.env` (default in example: `SignalClient2026!`)

4. API health: http://localhost:8000/api/health

### Client demo checklist

See [CLIENT_DEMO.md](CLIENT_DEMO.md). Short version:

- [ ] Confirm `ADMIN_PASSWORD` is not the old `changeme`
- [ ] Hard-refresh UI; sign in
- [ ] New campaign → ICP template → volume **5–10**
- [ ] Say accuracy line early (starter pull + human QA)
- [ ] Download CSV; quote Apify cost separately
- [ ] HubSpot: only promise push if OAuth is configured; otherwise “CSV now, portal in onboarding”

## Deploy on Render

`render.yaml` defines:

- `signal-api` (FastAPI)
- `signal-worker` (RQ worker)
- `signal-web` (Next.js)
- `signal-redis`
- `signal-db` (Postgres)

Blueprint from the repo, then set:

| Variable | Example |
|---|---|
| `APP_URL` | `https://signal-web.onrender.com` |
| `API_URL` | `https://signal-api.onrender.com` |
| `CORS_ORIGINS` | `https://signal-web.onrender.com` |
| `NEXT_PUBLIC_API_URL` | `https://signal-api.onrender.com` (web service **build** arg) |
| `HUBSPOT_REDIRECT_URI` | `https://signal-api.onrender.com/api/hubspot/callback` |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | client login |
| `APIFY_TOKEN` | required |
| `HUNTER_API_KEY` or `ZEROBOUNCE_API_KEY` | real email verify |
| `HUBSPOT_CLIENT_ID` / `HUBSPOT_CLIENT_SECRET` | CRM push (onboarding add-on) |

Quote API spend to the client (Apify + verify) per 100/1,000 leads. Do not eat it silently.

## What v1 does

- Login (JWT). Keys live on the server, not in the browser.
- ICP templates: SaaS, agencies, real estate, C-suite, commercial services, custom.
- Targeting: country/state/city, titles, industry, seniority, function, company size, revenue, has email/phone.
- Background runs with progress and campaign history.
- CRM-ready fields + CSV export (no AI icebreakers).
- Hunter or ZeroBounce when configured; otherwise MX fallback.
- Org-level dedupe on email and LinkedIn URL.
- HubSpot OAuth + contact upsert when configured in onboarding.

## Dev without rebuilding the frontend image

```powershell
docker compose up postgres redis api worker
cd frontend
npm install
npm run dev
```

API: http://localhost:8000 — Web: http://localhost:3000 (or http://localhost:3001 if you use the frontend container)

CLI debug (still works): `python pipeline.py --country "United States" --limit 5`

## Out of scope for v1

LinkedIn Sales Navigator scraping, Clay, extra paid data vendors, Salesforce, Google Maps, Stripe billing, “100% accuracy with no human QA.”
