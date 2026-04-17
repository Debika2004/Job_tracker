from datetime import datetime, timezone
from typing import Any

from app.config import get_settings
from app.db import get_jobs_collection
from app.services.gmail_service import fetch_messages
from app.services.openai_service import extract_job_fields


def run_pipeline_once() -> dict[str, Any]:
    settings = get_settings()
    emails = fetch_messages(settings.gmail_query, settings.gmail_max_results)

    if not emails:
        return {"processed": 0, "inserted": 0}

    docs: list[dict[str, Any]] = []
    for email_item in emails:
        extracted = extract_job_fields(email_item)
        docs.append(
            {
                "processed_at": datetime.now(timezone.utc),
                "source": "gmail",
                "gmail": {
                    "gmail_message_id": email_item.get("gmail_message_id"),
                    "thread_id": email_item.get("thread_id"),
                    "subject": email_item.get("subject"),
                    "from": email_item.get("from"),
                    "date": email_item.get("date"),
                    "snippet": email_item.get("snippet"),
                },
                "extracted": extracted,
            }
        )

    collection = get_jobs_collection()
    insert_result = collection.insert_many(docs)

    return {"processed": len(emails), "inserted": len(insert_result.inserted_ids)}


def get_latest_jobs(limit: int = 20) -> list[dict[str, Any]]:
    collection = get_jobs_collection()
    cursor = collection.find({}, {"gmail.raw": 0}).sort("processed_at", -1).limit(limit)

    jobs: list[dict[str, Any]] = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        jobs.append(doc)
    return jobs
