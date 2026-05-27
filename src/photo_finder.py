import io
import logging

import requests
from PIL import Image

from config import IMAGE_SIZE

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

_SEARCH_QUERIES = [
    "{artist} rapper türkiye",
    "{artist} müzisyen",
    "{artist} türkçe rap",
    "{artist}",
]


def _search_image_url(artist: str) -> str | None:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        log.error("duckduckgo-search paketi yüklü değil.")
        return None

    for template in _SEARCH_QUERIES:
        query = template.format(artist=artist)
        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    query,
                    max_results=15,
                    size="Large",
                    type_image="photo",
                ))
            for r in results:
                url = r.get("image", "")
                if url.startswith("http"):
                    return url
        except Exception as e:
            log.warning("DuckDuckGo sorgusu başarısız (%s): %s", query, e)
            continue
    return None


def _download_and_resize(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        iw, ih = img.size
        side = min(iw, ih)
        left = (iw - side) // 2
        top = (ih - side) // 2
        img = img.crop((left, top, left + side, top + side))
        return img.resize(IMAGE_SIZE, Image.LANCZOS)
    except Exception as e:
        log.warning("Görsel indirilemedi (%s): %s", url, e)
        return None


def find_artist_photo(artist: str) -> Image.Image | None:
    url = _search_image_url(artist)
    if not url:
        log.warning("'%s' için fotoğraf URL'i bulunamadı.", artist)
        return None
    img = _download_and_resize(url)
    if img is None:
        log.warning("'%s' fotoğrafı indirilemedi.", artist)
    else:
        log.info("'%s' fotoğrafı başarıyla indirildi.", artist)
    return img
