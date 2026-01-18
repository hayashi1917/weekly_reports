from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable


@dataclass(frozen=True)
class Issue:
    problem: str
    root_cause: str
    improvement: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class WeekReport:
    id: str
    week_id: str
    cycle_start: date
    cycle_end: date
    review_at: datetime
    status: str
    prev_week_report_id: str | None = None
    goals_week: tuple[str, ...] = ()
    goals_month: tuple[str, ...] = ()
    goals_long: tuple[str, ...] = ()
    good_points: tuple[str, ...] = ()
    issues: tuple[Issue, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Day:
    id: str
    week_report_id: str
    date: date
    available_minutes: int | None = None
    planned_minutes: int | None = None
    scheduled_minutes: int | None = None
    done_count: int | None = None
    total_count: int | None = None


@dataclass(frozen=True)
class Task:
    id: str
    week_report_id: str
    day_id: str
    title: str
    estimated_minutes: int
    priority: int | None = None
    status: str = "todo"
    reason_tags: tuple[str, ...] = ()
    note: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class TaskSession:
    id: str
    task_id: str
    start_at: datetime
    end_at: datetime
    note: str | None = None
    is_completed: bool | None = None


@dataclass(frozen=True)
class Snapshot:
    id: str
    week_report_id: str
    schema_version: str
    json_path: str
    pdf_path: str
    created_at: datetime


@dataclass(frozen=True)
class WeekReportBundle:
    report: WeekReport
    days: tuple[Day, ...] = ()
    tasks: tuple[Task, ...] = ()
    task_sessions: tuple[TaskSession, ...] = ()
    last_week_tasks: tuple[Task, ...] = ()


STATUS_VALUES = {"draft", "final"}
TASK_STATUS_VALUES = {"todo", "done", "carried_over", "dropped"}


def _require_text(value: str, label: str) -> str:
    if not value.strip():
        raise ValueError(f"{label} is required.")
    return value


def validate_report(bundle: WeekReportBundle) -> None:
    report = bundle.report
    if report.status not in STATUS_VALUES:
        raise ValueError("Invalid status for WeekReport.")
    if report.cycle_end < report.cycle_start:
        raise ValueError("cycle_end must be on or after cycle_start.")
    _require_text(report.week_id, "week_id")
    for goal_group in (report.goals_week, report.goals_month, report.goals_long):
        for goal in goal_group:
            _require_text(goal, "goal")
    for issue in report.issues:
        _require_text(issue.problem, "issue.problem")
        _require_text(issue.root_cause, "issue.root_cause")
        _require_text(issue.improvement, "issue.improvement")
    day_ids = {day.id for day in bundle.days}
    for task in bundle.tasks:
        _require_text(task.title, "task.title")
        if task.status not in TASK_STATUS_VALUES:
            raise ValueError(f"Invalid task status: {task.status}")
        if task.estimated_minutes <= 0:
            raise ValueError(f"Task estimated_minutes must be positive: {task.title}")
        if task.day_id and task.day_id not in day_ids:
            raise ValueError(f"Task day_id not found: {task.day_id}")
    for task in bundle.last_week_tasks:
        _require_text(task.title, "task.title")
        if task.status not in TASK_STATUS_VALUES:
            raise ValueError(f"Invalid task status: {task.status}")
        if task.estimated_minutes <= 0:
            raise ValueError(f"Task estimated_minutes must be positive: {task.title}")
    task_ids = {task.id for task in bundle.tasks}
    for session in bundle.task_sessions:
        if session.task_id not in task_ids:
            raise ValueError(f"TaskSession task_id not found: {session.task_id}")
        if session.end_at <= session.start_at:
            raise ValueError("TaskSession end_at must be after start_at.")


def build_issue(raw: dict) -> Issue:
    return Issue(
        problem=str(raw.get("problem", "")),
        root_cause=str(raw.get("root_cause", "")),
        improvement=str(raw.get("improvement", "")),
        tags=tuple(raw.get("tags", []) or ()),
    )


def build_tasks(raw_tasks: Iterable[dict]) -> tuple[Task, ...]:
    tasks: list[Task] = []
    for raw in raw_tasks:
        tasks.append(
            Task(
                id=str(raw.get("id", "")),
                week_report_id=str(raw.get("week_report_id", "")),
                day_id=str(raw.get("day_id", "")),
                title=str(raw.get("title", "")),
                estimated_minutes=int(raw.get("estimated_minutes", 0)),
                priority=raw.get("priority"),
                status=str(raw.get("status", "todo")),
                reason_tags=tuple(raw.get("reason_tags", []) or ()),
                note=raw.get("note"),
                created_at=_parse_datetime(raw.get("created_at"), required=False),
                updated_at=_parse_datetime(raw.get("updated_at"), required=False),
            )
        )
    return tuple(tasks)


def build_task_sessions(raw_sessions: Iterable[dict]) -> tuple[TaskSession, ...]:
    sessions: list[TaskSession] = []
    for raw in raw_sessions:
        sessions.append(
            TaskSession(
                id=str(raw.get("id", "")),
                task_id=str(raw.get("task_id", "")),
                start_at=_parse_datetime(raw.get("start_at"), required=True),
                end_at=_parse_datetime(raw.get("end_at"), required=True),
                note=raw.get("note"),
                is_completed=raw.get("is_completed"),
            )
        )
    return tuple(sessions)


def build_days(raw_days: Iterable[dict]) -> tuple[Day, ...]:
    days: list[Day] = []
    for raw in raw_days:
        days.append(
            Day(
                id=str(raw.get("id", "")),
                week_report_id=str(raw.get("week_report_id", "")),
                date=_parse_date(raw.get("date")),
                available_minutes=raw.get("available_minutes"),
                planned_minutes=raw.get("planned_minutes"),
                scheduled_minutes=raw.get("scheduled_minutes"),
                done_count=raw.get("done_count"),
                total_count=raw.get("total_count"),
            )
        )
    return tuple(days)


def build_bundle(payload: dict) -> WeekReportBundle:
    report_raw = payload.get("week_report", {})
    report = WeekReport(
        id=str(report_raw.get("id", "")),
        week_id=str(report_raw.get("week_id", "")),
        cycle_start=_parse_date(report_raw.get("cycle_start")),
        cycle_end=_parse_date(report_raw.get("cycle_end")),
        review_at=_parse_datetime(report_raw.get("review_at"), required=True),
        status=str(report_raw.get("status", "draft")),
        prev_week_report_id=report_raw.get("prev_week_report_id"),
        goals_week=tuple(report_raw.get("goals_week", []) or ()),
        goals_month=tuple(report_raw.get("goals_month", []) or ()),
        goals_long=tuple(report_raw.get("goals_long", []) or ()),
        good_points=tuple(report_raw.get("good_points", []) or ()),
        issues=tuple(build_issue(raw) for raw in report_raw.get("issues", []) or ()),
        created_at=_parse_datetime(report_raw.get("created_at"), required=False),
        updated_at=_parse_datetime(report_raw.get("updated_at"), required=False),
    )
    bundle = WeekReportBundle(
        report=report,
        days=build_days(payload.get("days", []) or ()),
        tasks=build_tasks(payload.get("tasks", []) or ()),
        task_sessions=build_task_sessions(payload.get("task_sessions", []) or ()),
        last_week_tasks=build_tasks(payload.get("last_week_tasks", []) or ()),
    )
    validate_report(bundle)
    return bundle


def bundle_to_dict(bundle: WeekReportBundle) -> dict:
    report = bundle.report
    return {
        "week_report": {
            "id": report.id,
            "week_id": report.week_id,
            "cycle_start": report.cycle_start.isoformat(),
            "cycle_end": report.cycle_end.isoformat(),
            "review_at": report.review_at.isoformat(),
            "status": report.status,
            "prev_week_report_id": report.prev_week_report_id,
            "goals_week": list(report.goals_week),
            "goals_month": list(report.goals_month),
            "goals_long": list(report.goals_long),
            "good_points": list(report.good_points),
            "issues": [
                {
                    "problem": issue.problem,
                    "root_cause": issue.root_cause,
                    "improvement": issue.improvement,
                    "tags": list(issue.tags),
                }
                for issue in report.issues
            ],
            "created_at": report.created_at.isoformat() if report.created_at else None,
            "updated_at": report.updated_at.isoformat() if report.updated_at else None,
        },
        "days": [
            {
                "id": day.id,
                "week_report_id": day.week_report_id,
                "date": day.date.isoformat(),
                "available_minutes": day.available_minutes,
                "planned_minutes": day.planned_minutes,
                "scheduled_minutes": day.scheduled_minutes,
                "done_count": day.done_count,
                "total_count": day.total_count,
            }
            for day in bundle.days
        ],
        "tasks": [
            {
                "id": task.id,
                "week_report_id": task.week_report_id,
                "day_id": task.day_id,
                "title": task.title,
                "estimated_minutes": task.estimated_minutes,
                "priority": task.priority,
                "status": task.status,
                "reason_tags": list(task.reason_tags),
                "note": task.note,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            for task in bundle.tasks
        ],
        "task_sessions": [
            {
                "id": session.id,
                "task_id": session.task_id,
                "start_at": session.start_at.isoformat(),
                "end_at": session.end_at.isoformat(),
                "note": session.note,
                "is_completed": session.is_completed,
            }
            for session in bundle.task_sessions
        ],
        "last_week_tasks": [
            {
                "id": task.id,
                "week_report_id": task.week_report_id,
                "day_id": task.day_id,
                "title": task.title,
                "estimated_minutes": task.estimated_minutes,
                "priority": task.priority,
                "status": task.status,
                "reason_tags": list(task.reason_tags),
                "note": task.note,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            }
            for task in bundle.last_week_tasks
        ],
    }


def _parse_date(value: str | None) -> date:
    if not value:
        raise ValueError("date value is required")
    return date.fromisoformat(value)


def _parse_datetime(value: str | None, *, required: bool) -> datetime | None:
    if not value:
        if required:
            raise ValueError("datetime value is required")
        return None
    return datetime.fromisoformat(value)
