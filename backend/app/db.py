from pymongo import MongoClient
from pymongo.collection import Collection

from app.config import get_settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_jobs_collection() -> Collection:
    settings = get_settings()
    client = get_client()
    return client[settings.mongodb_db][settings.mongodb_collection]


def close_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
