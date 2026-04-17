from contextlib import asynccontextmanager
import logging
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException, Query

from app.config import get_settings
from app.db import close_client
from app.services.gmail_service import create_authorization_url, exchange_code_for_token
from app.services.job_pipeline import get_latest_jobs, run_pipeline_once

scheduler = BackgroundScheduler(timezone="UTC")
logger = logging.getLogger(__name__)


def _scheduled_job() -> None:
    try:
        run_pipeline_once()
    except Exception:
        logger.exception("Scheduled Gmail job pipeline failed.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    scheduler.add_job(
        _scheduled_job,
        "interval",
        minutes=settings.scheduler_interval_minutes,
        id="gmail-job-sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
        close_client()


app = FastAPI(title="Job Tracker MVP Backend", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/gmail/oauth/start")
def gmail_oauth_start() -> dict[str, str]:
    auth_url = create_authorization_url()
    return {"auth_url": auth_url}


@app.get("/api/gmail/oauth/callback")
def gmail_oauth_callback(code: str = Query(..., min_length=1)) -> dict[str, str]:
    token_path = exchange_code_for_token(code)
    return {
        "message": "OAuth completed and token stored.",
        "token_path": str(token_path),
    }


@app.post("/api/jobs/run-once")
def run_once() -> dict[str, Any]:
    try:
        return run_pipeline_once()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/jobs/latest")
def latest_jobs(limit: int = Query(20, ge=1, le=100)) -> dict[str, list[dict[str, Any]]]:
    try:
        return {"jobs": get_latest_jobs(limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
