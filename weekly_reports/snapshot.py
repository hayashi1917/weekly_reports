from __future__ import annotations

from collections import defaultdict

from weekly_reports.models import Task, TaskSession, WeekReportBundle

SCHEMA_VERSION = "1.0"


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "estimated_minutes": task.estimated_minutes,
        "status": task.status,
        "day_id": task.day_id,
        "priority": task.priority,
        "reason_tags": list(task.reason_tags),
        "note": task.note,
    }


def _session_to_dict(session: TaskSession) -> dict:
    return {
        "id": session.id,
        "task_id": session.task_id,
        "start_at": session.start_at.isoformat(),
        "end_at": session.end_at.isoformat(),
        "note": session.note,
        "is_completed": session.is_completed,
    }


def build_snapshot(bundle: WeekReportBundle, *, pdf_path: str, json_path: str) -> dict:
    report = bundle.report
    tasks_by_day: dict[str, list[Task]] = defaultdict(list)
    for task in bundle.tasks:
        tasks_by_day[task.day_id].append(task)

    next_week_days = []
    for day in bundle.days:
        next_week_days.append(
            {
                "id": day.id,
                "date": day.date.isoformat(),
                "planned_minutes": day.planned_minutes,
                "scheduled_minutes": day.scheduled_minutes,
                "done_count": day.done_count,
                "total_count": day.total_count,
                "tasks": [_task_to_dict(task) for task in tasks_by_day.get(day.id, [])],
            }
        )

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "week_id": report.week_id,
        "cycle": {
            "start": report.cycle_start.isoformat(),
            "end": report.cycle_end.isoformat(),
        },
        "review_at": report.review_at.isoformat(),
        "goals": {
            "week": list(report.goals_week),
            "month": list(report.goals_month),
            "long": list(report.goals_long),
        },
        "review": {
            "good": list(report.good_points),
            "issues": [
                {
                    "problem": issue.problem,
                    "root_cause": issue.root_cause,
                    "improvement": issue.improvement,
                    "tags": list(issue.tags),
                }
                for issue in report.issues
            ],
        },
        "last_week_tasks": [_task_to_dict(task) for task in bundle.last_week_tasks],
        "next_week_days": next_week_days,
        "task_sessions": [_session_to_dict(session) for session in bundle.task_sessions],
        "exports": {
            "pdf_path": pdf_path,
            "json_path": json_path,
        },
    }
    return snapshot
