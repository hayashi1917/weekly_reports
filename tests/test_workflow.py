from datetime import datetime, timedelta

from weekly_reports.workflow import init_week_report
from weekly_reports.metrics import update_day_metrics
from weekly_reports.models import WeekReportBundle, build_bundle
from weekly_reports.snapshot import build_snapshot


def test_init_week_report_creates_week_and_days() -> None:
    review_at = datetime(2026, 1, 16, 18, 0)
    bundle = init_week_report(review_at, None)

    assert bundle.report.cycle_start == review_at.date() + timedelta(days=1)
    assert bundle.report.cycle_end == bundle.report.cycle_start + timedelta(days=6)
    assert len(bundle.days) == 7
    assert bundle.days[0].date == bundle.report.cycle_start


def test_metrics_and_snapshot_flow() -> None:
    payload = {
        "week_report": {
            "id": "wr_1",
            "week_id": "2026-W03",
            "cycle_start": "2026-01-17",
            "cycle_end": "2026-01-23",
            "review_at": "2026-01-16T18:00:00",
            "status": "draft",
            "goals_week": ["focus"],
            "goals_month": [],
            "goals_long": [],
            "good_points": ["steady"],
            "issues": [],
            "created_at": "2026-01-16T18:05:00",
            "updated_at": "2026-01-16T18:05:00",
        },
        "days": [
            {"id": "d1", "week_report_id": "wr_1", "date": "2026-01-17"},
        ],
        "tasks": [
            {
                "id": "t1",
                "week_report_id": "wr_1",
                "day_id": "d1",
                "title": "Task",
                "estimated_minutes": 90,
                "priority": 1,
                "status": "done",
                "reason_tags": [],
                "note": None,
                "created_at": "2026-01-16T18:10:00",
                "updated_at": "2026-01-16T18:10:00",
            }
        ],
        "task_sessions": [
            {
                "id": "s1",
                "task_id": "t1",
                "start_at": "2026-01-17T09:00:00",
                "end_at": "2026-01-17T10:30:00",
                "note": "session",
                "is_completed": True,
            }
        ],
        "last_week_tasks": [],
    }
    bundle = build_bundle(payload)
    updated_days = update_day_metrics(bundle.days, bundle.tasks, bundle.task_sessions)
    updated_bundle = WeekReportBundle(
        report=bundle.report,
        days=updated_days,
        tasks=bundle.tasks,
        task_sessions=bundle.task_sessions,
        last_week_tasks=bundle.last_week_tasks,
    )

    assert updated_days[0].planned_minutes == 90
    assert updated_days[0].scheduled_minutes == 90
    assert updated_days[0].done_count == 1
    assert updated_days[0].total_count == 1

    snapshot = build_snapshot(updated_bundle, pdf_path="out.pdf", json_path="out.json")
    assert snapshot["schema_version"] == "1.0"
    assert snapshot["next_week_days"][0]["planned_minutes"] == 90
