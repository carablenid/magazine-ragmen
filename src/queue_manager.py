import json
import uuid
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

from config import QUEUE_MAX_AGE_DAYS

PER_ARTIST_QUEUE_LIMIT = 2  # Kuyrukta sanatçı başına max item

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
    artist_counts = Counter(item["artist"] for item in data["queue"])
    added = 0
    for item in items:
        if item["id"] in posted_ids or item["id"] in existing_ids:
            continue
        if artist_counts[item["artist"]] >= PER_ARTIST_QUEUE_LIMIT:
            continue
        data["queue"].append(item)
        artist_counts[item["artist"]] += 1
        added += 1
    data["last_scrape"] = datetime.utcnow().isoformat()
    _save(data)
    return added


def pop_items(n: int) -> list[dict]:
    """Round-robin: her slot farklı sanatçıdan, son postlardaki artistler son sıraya."""
    data = _load()
    queue = data["queue"]

    recent_artists = {item["artist"] for item in data.get("posted", [])[-5:]}
    seen: set[str] = set()
    selected = []

    # Pass 1: son 5 postta olmayan sanatçılar — sanatçı başına 1 slot
    for item in queue:
        if len(selected) >= n:
            break
        if item["artist"] not in recent_artists and item["artist"] not in seen:
            selected.append(item)
            seen.add(item["artist"])

    # Pass 2: kalan slotlar için recent sanatçılar — yine sanatçı başına 1
    if len(selected) < n:
        for item in queue:
            if len(selected) >= n:
                break
            if item["artist"] not in seen:
                selected.append(item)
                seen.add(item["artist"])

    # Pass 3: hâlâ dolmadıysa kalan her şey
    if len(selected) < n:
        leftovers = [i for i in queue if i["id"] not in {s["id"] for s in selected}]
        selected.extend(leftovers[:n - len(selected)])

    selected_ids = {item["id"] for item in selected}
    data["queue"] = [i for i in queue if i["id"] not in selected_ids]
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
