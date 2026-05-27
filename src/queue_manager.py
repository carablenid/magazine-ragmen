import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from config import QUEUE_MAX_AGE_DAYS

QUEUE_PATH = Path("data/queue.json")


def _load() -> dict:
    if not QUEUE_PATH.exists():
        return {"queue": [], "posted": [], "last_scrape": None}
    with open(QUEUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_queue() -> list[dict]:
    return _load()["queue"]


def get_posted_ids() -> set[str]:
    data = _load()
    return {item["id"] for item in data.get("posted", [])}


def add_items(items: list[dict]) -> int:
    data = _load()
    posted_ids = {item["id"] for item in data["posted"]}
    existing_ids = {item["id"] for item in data["queue"]}
    added = 0
    for item in items:
        if item["id"] not in posted_ids and item["id"] not in existing_ids:
            data["queue"].append(item)
            added += 1
    data["last_scrape"] = datetime.utcnow().isoformat()
    _save(data)
    return added


def pop_items(n: int) -> list[dict]:
    data = _load()
    selected = data["queue"][:n]
    data["queue"] = data["queue"][n:]
    _save(data)
    return selected


def mark_as_posted(items: list[dict]) -> None:
    data = _load()
    for item in items:
        item["posted_at"] = datetime.utcnow().isoformat()
        data["posted"].append(item)
    _save(data)


def clean_old_items() -> None:
    data = _load()
    cutoff = datetime.utcnow() - timedelta(days=QUEUE_MAX_AGE_DAYS)
    data["queue"] = [
        i for i in data["queue"]
        if datetime.fromisoformat(i["scraped_at"]) > cutoff
    ]
    data["posted"] = [
        i for i in data["posted"]
        if datetime.fromisoformat(i.get("posted_at", i["scraped_at"])) > cutoff
    ]
    _save(data)


def queue_size() -> int:
    return len(_load()["queue"])


def make_item(artist: str, title: str, summary: str, source_url: str,
              image_url: str | None) -> dict:
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, source_url)),
        "artist": artist,
        "title": title,
        "summary": summary,
        "source_url": source_url,
        "image_url": image_url,
        "scraped_at": datetime.utcnow().isoformat(),
    }
