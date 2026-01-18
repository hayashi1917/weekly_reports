from __future__ import annotations

from collections import defaultdict

from weekly_reports.models import Day, Task, TaskSession


def update_day_metrics(
    days: tuple[Day, ...],
    tasks: tuple[Task, ...],
    task_sessions: tuple[TaskSession, ...],
) -> tuple[Day, ...]:
    tasks_by_day: dict[str, list[Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_day[task.day_id].append(task)

    sessions_by_task: dict[str, list[TaskSession]] = defaultdict(list)
    for session in task_sessions:
        sessions_by_task[session.task_id].append(session)

    updated_days: list[Day] = []
    for day in days:
        day_tasks = tasks_by_day.get(day.id, [])
        planned_minutes = sum(task.estimated_minutes for task in day_tasks)
        total_count = len(day_tasks)
        done_count = sum(1 for task in day_tasks if task.status == "done")
        scheduled_minutes = 0
        for task in day_tasks:
            for session in sessions_by_task.get(task.id, []):
                delta = session.end_at - session.start_at
                scheduled_minutes += int(delta.total_seconds() // 60)

        updated_days.append(
            Day(
                id=day.id,
                week_report_id=day.week_report_id,
                date=day.date,
                available_minutes=day.available_minutes,
                planned_minutes=planned_minutes,
                scheduled_minutes=scheduled_minutes,
                done_count=done_count,
                total_count=total_count,
            )
        )
    return tuple(updated_days)
