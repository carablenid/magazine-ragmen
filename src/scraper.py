import os
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup

from config import ARTISTS, ARTIST_SEARCH_TERMS, MAX_NEWS_AGE_HOURS, YOUTUBE_CHANNELS
from src.queue_manager import make_item

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9",
}


def _fetch_rss(url: str) -> feedparser.FeedParserDict:
    # Önce requests ile dene (daha iyi header kontrolü)
    try:
        r = requests.get(url, headers={**HEADERS, "Accept": "application/rss+xml,application/xml,*/*"}, timeout=12)
        if r.status_code == 200 and len(r.content) > 500:
            feed = feedparser.parse(r.content)
            if feed.entries:
                return feed
            log.debug("requests ile boş feed, feedparser fallback deneniyor.")
        else:
            log.warning("RSS HTTP %s (%d byte), fallback deneniyor.", r.status_code, len(r.content))
    except Exception as e:
        log.warning("RSS requests hatası: %s", e)

    # Fallback: feedparser doğrudan URL çeksin
    try:
        feed = feedparser.parse(url)
        return feed
    except Exception as e:
        log.warning("RSS feedparser hatası: %s", e)
        return feedparser.FeedParserDict(entries=[])


def _entry_published(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return None


def _extract_image_from_summary(summary: str) -> str | None:
    """Google News RSS summary'sindeki img tag'inden URL çek."""
    try:
        soup = BeautifulSoup(summary, "lxml")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    except Exception:
        pass
    return None


def _og_image(article_url: str) -> str | None:
    try:
        r = requests.get(article_url, headers=HEADERS, timeout=6, allow_redirects=True)
        soup = BeautifulSoup(r.text, "lxml")
        for prop in ("og:image", "twitter:image"):
            tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                return tag["content"]
    except Exception:
        pass
    return None


def scrape_google_news() -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(hours=MAX_NEWS_AGE_HOURS)
    items = []

    for artist in ARTISTS:
        query = ARTIST_SEARCH_TERMS.get(artist, artist)
        encoded = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=tr&gl=TR&ceid=TR:tr"
        feed = _fetch_rss(url)

        log.info("  %s → %d entry", artist, len(feed.entries))

        for entry in feed.entries:
            pub = _entry_published(entry)
            if pub and pub < cutoff:
                continue

            # Önce summary'den resim çekmeyi dene (hızlı)
            summary = getattr(entry, "summary", "") or ""
            image_url = _extract_image_from_summary(summary)

            # Yoksa article'a git (yavaş ama daha iyi)
            if not image_url:
                image_url = _og_image(entry.link)

            pub = _entry_published(entry)
            item = make_item(
                artist=artist,
                title=entry.title,
                summary=BeautifulSoup(summary, "lxml").get_text()[:400],
                source_url=entry.link,
                image_url=image_url,
            )
            if pub:
                item["published_at"] = pub.isoformat()
            items.append(item)

    return items


def scrape_youtube() -> list[dict]:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key or not YOUTUBE_CHANNELS:
        return []

    try:
        from googleapiclient.discovery import build
    except ImportError:
        return []

    cutoff = datetime.utcnow() - timedelta(hours=MAX_NEWS_AGE_HOURS)
    youtube = build("youtube", "v3", developerKey=api_key)
    items = []

    for channel_id, artist in YOUTUBE_CHANNELS.items():
        try:
            resp = youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=5,
                order="date",
                type="video",
                publishedAfter=cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ).execute()
        except Exception as e:
            log.warning("YouTube hatası (%s): %s", artist, e)
            continue

        for v in resp.get("items", []):
            snippet = v["snippet"]
            video_id = v["id"]["videoId"]
            thumb = (snippet["thumbnails"].get("maxres")
                     or snippet["thumbnails"].get("high", {}))
            items.append(make_item(
                artist=artist,
                title=snippet["title"],
                summary=snippet.get("description", "")[:400],
                source_url=f"https://www.youtube.com/watch?v={video_id}",
                image_url=thumb.get("url"),
            ))

    return items


def scrape_all() -> list[dict]:
    log.info("Scraping Google News (%d sanatçı)...", len(ARTISTS))
    news = scrape_google_news()
    log.info("Toplam %d haber bulundu.", len(news))

    yt = scrape_youtube()
    if yt:
        log.info("%d YouTube haberi bulundu.", len(yt))

    return news + yt
