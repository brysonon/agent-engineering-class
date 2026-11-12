"""Discover, download, and configure general conference talks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from conference_source import (
    conference_date_label,
    conference_slug,
    discover_conference_urls,
    download_conference,
    write_conference_config,
)
from settings import PROJECT_DIR


DEFAULT_OUTPUT_ROOT = PROJECT_DIR / "conference_talks"
DEFAULT_CONFIG = PROJECT_DIR / "conferences.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-year", type=int, default=1971)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--write-config-only", action="store_true")
    args = parser.parse_args()

    if args.end_year is not None and args.start_year > args.end_year:
        parser.error("--start-year must be less than or equal to --end-year")
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.retries < 1:
        parser.error("--retries must be at least 1")

    conference_urls = discover_conference_urls(start_year=args.start_year, end_year=args.end_year)
    if not conference_urls:
        raise ValueError("No conferences were discovered for the requested range")

    print(f"Discovered {len(conference_urls)} conferences")
    args.output_root.mkdir(parents=True, exist_ok=True)

    if args.write_config_only:
        write_conference_config(conference_urls, args.output_root, args.config)
        print(f"Wrote config for {len(conference_urls)} conferences to {args.config}")
        return 0

    successful_urls = []
    total_talks = 0
    failures = []

    for index, conference_url in enumerate(conference_urls, start=1):
        label = conference_date_label(conference_url)
        folder = args.output_root / conference_slug(conference_url)
        print(f"[{index}/{len(conference_urls)}] {label}")
        try:
            written, expected = download_conference(
                conference_url,
                folder,
                workers=args.workers,
                retries=args.retries,
                skip_existing=args.skip_existing,
            )
        except Exception as exc:  # noqa: BLE001
            failures.append((conference_url, str(exc)))
            print(f"  failed: {exc}")
            continue

        print(f"  wrote {written}/{expected} talks to {folder.name}")
        if written == expected:
            successful_urls.append(conference_url)
            total_talks += written
        else:
            failures.append((conference_url, f"wrote {written}/{expected}"))

    if failures:
        print("\nSome conferences failed:")
        for conference_url, reason in failures:
            print(f"- {conference_url}: {reason}")
        print("\nLeaving conferences.json unchanged so the index only uses complete imports.")
        return 1

    write_conference_config(successful_urls, args.output_root, args.config)
    print(f"Imported {len(successful_urls)} conferences and {total_talks} talks")
    print(f"Wrote config to {args.config}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
