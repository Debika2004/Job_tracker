from datetime import datetime, timezone
from typing import Any

from pymongo import UpdateOne

from app.config import get_settings
from app.db import get_jobs_collection
from app.services.gmail_service import fetch_messages
from app.services.openai_service import extract_job_fields


def run_pipeline_once() -> dict[str, Any]:
    settings = get_settings()
    emails = fetch_messages(settings.gmail_query, settings.gmail_max_results)

    if not emails:
        return {"processed": 0, "inserted": 0}

    operations: list[UpdateOne] = []
    for email_item in emails:
        extracted = extract_job_fields(email_item)
        gmail_message_id = email_item.get("gmail_message_id")
        if not gmail_message_id:
            continue

        operations.append(
            UpdateOne(
                {"gmail.gmail_message_id": gmail_message_id},
                {
                    "$set": {
                        "processed_at": datetime.now(timezone.utc),
                        "source": "gmail",
                        "gmail": {
                            "gmail_message_id": gmail_message_id,
                            "thread_id": email_item.get("thread_id"),
                            "subject": email_item.get("subject"),
                            "from": email_item.get("from"),
                            "date": email_item.get("date"),
                            "snippet": email_item.get("snippet"),
                        },
                        "extracted": extracted,
                    }
                },
                upsert=True,
            )
        )

    if not operations:
        return {"processed": len(emails), "inserted": 0, "updated": 0}

    collection = get_jobs_collection()
    result = collection.bulk_write(operations, ordered=False)

    return {
        "processed": len(emails),
        "inserted": result.upserted_count,
        "updated": result.modified_count,
    }


def get_latest_jobs(limit: int = 20) -> list[dict[str, Any]]:
    collection = get_jobs_collection()
    cursor = collection.find({}, {"gmail.raw": 0}).sort("processed_at", -1).limit(limit)

    jobs: list[dict[str, Any]] = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        jobs.append(doc)
    return jobs
