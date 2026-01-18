from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from weekly_reports.models import Day, Task, TaskSession, WeekReportBundle


def _section(title: str, body_lines: list[str]) -> list:
    styles = getSampleStyleSheet()
    items = [Paragraph(f"<b>{title}</b>", styles["Heading3"])]
    if body_lines:
        items.append(Paragraph("<br/>".join(body_lines), styles["BodyText"]))
    else:
        items.append(Paragraph("(未記入)", styles["BodyText"]))
    items.append(Spacer(1, 0.4 * cm))
    return items


def _issues_section(issues) -> list:
    styles = getSampleStyleSheet()
    items = [Paragraph("<b>課題/原因/改善策</b>", styles["Heading3"])]
    rows = [["課題", "根本原因", "改善策", "タグ"]]
    for issue in issues:
        rows.append([issue.problem, issue.root_cause, issue.improvement, ", ".join(issue.tags)])
    if len(rows) == 1:
        rows.append(["(未記入)", "", "", ""])
    table = Table(rows, colWidths=[5 * cm, 5 * cm, 5 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    items.append(table)
    items.append(Spacer(1, 0.4 * cm))
    return items


def _task_table(title: str, tasks: tuple[Task, ...]) -> list:
    styles = getSampleStyleSheet()
    items = [Paragraph(f"<b>{title}</b>", styles["Heading3"])]
    rows = [["タスク", "見積(分)", "主担当日", "状態", "理由タグ"]]
    for task in tasks:
        rows.append(
            [
                task.title,
                str(task.estimated_minutes),
                task.day_id,
                task.status,
                ", ".join(task.reason_tags),
            ]
        )
    if len(rows) == 1:
        rows.append(["(未記入)", "", "", "", ""])
    table = Table(rows, colWidths=[7 * cm, 2.5 * cm, 3 * cm, 3 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    items.append(table)
    items.append(Spacer(1, 0.4 * cm))
    return items


def _day_table(days: tuple[Day, ...]) -> list:
    styles = getSampleStyleSheet()
    items = [Paragraph("<b>来週タスク（日付行）</b>", styles["Heading3"])]
    rows = [["日付", "曜日", "見積合計(分)", "セッション合計(分)", "完了率"]]
    for day in days:
        weekday = day.date.strftime("%a")
        total = day.total_count or 0
        done = day.done_count or 0
        rate = f"{done}/{total}" if total else "0/0"
        rows.append(
            [
                day.date.isoformat(),
                weekday,
                str(day.planned_minutes or 0),
                str(day.scheduled_minutes or 0),
                rate,
            ]
        )
    if len(rows) == 1:
        rows.append(["(未記入)", "", "", "", ""])
    table = Table(rows, colWidths=[4 * cm, 2.5 * cm, 3.5 * cm, 3.5 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    items.append(table)
    items.append(Spacer(1, 0.4 * cm))
    return items


def _session_table(sessions: tuple[TaskSession, ...], tasks: tuple[Task, ...]) -> list:
    styles = getSampleStyleSheet()
    items = [Paragraph("<b>タスク実行枠</b>", styles["Heading3"])]
    task_map = {task.id: task for task in tasks}
    rows = [["タスク", "開始", "終了", "完了", "メモ"]]
    for session in sessions:
        task_title = task_map.get(session.task_id).title if task_map.get(session.task_id) else "-"
        rows.append(
            [
                task_title,
                session.start_at.strftime("%Y-%m-%d %H:%M"),
                session.end_at.strftime("%Y-%m-%d %H:%M"),
                "済" if session.is_completed else "未",
                session.note or "",
            ]
        )
    if len(rows) == 1:
        rows.append(["(未記入)", "", "", "", ""])
    table = Table(rows, colWidths=[6 * cm, 4 * cm, 4 * cm, 2 * cm, 3 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    items.append(table)
    items.append(Spacer(1, 0.4 * cm))
    return items


def generate_pdf(bundle: WeekReportBundle, output_path: str) -> Path:
    path = Path(output_path)
    report = bundle.report
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=1.2 * cm, leftMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    next_review = report.review_at + timedelta(days=7)

    story: list = [
        Paragraph(
            "<b>Weekly Report</b><br/>"
            f"特訓日時: {report.review_at.strftime('%Y-%m-%d %H:%M')}<br/>"
            f"次回日時: {next_review.strftime('%Y-%m-%d %H:%M')}<br/>"
            f"期間: {report.cycle_start} ~ {report.cycle_end}<br/>"
            f"状態: {report.status}",
            styles["Title"],
        ),
        Spacer(1, 0.5 * cm),
    ]

    story.extend(_section("週目標", list(report.goals_week)))
    story.extend(_section("月目標", list(report.goals_month)))
    story.extend(_section("長期目標", list(report.goals_long)))

    story.extend(_task_table("先週の宿題（実績）", bundle.last_week_tasks))
    story.extend(_day_table(bundle.days))
    story.extend(_task_table("来週タスク", bundle.tasks))

    story.extend(_section("GOOD", list(report.good_points)))
    story.extend(_issues_section(report.issues))
    story.extend(_session_table(bundle.task_sessions, bundle.tasks))

    doc.build(story)
    return path
