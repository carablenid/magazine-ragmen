import os
import json
import base64
import logging
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

SESSION_FILE = Path("playwright_session.json")


def _load_session_path() -> str:
    """Session'ı geçici bir dosyaya yaz ve yolunu döndür."""
    b64 = os.environ.get("INSTAGRAM_PLAYWRIGHT_SESSION")
    if b64:
        b64 = b64.encode("ascii", errors="ignore").decode("ascii").strip()
        data = base64.b64decode(b64)
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="wb")
        tmp.write(data)
        tmp.close()
        return tmp.name
    if SESSION_FILE.exists():
        return str(SESSION_FILE.resolve())
    raise RuntimeError(
        "Instagram session bulunamadı. "
        "create_session.py çalıştırarak playwright_session.json oluştur."
    )


def post_photo(image_path: str, caption: str) -> str:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    session_path = _load_session_path()
    abs_path = str(Path(image_path).resolve())

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(
            storage_state=session_path,
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        log.info("Instagram ana sayfasına gidiliyor...")
        page.goto("https://www.instagram.com/", wait_until="networkidle", timeout=30000)

        if "accounts/login" in page.url:
            browser.close()
            raise RuntimeError("Instagram session geçersiz. create_session.py ile yenile.")

        log.info("Yeni post akışı başlatılıyor...")

        # "Create" / yeni post butonuna tıkla
        page.click('a[href="/create/select/"], svg[aria-label="New post"], '
                   '[aria-label="New post"]', timeout=10000)

        # Dosya seçici
        with page.expect_file_chooser(timeout=10000) as fc_info:
            page.click('button:has-text("Select from computer")', timeout=8000)
        fc_info.value.set_files(abs_path)
        log.info("Görsel yüklendi.")

        # Crop ekranı → Next
        page.wait_for_selector('div[role="dialog"] button:has-text("Next")', timeout=20000)
        page.click('div[role="dialog"] button:has-text("Next")')

        # Filter ekranı → Next
        page.wait_for_selector('div[role="dialog"] button:has-text("Next")', timeout=10000)
        page.click('div[role="dialog"] button:has-text("Next")')

        # Caption ekranı
        caption_sel = 'div[role="dialog"] div[role="textbox"], div[role="dialog"] textarea'
        page.wait_for_selector(caption_sel, timeout=10000)
        page.fill(caption_sel, caption)
        log.info("Caption girildi.")

        # Share
        page.click('div[role="dialog"] button:has-text("Share")', timeout=10000)
        page.wait_for_timeout(5000)  # Post işleminin tamamlanması için bekle
        log.info("Post paylaşıldı!")

        browser.close()

    return "posted_via_playwright"
