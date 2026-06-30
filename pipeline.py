import sys
from src.config import setup_terminal_encoding, load_environment, parse_arguments
from src.pipeline_runner import PipelineConfig, run_pipeline
from src.exporter import print_terminal_summary


def main():
    setup_terminal_encoding()

    try:
        load_environment()
    except ValueError as e:
        print(e)
        sys.exit(1)

    args = parse_arguments()
    titles_list = [t.strip() for t in args.titles.split(",") if t.strip()]

    print("=" * 60)
    print("🚀 AUTOMATED AI LEAD GENERATION & ENRICHMENT PIPELINE (MODULAR)")
    print("=" * 60)
    print(f"📍 Target Country : {args.country}")
    print(f"🎯 Target Roles   : {', '.join(titles_list)}")
    print(f"📦 Extract Limit  : {args.limit} leads")
    print(f"📂 Output Folder  : {args.output_dir}")
    print(f"🛡️ Email Verify   : {'DISABLED' if args.skip_verification else 'ENABLED (Syntax + DNS MX Check)'}")
    print(f"🔔 Slack Alerts   : {'DISABLED' if args.skip_slack else 'ENABLED'}")
    print("-" * 60)

    def on_progress(step, message, current=0, total=0):
        if step in {"scrape", "export", "slack", "done"}:
            print(message)
        elif step in {"process", "verify", "enrich"}:
            print(f"   {message}")

    config = PipelineConfig(
        country=args.country,
        titles=titles_list,
        limit=args.limit,
        output_dir=args.output_dir,
        skip_verification=args.skip_verification,
        skip_slack=args.skip_slack,
    )

    try:
        result = run_pipeline(config, on_progress=on_progress)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

    if result.csv_path:
        print(f"\n💾 Spreadsheet created successfully: {result.csv_path}")
    if result.slack_sent:
        print("✅ Slack alert sent.")
    for warning in result.warnings:
        print(f"⚠️ {warning}")

    print_terminal_summary(result.processed_leads)


if __name__ == "__main__":
    main()
