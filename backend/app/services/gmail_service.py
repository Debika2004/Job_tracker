import base64
import json
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import get_settings


def _token_path() -> Path:
    settings = get_settings()
    return Path(settings.gmail_token_path)


def _scopes() -> list[str]:
    settings = get_settings()
    return [scope.strip() for scope in settings.gmail_scopes.split(",") if scope.strip()]


def _oauth_client_config() -> dict[str, Any]:
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.google_client_id,
            "project_id": "job-tracker-mvp",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": settings.google_client_secret,
            "redirect_uris": [settings.google_redirect_uri],
        }
    }


def create_authorization_url() -> str:
    settings = get_settings()
    flow = Flow.from_client_config(_oauth_client_config(), scopes=_scopes())
    flow.redirect_uri = settings.google_redirect_uri
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_token(code: str) -> Path:
    settings = get_settings()
    flow = Flow.from_client_config(_oauth_client_config(), scopes=_scopes())
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    token_file = _token_path()
    token_file.write_text(flow.credentials.to_json(), encoding="utf-8")
    return token_file


def _load_credentials() -> Credentials:
    token_file = _token_path()
    if not token_file.exists():
        raise RuntimeError("Gmail OAuth token not found. Complete /api/gmail/oauth/start first.")

    credentials = Credentials.from_authorized_user_file(str(token_file), _scopes())
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token_file.write_text(credentials.to_json(), encoding="utf-8")

    if not credentials.valid:
        raise RuntimeError("Gmail OAuth token is invalid. Re-run OAuth flow.")

    return credentials


def _decode_body(payload: dict[str, Any]) -> str:
    body_data = payload.get("body", {}).get("data")
    if body_data:
        decoded = base64.urlsafe_b64decode(body_data + "==")
        return decoded.decode("utf-8", errors="ignore")

    text_chunks: list[str] = []
    for part in payload.get("parts", []) or []:
        mime_type = part.get("mimeType", "")
        if mime_type.startswith("text/"):
            part_data = part.get("body", {}).get("data")
            if part_data:
                decoded = base64.urlsafe_b64decode(part_data + "==")
                text_chunks.append(decoded.decode("utf-8", errors="ignore"))
        elif part.get("parts"):
            text_chunks.append(_decode_body(part))

    return "\n".join(chunk for chunk in text_chunks if chunk)


def _header_map(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {
        str(item.get("name", "")).lower(): str(item.get("value", ""))
        for item in headers or []
    }


def fetch_messages(query: str, max_results: int) -> list[dict[str, Any]]:
    credentials = _load_credentials()
    gmail = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    response = (
        gmail.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    messages = response.get("messages", [])

    parsed: list[dict[str, Any]] = []
    for message in messages:
        message_id = message.get("id")
        if not message_id:
            continue

        raw = (
            gmail.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = raw.get("payload", {})
        headers = _header_map(payload.get("headers", []))
        parsed.append(
            {
                "gmail_message_id": raw.get("id"),
                "thread_id": raw.get("threadId"),
                "internal_date": raw.get("internalDate"),
                "snippet": raw.get("snippet", ""),
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "date": headers.get("date", ""),
                "body": _decode_body(payload),
                "raw": json.dumps(raw, ensure_ascii=False),
            }
        )

    return parsed
