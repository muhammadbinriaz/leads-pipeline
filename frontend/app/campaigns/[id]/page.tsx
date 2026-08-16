"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Shell from "@/components/Shell";
import { api, apiUrl, getToken } from "@/lib/api";
import type { Campaign, HubSpotStatus, Lead } from "@/lib/types";

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [hubspot, setHubspot] = useState<HubSpotStatus | null>(null);
  const [verified, setVerified] = useState(false);
  const [hasPhone, setHasPhone] = useState(false);
  const [hasLinkedin, setHasLinkedin] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadCampaign() {
    const data = await api<Campaign>(`/api/campaigns/${params.id}`);
    setCampaign(data);
    return data;
  }

  async function loadLeads(next = { verified, hasPhone, hasLinkedin }) {
    const query = new URLSearchParams();
    if (next.verified) query.set("verified", "true");
    if (next.hasPhone) query.set("has_phone", "true");
    if (next.hasLinkedin) query.set("has_linkedin", "true");
    const suffix = query.toString() ? `?${query}` : "";
    setLeads(await api<Lead[]>(`/api/campaigns/${params.id}/leads${suffix}`));
  }

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | undefined;
    loadCampaign()
      .then(async (data) => {
        if (data.status === "ready") await loadLeads();
      })
      .catch((err) => setError(err.message));
    api<HubSpotStatus>("/api/hubspot/status").then(setHubspot).catch(() => undefined);

    timer = setInterval(async () => {
      try {
        const data = await loadCampaign();
        if (data.status === "ready" || data.status === "failed") {
          if (data.status === "ready") await loadLeads();
          if (timer) clearInterval(timer);
        }
      } catch {
        /* keep polling until auth fails */
      }
    }, 2000);
    return () => {
      if (timer) clearInterval(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  async function applyFilters() {
    await loadLeads({ verified, hasPhone, hasLinkedin });
  }

  async function downloadCsv() {
    const response = await fetch(apiUrl(`/api/campaigns/${params.id}/export.csv`), {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${campaign?.name || "leads"}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function pushHubspot() {
    setError("");
    setMessage("");
    try {
      const result = await api<{ pushed: number; failed: number; errors: string[] }>(
        `/api/hubspot/campaigns/${params.id}/push`,
        { method: "POST" },
      );
      setMessage(`HubSpot: ${result.pushed} pushed, ${result.failed} failed.`);
      await loadLeads();
    } catch (err) {
      setError(err instanceof Error ? err.message : "HubSpot push failed");
    }
  }

  const percent =
    campaign && campaign.progress_total
      ? Math.min(100, Math.round((campaign.progress_current / campaign.progress_total) * 100))
      : campaign?.status === "ready"
        ? 100
        : 8;

  return (
    <Shell>
      <h1 className="page-title">{campaign?.name || "Campaign"}</h1>
      <p className="page-sub">{campaign?.progress_message || "Loading…"}</p>
      {campaign ? <span className={`badge ${campaign.status}`}>{campaign.status}</span> : null}
      <div className="progress">
        <span style={{ width: `${percent}%` }} />
      </div>
      {campaign?.error_message ? <p className="error">{campaign.error_message}</p> : null}
      <div className="toolbar">
        <button className="btn secondary" type="button" onClick={downloadCsv} disabled={campaign?.status !== "ready"}>
          Download CSV
        </button>
        <button
          className="btn"
          type="button"
          onClick={pushHubspot}
          disabled={campaign?.status !== "ready" || !hubspot?.connected}
        >
          Push to HubSpot
        </button>
        {!hubspot?.connected ? (
          <span className="hint">
            HubSpot not connected yet — download CSV now; connect the portal in Settings during onboarding.
          </span>
        ) : null}
      </div>
      <div className="filters">
        <label>
          <input type="checkbox" checked={verified} onChange={(e) => setVerified(e.target.checked)} /> Verified only
        </label>
        <label>
          <input type="checkbox" checked={hasPhone} onChange={(e) => setHasPhone(e.target.checked)} /> Has phone
        </label>
        <label>
          <input type="checkbox" checked={hasLinkedin} onChange={(e) => setHasLinkedin(e.target.checked)} /> Has LinkedIn
        </label>
        <button className="btn secondary" type="button" onClick={applyFilters}>
          Apply
        </button>
      </div>
      {message ? <p className="ok">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Title</th>
              <th>Email</th>
              <th>Status</th>
              <th>Phone</th>
              <th>Company</th>
              <th>Industry</th>
              <th>Size</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>
                  {lead.full_name}
                  {lead.person_linkedin ? (
                    <>
                      <br />
                      <a href={lead.person_linkedin} target="_blank" rel="noreferrer">
                        LinkedIn
                      </a>
                    </>
                  ) : null}
                </td>
                <td>{lead.title}</td>
                <td>{lead.email}</td>
                <td>{lead.verification_status}</td>
                <td>{lead.phone}</td>
                <td>
                  {lead.company_name}
                  {lead.company_website ? (
                    <>
                      <br />
                      <a href={lead.company_website.startsWith("http") ? lead.company_website : `https://${lead.company_website}`} target="_blank" rel="noreferrer">
                        Website
                      </a>
                    </>
                  ) : null}
                </td>
                <td>{lead.industry}</td>
                <td>{lead.company_size}</td>
                <td>{lead.location || lead.headquarters}</td>
              </tr>
            ))}
            {!leads.length ? (
              <tr>
                <td colSpan={9}>
                  {campaign?.status === "ready" ? "No leads match these filters." : "Leads will appear when the run finishes."}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
