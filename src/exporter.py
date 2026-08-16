import csv
import io
import os
import re

CSV_HEADERS = [
    "Full Name",
    "Title",
    "Email",
    "Verification Status",
    "Phone",
    "Person LinkedIn",
    "Company Name",
    "Company Website",
    "Company LinkedIn",
    "Industry",
    "Company Size",
    "Revenue",
    "Headquarters",
    "Location",
    "Source",
    "Campaign Name",
    "Company Description",
]


def _row(lead: dict) -> dict:
    return {key: lead.get(key, "") or "" for key in CSV_HEADERS}


def export_leads_to_csv(processed_leads: list[dict], output_dir: str, country: str, timestamp: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    cleaned_country = re.sub(r"[^a-zA-Z0-9]", "_", country or "campaign").lower()
    filename = f"campaign_leads_{cleaned_country}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, mode="w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for lead in processed_leads:
            writer.writerow(_row(lead))
    return filepath


def leads_to_csv_bytes(processed_leads: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS)
    writer.writeheader()
    for lead in processed_leads:
        writer.writerow(_row(lead))
    return buffer.getvalue().encode("utf-8")


def print_terminal_summary(processed_leads: list[dict]):
    from tabulate import tabulate

    summary_data = []
    for lead in processed_leads:
        summary_data.append([
            lead.get("Full Name", ""),
            lead.get("Email", ""),
            lead.get("Verification Status", ""),
            lead.get("Company Name") or lead.get("Cleaned Company Name", ""),
            lead.get("Industry", ""),
        ])

    print("\n" + "=" * 60)
    print("CAMPAIGN RUN SUMMARY")
    print("=" * 60)
    print(tabulate(
        summary_data,
        headers=["Name", "Email", "Verification Status", "Company", "Industry"],
        tablefmt="grid",
    ))

    total_leads = len(processed_leads)
    valid_leads = sum(1 for item in processed_leads if item.get("Is Valid Email"))
    print(f"\nResults: Processed {total_leads} leads | Verified deliverable: {valid_leads}/{total_leads}")
    print("=" * 60 + "\n")
