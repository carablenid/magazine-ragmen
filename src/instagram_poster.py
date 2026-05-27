import os
import logging
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

log = logging.getLogger(__name__)

SESSION_FILE = Path("session.json")
_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is not None:
        return _client

    cl = Client()
    cl.delay_range = [2, 5]

    session_id = os.environ.get("INSTAGRAM_SESSION_ID")
    username = os.environ["INSTAGRAM_USERNAME"]
    password = os.environ["INSTAGRAM_PASSWORD"]

    if session_id:
        # Challenge yok — browser session ID ile giriş
        try:
            cl.login_by_sessionid(session_id)
            log.info("Session ID ile giriş başarılı.")
            cl.dump_settings(str(SESSION_FILE))
            _client = cl
            return cl
        except Exception as e:
            log.warning("Session ID ile giriş başarısız: %s — username/password deniyor.", e)

    if SESSION_FILE.exists():
        try:
            cl.load_settings(str(SESSION_FILE))
            cl.login(username, password)
            log.info("Kayıtlı session ile giriş başarılı.")
            _client = cl
            return cl
        except Exception as e:
            log.warning("Kayıtlı session geçersiz: %s — yeniden giriş yapılıyor.", e)
            _client = None
            cl = Client()
            cl.delay_range = [2, 5]

    cl.login(username, password)
    cl.dump_settings(str(SESSION_FILE))
    log.info("Yeni session oluşturuldu.")
    _client = cl
    return cl


def post_photo(image_path: str, caption: str) -> str:
    cl = _get_client()
    try:
        media = cl.photo_upload(image_path, caption)
    except (LoginRequired, Exception) as e:
        if "login" in str(e).lower() or "session" in str(e).lower():
            log.warning("Session süresi dolmuş, yeniden giriş yapılıyor.")
            global _client
            _client = None
            cl = _get_client()
            media = cl.photo_upload(image_path, caption)
        else:
            raise
    cl.dump_settings(str(SESSION_FILE))
    log.info("Post yayınlandı: %s", media.pk)
    return str(media.pk)
