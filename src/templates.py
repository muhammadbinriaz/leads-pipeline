ICP_TEMPLATES = [
    {
        "id": "saas",
        "name": "SaaS / B2B Software",
        "description": "Decision-makers at software companies who buy tools for sales, product, or growth.",
        "titles": ["CEO", "Founder", "CRO", "VP of Sales", "Head of Growth", "VP of Marketing"],
        "industries": ["Computer Software", "Internet", "Information Technology & Services"],
        "seniority": ["c_suite", "vp", "owner"],
        "functions": ["sales", "marketing", "business_development"],
        "company_sizes": ["11-50", "51-200", "201-500"],
        "revenue_bands": ["1m_10m", "10m_50m"],
        "has_email": True,
        "has_phone": False,
        "country": "United States",
        "limit": 10,
    },
    {
        "id": "agencies",
        "name": "Marketing Agencies",
        "description": "Agency owners and new-business leads for partnership or outbound lists.",
        "titles": ["CEO", "Founder", "Managing Director", "Head of New Business", "VP of Business Development"],
        "industries": ["Marketing & Advertising", "Public Relations & Communications", "Media Production"],
        "seniority": ["c_suite", "owner", "partner", "vp"],
        "functions": ["business_development", "marketing", "sales"],
        "company_sizes": ["1-10", "11-50", "51-200"],
        "revenue_bands": ["lt_1m", "1m_10m"],
        "has_email": True,
        "has_phone": False,
        "country": "United States",
        "limit": 10,
    },
    {
        "id": "real_estate",
        "name": "Real Estate",
        "description": "Brokers, investors, and property managers for prospect list building.",
        "titles": ["Broker", "Managing Broker", "Principal", "Owner", "Director of Acquisitions", "Property Manager"],
        "industries": ["Real Estate", "Commercial Real Estate", "Investment Management"],
        "seniority": ["owner", "c_suite", "director", "partner"],
        "functions": ["operations", "finance", "business_development"],
        "company_sizes": ["1-10", "11-50", "51-200"],
        "revenue_bands": ["1m_10m", "10m_50m"],
        "has_email": True,
        "has_phone": True,
        "country": "United States",
        "limit": 10,
    },
    {
        "id": "csuite",
        "name": "C-Suite / Executives",
        "description": "Named executives for high-touch outreach — titles at the top of the house.",
        "titles": ["CEO", "CFO", "COO", "CRO", "CMO", "CTO", "President"],
        "industries": [],
        "seniority": ["c_suite", "owner"],
        "functions": [],
        "company_sizes": ["51-200", "201-500", "501-1000", "1001-5000"],
        "revenue_bands": ["10m_50m", "50m_200m", "200m_1b"],
        "has_email": True,
        "has_phone": False,
        "country": "United States",
        "limit": 10,
    },
    {
        "id": "commercial_services",
        "name": "Commercial Services",
        "description": "Facility, cleaning, and B2B service buyers at companies with physical locations.",
        "titles": ["Facilities Manager", "Office Manager", "Operations Manager", "Director of Operations", "Property Manager"],
        "industries": ["Environmental Services", "Hospitality", "Real Estate", "Construction"],
        "seniority": ["manager", "director", "owner"],
        "functions": ["operations"],
        "company_sizes": ["11-50", "51-200", "201-500"],
        "revenue_bands": ["1m_10m", "10m_50m"],
        "has_email": True,
        "has_phone": True,
        "country": "United States",
        "limit": 10,
    },
    {
        "id": "custom",
        "name": "Custom ICP",
        "description": "Start from a blank targeting profile and set every filter yourself.",
        "titles": ["CEO", "Founder", "VP of Sales"],
        "industries": [],
        "seniority": [],
        "functions": [],
        "company_sizes": [],
        "revenue_bands": [],
        "has_email": True,
        "has_phone": False,
        "country": "United States",
        "limit": 10,
    },
]

SENIORITY_OPTIONS = [
    {"value": "c_suite", "label": "C-Suite"},
    {"value": "vp", "label": "VP"},
    {"value": "director", "label": "Director"},
    {"value": "manager", "label": "Manager"},
    {"value": "senior", "label": "Senior"},
    {"value": "owner", "label": "Owner"},
    {"value": "partner", "label": "Partner"},
    {"value": "entry", "label": "Entry"},
    {"value": "intern", "label": "Intern"},
]

