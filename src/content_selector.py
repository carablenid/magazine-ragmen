from datetime import datetime

from src.queue_manager import get_posted_ids

FUN_FACT_THRESHOLD_HOURS = 48

PRIORITY_KEYWORDS = {
    "yeni şarkı": 10, "yeni albüm": 10, "single": 8, "klip": 8,
    "konser": 6, "tur": 6, "collab": 5, "feat": 5,
    "kavga": 4, "olay": 4, "kriz": 4, "açıklama": 3,
}


def _score(item: dict) -> int:
    text = (item["title"] + " " + item.get("summary", "")).lower()
    score = 0
    for keyword, weight in PRIORITY_KEYWORDS.items():
        if keyword in text:
            score += weight
    # Recency bonus: yayın tarihi varsa onu, yoksa scrape tarihini kullan
    try:
        ref_date = item.get("published_at") or item["scraped_at"]
        age_hours = (datetime.utcnow() - datetime.fromisoformat(ref_date)).total_seconds() / 3600
        score += max(0, 168 - age_hours)  # 7 gün içindeyse bonus
    except Exception:
        pass
    # Prefer items with an image
    if item.get("image_url"):
        score += 5
    return score


def _age_hours(item: dict) -> float:
    try:
        ref_date = item.get("published_at") or item["scraped_at"]
        return (datetime.utcnow() - datetime.fromisoformat(ref_date)).total_seconds() / 3600
    except Exception:
        return 999


def select_items(candidates: list[dict], n: int) -> list[dict]:
    posted_ids = get_posted_ids()
    fresh = [i for i in candidates if i["id"] not in posted_ids]
    ranked = sorted(fresh, key=_score, reverse=True)
    selected = ranked[:n]
    for item in selected:
        item["is_fun_fact"] = _age_hours(item) > FUN_FACT_THRESHOLD_HOURS
    return selected
