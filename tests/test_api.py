import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from weekly_reports.api import create_app


def test_init_week_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post("/api/weeks/init", json={"review_at": "2026-01-16T18:00:00"})
    assert response.status_code == 200
    payload = response.json()
    assert "week_report" in payload
    assert len(payload["days"]) == 7


def test_finalize_endpoint() -> None:
    client = TestClient(create_app())
    bundle = {
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
    response = client.post(
        "/api/weeks/finalize",
        json={"bundle": bundle, "generate_pdf": False, "output_dir": "outputs"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["snapshot"]["schema_version"] == "1.0"
