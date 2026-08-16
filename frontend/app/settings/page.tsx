"use client";

import { useEffect, useState } from "react";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";
import type { HubSpotStatus } from "@/lib/types";

export default function SettingsPage() {
  const [status, setStatus] = useState<HubSpotStatus | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setStatus(await api<HubSpotStatus>("/api/hubspot/status"));
  }

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("hubspot") === "connected") setMessage("HubSpot connected.");
    load().catch((err) => setError(err.message));
  }, []);

  async function connect() {
    const data = await api<{ url: string }>("/api/hubspot/authorize");
    window.location.href = data.url;
  }

  async function disconnect() {
    await api("/api/hubspot", { method: "DELETE" });
    setMessage("HubSpot disconnected.");
    await load();
  }

  return (
    <Shell>
      <h1 className="page-title">Settings</h1>
      <p className="page-sub">
        HubSpot is an onboarding add-on. Until connected, deliver CSV. Scraping and verify keys stay on the server.
      </p>
      <div className="card">
        <h3>HubSpot</h3>
        <p>
          {status?.connected
            ? `Connected${status.portal_id ? ` (portal ${status.portal_id})` : ""}. You can push finished campaigns from the campaign page.`
            : status?.configured
              ? "App credentials are on the server. Connect this workspace to your HubSpot portal when you are ready to push contacts."
              : "HubSpot OAuth is not configured on the server yet. Use CSV export for delivery; we connect your portal during onboarding."}
        </p>
        <div className="toolbar">
          <button className="btn" type="button" onClick={connect} disabled={!status?.configured}>
            Connect HubSpot
          </button>
          {status?.connected ? (
            <button className="btn secondary" type="button" onClick={disconnect}>
              Disconnect
            </button>
          ) : null}
        </div>
        {message ? <p className="ok">{message}</p> : null}
        {error ? <p className="error">{error}</p> : null}
      </div>
    </Shell>
  );
}
