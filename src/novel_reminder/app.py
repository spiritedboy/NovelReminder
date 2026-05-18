from __future__ import annotations

import argparse
import json
import logging
import time

from .config import load_settings
from .service import NovelReminderService


def main() -> int:
    parser = argparse.ArgumentParser(description="Novel update reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run-once")
    subparsers.add_parser("run-loop")
    subparsers.add_parser("show-state")
    args = parser.parse_args()

    settings = load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    service = NovelReminderService(settings)
    if args.command == "run-once":
        service.run_once()
        return 0

    if args.command == "show-state":
        print(
            json.dumps(
                service.list_states(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    while True:
        service.run_once()
        time.sleep(settings.interval_seconds)
