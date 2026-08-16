export type User = {
  id: string;
  email: string;
  role: string;
  organization_id: string;
  organization_name: string;
};

export type Targeting = {
  titles: string[];
  country: string;
  countries: string[];
  states: string[];
  cities: string[];
  industries: string[];
  company_sizes: string[];
  revenue_bands: string[];
  seniority: string[];
  functions: string[];
  has_email: boolean;
  has_phone: boolean;
  limit: number;
};

export type IcpTemplate = {
  id: string;
  name: string;
  description: string;
  titles: string[];
  industries: string[];
  seniority: string[];
  functions: string[];
  company_sizes: string[];
  revenue_bands: string[];
  has_email: boolean;
  has_phone: boolean;
  country: string;
  limit: number;
};

export type Campaign = {
  id: string;
  name: string;
  template_id: string;
  targeting: Targeting;
  status: string;
  progress_step: string;
  progress_message: string;
  progress_current: number;
  progress_total: number;
  total_leads: number;
  valid_leads: number;
  skipped_dupes: number;
  error_message: string;
  created_at: string;
};

export type Lead = {
  id: string;
  campaign_id: string;
  full_name: string;
  title: string;
  email: string;
  verification_status: string;
  is_valid_email: boolean;
  phone: string;
  person_linkedin: string;
  company_name: string;
  company_website: string;
  company_linkedin: string;
  industry: string;
  company_size: string;
  revenue: string;
  headquarters: string;
  location: string;
  source: string;
  campaign_name: string;
  icebreaker?: string;
  company_description: string;
  hubspot_id: string;
};

export type Meta = {
  countries: string[];
  seniority: { value: string; label: string }[];
  functions: { value: string; label: string }[];
  company_sizes: { value: string; label: string }[];
  revenue_bands: { value: string; label: string }[];
  industries: string[];
};

export type HubSpotStatus = {
  connected: boolean;
  portal_id: string;
  configured: boolean;
};
