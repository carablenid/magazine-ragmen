import os
import re
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
    "User-Agent": "Mozilla/5.0 (compatible; MagazineRagmenBot/1.0)"
}


def _google_news_rss(query: str) -> list[dict]:
    encoded = quote_plus(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=tr&gl=TR&ceid=TR:tr"
    feed = feedparser.parse(url)
    return feed.entries


def _entry_published(entry) -> datetime | None:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    return None


def _og_image(article_url: str) -> str | None:
    try:
        r = requests.get(article_url, headers=HEADERS, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.text, "lxml")
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]
        tag = soup.find("meta", attrs={"name": "twitter:image"})
        if tag and tag.get("content"):
            return tag["content"]
    except Exception:
        pass
    return None


def _resolve_google_url(entry_url: str) -> str:
    """Google News URLs redirect to the actual article."""
    try:
        r = requests.get(entry_url, headers=HEADERS, timeout=8, allow_redirects=True)
        return r.url
    except Exception:
        return entry_url


def scrape_google_news() -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(hours=MAX_NEWS_AGE_HOURS)
    items = []

    for artist in ARTISTS:
        query = ARTIST_SEARCH_TERMS.get(artist, artist)
        try:
            entries = _google_news_rss(query)
        except Exception as e:
            log.warning("RSS fetch failed for %s: %s", artist, e)
            continue

        for entry in entries:
            pub = _entry_published(entry)
            if pub and pub < cutoff:
                continue

            source_url = _resolve_google_url(entry.link)
            image_url = _og_image(source_url)

            items.append(make_item(
                artist=artist,
                title=entry.title,
                summary=getattr(entry, "summary", "")[:400],
                source_url=source_url,
                image_url=image_url,
            ))

    return items


def scrape_youtube() -> list[dict]:
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key or not YOUTUBE_CHANNELS:
        return []

    try:
        from googleapiclient.discovery import build
    except ImportError:
        log.warning("google-api-python-client not installed, skipping YouTube.")
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
            log.warning("YouTube fetch failed for %s: %s", artist, e)
            continue

        for v in resp.get("items", []):
            snippet = v["snippet"]
            video_id = v["id"]["videoId"]
            thumb = snippet["thumbnails"].get("maxres") or snippet["thumbnails"].get("high", {})
            items.append(make_item(
                artist=artist,
                title=snippet["title"],
                summary=snippet.get("description", "")[:400],
                source_url=f"https://www.youtube.com/watch?v={video_id}",
                image_url=thumb.get("url"),
            ))

    return items


def scrape_all() -> list[dict]:
    log.info("Scraping Google News...")
    news = scrape_google_news()
    log.info("Found %d news items.", len(news))

    log.info("Scraping YouTube...")
    yt = scrape_youtube()
    log.info("Found %d YouTube items.", len(yt))

    return news + yt
