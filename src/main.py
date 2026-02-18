"""
RS&Co. Enterprise — Dynamics 365 / SharePoint Task Sync
Entry point for CLI and Azure Function / Power Automate HTTP trigger use.

Usage:
  python -m src.main                    # full bidirectional sync
  python -m src.main --mode push        # SharePoint → D365 only
  python -m src.main --mode pull        # D365 → SharePoint only
  python -m src.main --mode full --project-id <GUID>
"""

import argparse
import json
import logging
import sys

from dotenv import load_dotenv

load_dotenv()  # loads .env from cwd if present; no-op in Azure Function (env vars set directly)

from src.sync.task_sync import sync_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("rs_enterprise")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Sync SharePoint To-Dos & WBS Tasks with Dynamics 365"
    )
    parser.add_argument(
        "--mode",
        choices=["push", "pull", "full"],
        default="full",
        help="Sync direction (default: full)",
    )
    parser.add_argument(
        "--project-id",
        default="",
        help="Dynamics 365 Project Operations project GUID (overrides D365_PROJECT_ID env var)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (useful for Power Automate HTTP response parsing)",
    )
    args = parser.parse_args(argv)

    try:
        results = sync_all(mode=args.mode, project_id=args.project_id)
    except Exception as exc:
        logger.critical("Sync failed: %s", exc, exc_info=True)
        return 1

    if args.json:
        output = {
            key: {
                "created": r.created,
                "updated": r.updated,
                "skipped": r.skipped,
                "errors": r.errors,
            }
            for key, r in results.items()
        }
        print(json.dumps(output, indent=2))
    else:
        for key, r in results.items():
            print(f"{key.upper():>6}: {r.summary()}")

    total_errors = sum(r.errors for r in results.values())
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
