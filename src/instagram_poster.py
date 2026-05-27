import os
import base64
import logging
import tempfile
from pathlib import Path

log = logging.getLogger(__name__)

SESSION_FILE = Path("playwright_session.json")


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


def _click_first(page, selectors: list[str], timeout: int = 8000):
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=timeout)
            page.click(sel, timeout=timeout)
            return sel
        except Exception:
            continue
    raise RuntimeError(f"Hiçbir selector bulunamadı: {selectors}")


def _mouse_click_text_in_dialog(page, text: str) -> bool:
    """Dialog içinde text ile eşleşen elementin koordinatına gerçek mouse click gönderir."""
    coords = page.evaluate(f"""
        () => {{
            const dialog = document.querySelector('div[role="dialog"]');
            if (!dialog) return null;
            const all = dialog.querySelectorAll('*');
            for (const el of all) {{
                if (el.textContent.trim() === '{text}' && el.offsetParent !== null) {{
                    const r = el.getBoundingClientRect();
                    return {{x: r.left + r.width / 2, y: r.top + r.height / 2}};
                }}
            }}
            return null;
        }}
    """)
    if coords:
        page.mouse.click(coords["x"], coords["y"])
        return True
    return False


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

        if "accounts/login" in page.url:
            browser.close()
            raise RuntimeError("Instagram session geçersiz. create_session.py ile yenile.")

        log.info("Mevcut URL: %s | Yeni post başlatılıyor...", page.url)

        # Create butonu
        _click_first(page, [
            'a[href="/create/select/"]',
            '[aria-label="New post"]',
            'svg[aria-label="New post"]',
        ], timeout=10000)
        page.wait_for_timeout(2000)

        # Dosya seçici
        with page.expect_file_chooser(timeout=15000) as fc_info:
            _click_first(page, [
                'button:has-text("Select from computer")',
                '[role="button"]:has-text("Select from computer")',
            ], timeout=10000)
        fc_info.value.set_files(abs_path)
        log.info("Görsel yüklendi.")
        page.wait_for_timeout(4000)

        # Crop ekranı → Next
        _click_first(page, [
            'text=Next',
            '[role="button"]:has-text("Next")',
            'span:has-text("Next")',
        ], timeout=15000)
        log.info("Crop Next tıklandı.")
        page.wait_for_timeout(2000)

        # Filter ekranı → Next
        _click_first(page, [
            'text=Next',
            '[role="button"]:has-text("Next")',
            'span:has-text("Next")',
        ], timeout=15000)
        log.info("Filter Next tıklandı.")
        page.wait_for_timeout(2000)

        # Caption ekranı — keyboard.type ile yaz (fill() React eventlarını tetiklemiyor)
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

        # Share — dialog içinde elementin koordinatına gerçek mouse click
        log.info("Share tıklanıyor...")
        clicked = _mouse_click_text_in_dialog(page, "Share")
        if not clicked:
            page.locator('div[role="dialog"]').get_by_text("Share", exact=True).click(force=True, timeout=10000)
        log.info("Share tıklandı, tamamlanması bekleniyor...")
        page.wait_for_timeout(7000)
        log.info("Post paylaşıldı!")

        browser.close()

    return "posted_via_playwright"
