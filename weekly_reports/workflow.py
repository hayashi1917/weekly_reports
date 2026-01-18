from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from weekly_reports.models import Day, WeekReport, WeekReportBundle


def week_id_from_date(start_date) -> str:
    iso_year, iso_week, _ = start_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def init_week_report(review_at: datetime, prev_bundle: WeekReportBundle | None) -> WeekReportBundle:
    # レビューは金曜18:00想定で、次のサイクル開始は土曜日。
    cycle_start = review_at.date() + timedelta(days=1)
    cycle_end = cycle_start + timedelta(days=6)
    week_id = week_id_from_date(cycle_start)
    report_id = f"wr_{uuid4().hex[:8]}"
    now = datetime.now()
    report = WeekReport(
        id=report_id,
        week_id=week_id,
        cycle_start=cycle_start,
        cycle_end=cycle_end,
        review_at=review_at,
        status="draft",
        prev_week_report_id=prev_bundle.report.id if prev_bundle else None,
        goals_week=prev_bundle.report.goals_week if prev_bundle else (),
        goals_month=prev_bundle.report.goals_month if prev_bundle else (),
        goals_long=prev_bundle.report.goals_long if prev_bundle else (),
        good_points=(),
        issues=(),
        created_at=now,
        updated_at=now,
    )
    days = []
    for offset in range(7):
        day_date = cycle_start + timedelta(days=offset)
        day_id = f"{week_id}-{day_date.isoformat()}"
        days.append(
            Day(
                id=day_id,
                week_report_id=report_id,
                date=day_date,
                available_minutes=None,
                planned_minutes=0,
                scheduled_minutes=0,
                done_count=0,
                total_count=0,
            )
        )
    return WeekReportBundle(report=report, days=tuple(days))
