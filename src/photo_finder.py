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

_WIKI_VARIANTS = [
    "{artist}",
    "{artist} (rapper)",
    "{artist} (musician)",
]


def _ascii_slug(text: str) -> str:
    return (
        text.replace("ş", "s").replace("Ş", "S")
        .replace("ı", "i").replace("İ", "I")
        .replace("ğ", "g").replace("Ğ", "G")
        .replace("ü", "u").replace("Ü", "U")
        .replace("ö", "o").replace("Ö", "O")
        .replace("ç", "c").replace("Ç", "C")
    )


def _wikipedia_image_url(artist: str) -> str | None:
    names = [artist, _ascii_slug(artist)]
    for variant in _WIKI_VARIANTS:
        for name in names:
            title = variant.format(artist=name)
            try:
                url = (
                    "https://en.wikipedia.org/api/rest_v1/page/summary/"
                    + requests.utils.quote(title, safe="")
                )
                r = requests.get(url, headers=HEADERS, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    thumb = data.get("originalimage", {}).get("source") or data.get("thumbnail", {}).get("source")
                    if thumb:
                        log.info("Wikipedia'dan fotoğraf bulundu: %s", title)
                        return thumb
            except Exception as e:
                log.debug("Wikipedia sorgusu başarısız (%s): %s", title, e)
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
    url = _wikipedia_image_url(artist)
    if not url:
        log.warning("'%s' için Wikipedia'da fotoğraf bulunamadı — fallback kullanılacak.", artist)
        return None
    img = _download_and_resize(url)
    if img:
        log.info("'%s' fotoğrafı Wikipedia'dan alındı.", artist)
    return img
