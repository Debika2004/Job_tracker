import json
from typing import Any

from openai import OpenAI

from app.config import get_settings


PROMPT = """
You extract job application data from email text.
Return strict JSON only with these keys:
company, role, location, application_url, status, deadline, salary, summary
If a field is unknown, return null for that field.
""".strip()


def extract_job_fields(email_item: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    user_content = {
        "subject": email_item.get("subject"),
        "from": email_item.get("from"),
        "date": email_item.get("date"),
        "snippet": email_item.get("snippet"),
        "body": email_item.get("body"),
    }

    try:
        completion = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            temperature=0,
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
            ],
        )
        content = completion.choices[0].message.content or "{}"
        extracted = json.loads(content)
        return extracted if isinstance(extracted, dict) else {}
    except Exception:
        return {}
