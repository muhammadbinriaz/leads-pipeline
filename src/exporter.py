import os
import re
import csv
import io

CSV_HEADERS = [
    "Full Name", "Email", "Verification Status", "Title",
    "Original Company Name", "Cleaned Company Name", "Industry",
    "AI Icebreaker", "Company Description", "LinkedIn URL"
]

def export_leads_to_csv(processed_leads: list[dict], output_dir: str, country: str, timestamp: str) -> str:
    """
    Saves processed lead details into a formatted CSV spreadsheet file.
    """
    os.makedirs(output_dir, exist_ok=True)
    cleaned_country = re.sub(r'[^a-zA-Z0-9]', '_', country).lower()
    filename = f"campaign_leads_{cleaned_country}_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        for lead in processed_leads:
            row = {k: v for k, v in lead.items() if k in CSV_HEADERS}
            writer.writerow(row)
    
    return filepath


def leads_to_csv_bytes(processed_leads: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_HEADERS)
    writer.writeheader()
    for lead in processed_leads:
        row = {k: v for k, v in lead.items() if k in CSV_HEADERS}
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")

def print_terminal_summary(processed_leads: list[dict]):
    """
    Generates a visual summary grid table in the console using tabulate.
    """
    from tabulate import tabulate

    summary_data = []
    for lead in processed_leads:
        icebreaker = lead["AI Icebreaker"]
        if len(icebreaker) > 50:
            icebreaker = icebreaker[:47] + "..."
        summary_data.append([
            lead["Full Name"],
            lead["Email"],
            lead["Verification Status"],
            lead["Cleaned Company Name"],
            icebreaker
        ])
        
    print("\n" + "=" * 60)
    print("📊 CAMPAIGN RUN SUMMARY")
    print("=" * 60)
    print(tabulate(summary_data, headers=["Name", "Email", "Verification Status", "Cleaned Company", "AI Icebreaker"], tablefmt="grid"))
    
    total_leads = len(processed_leads)
    valid_leads = sum(1 for l in processed_leads if l["Is Valid Email"])
    print(f"\n📈 Results: Processed {total_leads} leads | Verified Deliverable: {valid_leads}/{total_leads}")
    print("=" * 60 + "\n")
