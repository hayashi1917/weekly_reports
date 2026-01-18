from __future__ import annotations

import argparse
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from weekly_reports.metrics import update_day_metrics
from weekly_reports.models import (
    WeekReportBundle,
    build_bundle,
    bundle_to_dict,
)
from weekly_reports.pdf import generate_pdf
from weekly_reports.snapshot import build_snapshot
from weekly_reports.workflow import init_week_report


def _parse_datetime(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


def load_bundle(path: Path) -> WeekReportBundle:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return build_bundle(payload)


def save_bundle(bundle: WeekReportBundle, output: Path) -> None:
    output.write_text(
        json.dumps(bundle_to_dict(bundle), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def command_init(args: argparse.Namespace) -> None:
    prev_bundle = load_bundle(args.prev) if args.prev else None
    review_at = _parse_datetime(args.review_at)
    bundle = init_week_report(review_at, prev_bundle)
    save_bundle(bundle, args.output)
    print(f"Initialized week report: {args.output}")


def command_finalize(args: argparse.Namespace) -> None:
    bundle = load_bundle(args.input)
    updated_days = update_day_metrics(bundle.days, bundle.tasks, bundle.task_sessions)
    report = replace(bundle.report, status="final", updated_at=datetime.now())
    updated_bundle = WeekReportBundle(
        report=report,
        days=updated_days,
        tasks=bundle.tasks,
        task_sessions=bundle.task_sessions,
        last_week_tasks=bundle.last_week_tasks,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / f"{report.week_id}_weekly_report.pdf"
    json_path = output_dir / f"{report.week_id}_snapshot.json"

    generate_pdf(updated_bundle, str(pdf_path))
    snapshot = build_snapshot(updated_bundle, pdf_path=str(pdf_path), json_path=str(json_path))
    json_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    save_bundle(updated_bundle, args.bundle_output)
    print(f"Generated snapshot: {json_path}")
    print(f"Generated PDF: {pdf_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Weekly report manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-week", help="Create a new weekly report")
    init_parser.add_argument("--review-at", required=True, help="Review datetime (ISO format)")
    init_parser.add_argument("--prev", type=Path, help="Previous week report JSON")
    init_parser.add_argument("--output", type=Path, default=Path("week_report.json"))
    init_parser.set_defaults(func=command_init)

    finalize_parser = subparsers.add_parser("finalize", help="Finalize a weekly report")
    finalize_parser.add_argument("input", type=Path, help="Week report JSON")
    finalize_parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    finalize_parser.add_argument(
        "--bundle-output", type=Path, default=Path("week_report_final.json")
    )
    finalize_parser.set_defaults(func=command_finalize)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
