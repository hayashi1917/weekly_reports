from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from weekly_reports.metrics import update_day_metrics
from weekly_reports.models import WeekReportBundle, build_bundle, bundle_to_dict
from weekly_reports.snapshot import build_snapshot
from weekly_reports.workflow import init_week_report


class InitWeekRequest(BaseModel):
    review_at: datetime = Field(..., description="Review datetime in ISO format")
    prev_bundle: dict[str, Any] | None = None


class FinalizeRequest(BaseModel):
    bundle: dict[str, Any]
    output_dir: str = "outputs"
    generate_pdf: bool = True


def create_app() -> FastAPI:
    app = FastAPI(title="Weekly Reports API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/weeks/init")
    def init_week(request: InitWeekRequest) -> dict[str, Any]:
        prev_bundle: WeekReportBundle | None = None
        if request.prev_bundle:
            prev_bundle = build_bundle(request.prev_bundle)
        bundle = init_week_report(request.review_at, prev_bundle)
        return bundle_to_dict(bundle)

    @app.post("/api/weeks/finalize")
    def finalize_week(request: FinalizeRequest) -> dict[str, Any]:
        try:
            bundle = build_bundle(request.bundle)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        updated_days = update_day_metrics(bundle.days, bundle.tasks, bundle.task_sessions)
        report = replace(bundle.report, status="final", updated_at=datetime.now())
        updated_bundle = WeekReportBundle(
            report=report,
            days=updated_days,
            tasks=bundle.tasks,
            task_sessions=bundle.task_sessions,
            last_week_tasks=bundle.last_week_tasks,
        )
        output_dir = Path(request.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / f"{bundle.report.week_id}_weekly_report.pdf"
        json_path = output_dir / f"{bundle.report.week_id}_snapshot.json"

        if request.generate_pdf:
            # PDF生成が必要な時だけ reportlab を読み込み、テスト時の依存を軽くする。
            from weekly_reports.pdf import generate_pdf

            generate_pdf(updated_bundle, str(pdf_path))
        snapshot = build_snapshot(updated_bundle, pdf_path=str(pdf_path), json_path=str(json_path))
        json_path.write_text(snapshot_json(snapshot), encoding="utf-8")

        return {
            "bundle": bundle_to_dict(updated_bundle),
            "snapshot": snapshot,
        }

    return app


def snapshot_json(snapshot: dict[str, Any]) -> str:
    import json

    return json.dumps(snapshot, ensure_ascii=False, indent=2)
