"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Shell from "@/components/Shell";
import { api } from "@/lib/api";
import type { Campaign, IcpTemplate, Meta, Targeting } from "@/lib/types";

const emptyTargeting: Targeting = {
  titles: [],
  country: "United States",
  countries: [],
  states: [],
  cities: [],
  industries: [],
  company_sizes: [],
  revenue_bands: [],
  seniority: [],
  functions: [],
  has_email: true,
  has_phone: false,
  limit: 10,
};

function csv(values: string[]) {
  return values.join(", ");
}

function parseCsv(value: string) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function toggleValue(values: string[], value: string) {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value];
}

type Option = { value: string; label: string };

function ChipGroup({
  options,
  values,
  onChange,
  scrollable = false,
}: {
  options: Option[];
  values: string[];
  onChange: (next: string[]) => void;
  scrollable?: boolean;
}) {
  return (
    <div className={scrollable ? "chip-scroll chip-group" : "chip-group"}>
      {options.map((option) => {
        const active = values.includes(option.value);
        return (
          <button
            key={option.value}
            type="button"
            className={`chip ${active ? "active" : ""}`}
            onClick={() => onChange(toggleValue(values, option.value))}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export default function NewCampaignPage() {
  const router = useRouter();
  const [templates, setTemplates] = useState<IcpTemplate[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [selected, setSelected] = useState("saas");
  const [name, setName] = useState("SaaS outreach list");
  const [targeting, setTargeting] = useState<Targeting>(emptyTargeting);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Promise.all([api<IcpTemplate[]>("/api/templates"), api<Meta>("/api/meta")])
      .then(([tpl, metaData]) => {
        setTemplates(tpl);
        setMeta(metaData);
        const first = tpl.find((item) => item.id === "saas") || tpl[0];
        if (first) applyTemplate(first);
      })
      .catch((err) => setError(err.message));
  }, []);

  function applyTemplate(template: IcpTemplate) {
    setSelected(template.id);
    setName(`${template.name} list`);
    setTargeting({
      titles: template.titles,
      country: template.country,
      countries: template.country ? [template.country] : [],
      states: [],
      cities: [],
      industries: template.industries,
      company_sizes: template.company_sizes,
      revenue_bands: template.revenue_bands,
      seniority: template.seniority,
      functions: template.functions,
      has_email: template.has_email,
      has_phone: template.has_phone,
      limit: Math.min(template.limit || 10, 25),
    });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const campaign = await api<Campaign>("/api/campaigns", {
        method: "POST",
        body: JSON.stringify({ name, template_id: selected, targeting }),
      });
      router.push(`/campaigns/${campaign.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create campaign");
    } finally {
      setLoading(false);
    }
  }

  const industryOptions = (meta?.industries || []).map((industry) => ({ value: industry, label: industry }));

  return (
    <Shell>
      <h1 className="page-title">New campaign</h1>
      <p className="page-sub">
        Pick an ICP and launch a first-draft list. Treat exports as a starter pull — final accuracy QA stays a human step.
      </p>
      <div className="grid cards">
        {templates.map((template) => (
          <button
            key={template.id}
            type="button"
            className={`card ${selected === template.id ? "selected" : ""}`}
            onClick={() => applyTemplate(template)}
            style={{ textAlign: "left", cursor: "pointer" }}
          >
            <h3>{template.name}</h3>
            <p>{template.description}</p>
          </button>
        ))}
      </div>
      <form onSubmit={onSubmit} style={{ marginTop: "1.5rem" }}>
        <div className="field">
          <label>Campaign name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="row">
          <div className="field">
            <label>Country</label>
            <select
              value={targeting.country}
              onChange={(e) => setTargeting({ ...targeting, country: e.target.value, countries: [e.target.value] })}
            >
              {(meta?.countries || ["United States"]).map((country) => (
                <option key={country} value={country}>
                  {country}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Lead volume</label>
            <input
              type="number"
              min={1}
              max={5000}
              value={targeting.limit}
              onChange={(e) => setTargeting({ ...targeting, limit: Number(e.target.value) })}
            />
            <p className="hint">Start with 5–10 for a test run. Apify bills per lead returned.</p>
          </div>
        </div>
        <div className="field">
          <label>Job titles (comma-separated)</label>
          <textarea
            rows={2}
            value={csv(targeting.titles)}
            onChange={(e) => setTargeting({ ...targeting, titles: parseCsv(e.target.value) })}
          />
        </div>
        <div className="row">
          <div className="field">
            <label>States</label>
            <input
              value={csv(targeting.states)}
              onChange={(e) => setTargeting({ ...targeting, states: parseCsv(e.target.value) })}
              placeholder="California, New York"
            />
          </div>
          <div className="field">
            <label>Cities</label>
            <input
              value={csv(targeting.cities)}
              onChange={(e) => setTargeting({ ...targeting, cities: parseCsv(e.target.value) })}
              placeholder="San Francisco, Austin"
            />
          </div>
        </div>
        <div className="field">
          <span className="field-label">Industries</span>
          <ChipGroup
            options={industryOptions}
            values={targeting.industries}
            onChange={(industries) => setTargeting({ ...targeting, industries })}
            scrollable
          />
        </div>
        <div className="field">
          <span className="field-label">Seniority</span>
          <ChipGroup
            options={meta?.seniority || []}
            values={targeting.seniority}
            onChange={(seniority) => setTargeting({ ...targeting, seniority })}
          />
        </div>
        <div className="field">
          <span className="field-label">Function</span>
          <ChipGroup
            options={meta?.functions || []}
            values={targeting.functions}
            onChange={(functions) => setTargeting({ ...targeting, functions })}
          />
        </div>
        <div className="field">
          <span className="field-label">Company size</span>
          <ChipGroup
            options={meta?.company_sizes || []}
            values={targeting.company_sizes}
            onChange={(company_sizes) => setTargeting({ ...targeting, company_sizes })}
          />
        </div>
        <div className="field">
          <span className="field-label">Revenue</span>
          <ChipGroup
            options={meta?.revenue_bands || []}
            values={targeting.revenue_bands}
            onChange={(revenue_bands) => setTargeting({ ...targeting, revenue_bands })}
          />
        </div>
        <div className="checks">
          <label>
            <input
              type="checkbox"
              checked={targeting.has_email}
              onChange={(e) => setTargeting({ ...targeting, has_email: e.target.checked })}
            />
            Require email
          </label>
          <label>
            <input
              type="checkbox"
              checked={targeting.has_phone}
              onChange={(e) => setTargeting({ ...targeting, has_phone: e.target.checked })}
            />
            Require phone
          </label>
        </div>
        {error ? <p className="error">{error}</p> : null}
        <div className="toolbar">
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Launching…" : "Launch campaign"}
          </button>
        </div>
      </form>
    </Shell>
  );
}
