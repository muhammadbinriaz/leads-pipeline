# Signal — Zaryab-type client demo script

Use this before a referral sits down. Product pitch: **ICP starter workspace + human QA**, not “replace Zaryab / replace VAs.”

## Login (rotated for demo)

- URL: http://localhost:3001  
- Email: `admin@signal.local`  
- Password: `SignalClient2026!`  

Hard-refresh the browser (Ctrl+Shift+R) so chips UI / contrast fixes load. Keys stay on the server — never type Apify/Groq in the UI.

Change `ADMIN_PASSWORD` in `.env` again before any real client handoff, then restart:

```powershell
docker compose up -d --force-recreate api worker
```

## Say this once, early (accuracy)

> “This is the starter pull for your ICP — titles, industry, size, geo. Final accuracy QA is still a human step. That’s where ongoing list-cleaning work stays.”

Do **not** say “100% accurate” or “no human needed.”

## Pitch line

> “Zaryab-style ICP quality at the targeting layer, software speed for the first draft, human QA for the list your sales team actually dials.”

## Live walkthrough (5–10 leads)

1. Campaigns → **New campaign**
2. Pick **SaaS / B2B Software** (or the niche matching the referral)
3. Set volume to **5–10** (Apify bills per lead returned)
4. Launch → stay on the campaign page until status is **ready**
5. Show filters: verified / has phone / has LinkedIn
6. Download CSV — point at name, title, email, LinkedIn, company, website, size, location
7. Settings → HubSpot: if OAuth is not configured, say:  
   > “We connect your HubSpot portal in onboarding. Today the deliverable is CSV; push is included once your portal is linked.”

## Cost disclosure (say out loud)

Quote software/hosting separately from data spend:

- **Apify:** billed per lead returned (order of ~$1–2 per 1,000 on paid plans; free tier higher / capped)
- **Email verify (Hunter / ZeroBounce):** optional later; without it, Signal uses MX checks only
- Software fee does **not** include unlimited scrapes

Example framing: “Workspace fee + pass-through data cost per 100/1,000 leads.”

## Who this closes

**Yes:** SaaS / agency / recruiter sales lead who wants self-serve volume and accepts starter list + QA.  
**Not yet:** Boutique “hand-research every LinkedIn profile, zero bad emails” only.

## After the demo (your wedge)

Their next hire can shift from “find me leads from scratch” to “clean / verify / enrich our exported sheets” — that is ongoing paid work for you.
