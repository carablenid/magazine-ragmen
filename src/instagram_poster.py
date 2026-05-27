import os
import base64
import logging
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

SESSION_FILE = Path("playwright_session.json")
SCREENSHOT_DIR = Path("/tmp/ig_debug")


def _load_session_path() -> str:
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


def _shot(page, name: str):
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = str(SCREENSHOT_DIR / f"{name}.png")
    page.screenshot(path=path, full_page=False)
    log.info("Screenshot: %s", path)


def _click_first(page, selectors: list[str], timeout: int = 8000):
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            page.click(sel, timeout=timeout)
            return sel
        except Exception:
            continue
    raise RuntimeError(f"Hiçbir selector bulunamadı: {selectors}")


def _js_click_text(page, text: str) -> bool:
    """DOM'da exact text ile eşleşen görünür ilk elemente JS click atar."""
    return page.evaluate(f"""
        () => {{
            const all = document.querySelectorAll('*');
            for (const el of all) {{
                if (el.children.length === 0 &&
                    el.textContent.trim() === '{text}' &&
                    el.offsetParent !== null) {{
                    el.dispatchEvent(new MouseEvent('click', {{bubbles: true, cancelable: true}}));
                    return true;
                }}
            }}
            return false;
        }}
    """)


def post_photo(image_path: str, caption: str) -> str:
    from playwright.sync_api import sync_playwright

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
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        _shot(page, "01_homepage")

        if "accounts/login" in page.url:
            browser.close()
            raise RuntimeError("Instagram session geçersiz. create_session.py ile yenile.")

        log.info("Mevcut URL: %s", page.url)
        log.info("Yeni post akışı başlatılıyor...")

        # Create butonu
        _click_first(page, [
            'a[href="/create/select/"]',
            '[aria-label="New post"]',
            'svg[aria-label="New post"]',
        ], timeout=10000)
        page.wait_for_timeout(2000)
        _shot(page, "02_after_create_click")

        # Dosya seçici
        with page.expect_file_chooser(timeout=15000) as fc_info:
            _click_first(page, [
                'button:has-text("Select from computer")',
                '[role="button"]:has-text("Select from computer")',
            ], timeout=10000)
        fc_info.value.set_files(abs_path)
        log.info("Görsel yüklendi, crop ekranı bekleniyor...")
        page.wait_for_timeout(4000)
        _shot(page, "03_after_file_upload")

        # Crop ekranı → Next
        _click_first(page, [
            'text=Next',
            '[role="button"]:has-text("Next")',
            'span:has-text("Next")',
        ], timeout=15000)
        log.info("Crop Next tıklandı.")
        page.wait_for_timeout(2000)
        _shot(page, "04_after_crop_next")

        # Filter ekranı → Next
        _click_first(page, [
            'text=Next',
            '[role="button"]:has-text("Next")',
            'span:has-text("Next")',
        ], timeout=15000)
        log.info("Filter Next tıklandı.")
        page.wait_for_timeout(2000)
        _shot(page, "05_after_filter_next")

        # Caption ekranı — keyboard.type ile yaz
        caption_sel = 'div[role="textbox"], div[contenteditable="true"]'
        page.wait_for_selector(caption_sel, timeout=15000)
        page.click(caption_sel)
        page.keyboard.type(caption)
        log.info("Caption girildi.")

        # Dialog başlığına tıkla → autocomplete kapanır, Discard açılmaz
        try:
            page.click('text=Create new post', timeout=3000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        _shot(page, "06_caption_filled")

        # Share — önce JS ile dene (disabled state'i de aşar)
        log.info("Share tıklanıyor...")
        clicked = _js_click_text(page, "Share")
        if not clicked:
            # JS başarısız olduysa Playwright force click
            page.click('text=Share', force=True, timeout=10000)
        log.info("Share tıklandı, tamamlanması bekleniyor...")
        page.wait_for_timeout(7000)
        _shot(page, "07_after_share")
        log.info("Post paylaşıldı!")

        browser.close()

    return "posted_via_playwright"