FUNCTION_OPTIONS = [
    {"value": "sales", "label": "Sales"},
    {"value": "marketing", "label": "Marketing"},
    {"value": "business_development", "label": "Business Development"},
    {"value": "engineering", "label": "Engineering"},
    {"value": "finance", "label": "Finance"},
    {"value": "operations", "label": "Operations"},
    {"value": "hr", "label": "HR"},
    {"value": "it", "label": "IT"},
]

COMPANY_SIZE_OPTIONS = [
    {"value": "1-10", "label": "1–10"},
    {"value": "11-50", "label": "11–50"},
    {"value": "51-200", "label": "51–200"},
    {"value": "201-500", "label": "201–500"},
    {"value": "501-1000", "label": "501–1,000"},
    {"value": "1001-5000", "label": "1,001–5,000"},
    {"value": "5001-10000", "label": "5,001–10,000"},
    {"value": "10001+", "label": "10,001+"},
]

REVENUE_OPTIONS = [
    {"value": "lt_1m", "label": "Less than $1M"},
    {"value": "1m_10m", "label": "$1M–$10M"},
    {"value": "10m_50m", "label": "$10M–$50M"},
    {"value": "50m_200m", "label": "$50M–$200M"},
    {"value": "200m_1b", "label": "$200M–$1B"},
    {"value": "gt_1b", "label": "More than $1B"},
]

INDUSTRY_OPTIONS = [
    "Accounting", "Agriculture", "Airlines/Aviation", "Animation", "Apparel & Fashion",
    "Architecture & Planning", "Automotive", "Aviation & Aerospace", "Banking", "Biotechnology",
    "Broadcast Media", "Building Materials", "Capital Markets", "Chemicals", "Civil Engineering",
    "Commercial Real Estate", "Computer & Network Security", "Computer Games", "Computer Hardware",
    "Computer Networking", "Computer Software", "Construction", "Consumer Electronics",
    "Consumer Goods", "Consumer Services", "Defense & Space", "Design", "E-Learning",
    "Education Management", "Electrical/Electronic Manufacturing", "Entertainment",
    "Environmental Services", "Events Services", "Financial Services", "Food & Beverages",
    "Food Production", "Furniture", "Government Administration", "Graphic Design",
    "Health, Wellness & Fitness", "Higher Education", "Hospital & Health Care", "Hospitality",
    "Human Resources", "Industrial Automation", "Information Services",
    "Information Technology & Services", "Insurance", "Internet", "Investment Banking",
    "Investment Management", "Law Practice", "Legal Services", "Leisure, Travel & Tourism",
    "Logistics & Supply Chain", "Luxury Goods & Jewelry", "Machinery", "Management Consulting",
    "Market Research", "Marketing & Advertising", "Mechanical or Industrial Engineering",
    "Media Production", "Medical Devices", "Medical Practice", "Mental Health Care",
    "Mining & Metals", "Non-Profit Organization Management", "Oil & Energy", "Online Media",
    "Outsourcing/Offshoring", "Pharmaceuticals", "Photography", "Professional Training & Coaching",
    "Public Relations & Communications", "Publishing", "Real Estate", "Recreation & Sports",
    "Renewables & Environment", "Research", "Restaurants", "Retail", "Security & Investigations",
    "Semiconductors", "Staffing & Recruiting", "Telecommunications",
    "Transportation/Trucking/Railroad", "Utilities", "Venture Capital & Private Equity",
    "Warehousing", "Wholesale", "Wine & Spirits", "Wireless", "Writing & Editing",
]

INDUSTRY_ALIASES = {
    "saas": "Computer Software",
    "software": "Computer Software",
    "b2b saas": "Computer Software",
    "it": "Information Technology & Services",
    "it services": "Information Technology & Services",
    "tech": "Information Technology & Services",
    "marketing": "Marketing & Advertising",
    "advertising": "Marketing & Advertising",
    "agencies": "Marketing & Advertising",
    "pr": "Public Relations & Communications",
    "facilities": "Environmental Services",
    "facilities services": "Environmental Services",
    "cleaning": "Environmental Services",
    "commercial cleaning": "Environmental Services",
}


def normalize_industries(values: list[str] | None) -> list[str]:
    if not values:
        return []
    allowed = {name.lower(): name for name in INDUSTRY_OPTIONS}
    seen: set[str] = set()
    out: list[str] = []
    for raw in values:
        key = str(raw).strip().lower()
        if not key:
            continue
        mapped = INDUSTRY_ALIASES.get(key) or allowed.get(key)
        if mapped and mapped not in seen:
            seen.add(mapped)
            out.append(mapped)
    return out


def get_template(template_id: str) -> dict | None:
    for item in ICP_TEMPLATES:
        if item["id"] == template_id:
            return item
    return None
