import os
import logging
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

log = logging.getLogger(__name__)

SESSION_FILE = Path("session.json")


def _get_client() -> Client:
    cl = Client()
    cl.delay_range = [2, 5]

    username = os.environ["INSTAGRAM_USERNAME"]
    password = os.environ["INSTAGRAM_PASSWORD"]

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(username, password)
            log.info("Mevcut session ile giriş yapıldı.")
            return cl
        except (LoginRequired, Exception) as e:
            log.warning("Session geçersiz, yeniden giriş: %s", e)

    cl.login(username, password)
    cl.dump_settings(str(SESSION_FILE))
    log.info("Yeni session oluşturuldu.")
    return cl


def post_photo(image_path: str, caption: str) -> str:
    cl = _get_client()
    try:
        media = cl.photo_upload(image_path, caption)
    except PleaseWaitFewMinutes as e:
        raise RuntimeError(f"Instagram rate limit: {e}")
    cl.dump_settings(str(SESSION_FILE))
    log.info("Post yayınlandı: %s", media.pk)
    return str(media.pk)
