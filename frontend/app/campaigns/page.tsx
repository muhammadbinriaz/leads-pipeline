"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";
import type { Campaign } from "@/lib/types";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Campaign[]>("/api/campaigns")
      .then(setCampaigns)
      .catch((err) => setError(err.message));
  }, []);

  return (
    <Shell>
      <h1 className="page-title">Campaigns</h1>
      <p className="page-sub">
        Pull ICP starter lists in minutes, download CSV, then run a human QA pass before outreach.
        HubSpot push is available after portal connect in Settings.
      </p>
      {error ? <p className="error">{error}</p> : null}
      <div className="toolbar">
        <Link className="btn" href="/campaigns/new">
          New campaign
        </Link>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Leads</th>
              <th>Verified</th>
              <th>Dupes skipped</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {campaigns.map((campaign) => (
              <tr key={campaign.id}>
                <td>{campaign.name}</td>
                <td>
                  <span className={`badge ${campaign.status}`}>{campaign.status}</span>
                </td>
                <td>{campaign.total_leads}</td>
                <td>{campaign.valid_leads}</td>
                <td>{campaign.skipped_dupes}</td>
                <td>
                  <Link href={`/campaigns/${campaign.id}`}>Open</Link>
                </td>
              </tr>
            ))}
            {!campaigns.length ? (
              <tr>
                <td colSpan={6}>No campaigns yet. Create one from an ICP template.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}
