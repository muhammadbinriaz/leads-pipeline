import os
import sys
import argparse
from dotenv import load_dotenv

def setup_terminal_encoding():
    # Force UTF-8 encoding on standard output/error to prevent UnicodeEncodeError in Windows terminals
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

def load_environment():
    load_dotenv()
    if not os.getenv("GROQ_API_KEY") or not os.getenv("APIFY_TOKEN"):
        raise ValueError("❌ Missing GROQ_API_KEY or APIFY_TOKEN in your .env file!")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Automated AI Lead Generation & Enrichment Pipeline")
    parser.add_argument("--country", type=str, default="United States", help="Target country location to filter leads")
    parser.add_argument("--titles", type=str, default="CEO, Founder, VP of Sales", help="Comma-separated target job titles")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of leads to extract and process")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory where lead spreadsheets will be saved")
    parser.add_argument("--skip-verification", action="store_true", help="Skip email syntax and MX verification")
    parser.add_argument("--skip-slack", action="store_true", help="Skip sending Slack completion alerts")
    return parser.parse_args()
