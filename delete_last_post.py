"""
Son Instagram postunu siler.

Yerelde:    python delete_last_post.py           (playwright_session.json gerekli)
Actions:    workflow_dispatch → delete_last_post.yml
"""
import os
import base64
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = Path("playwright_session.json")


def _session_path() -> str:
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
    raise SystemExit("Session bulunamadı: playwright_session.json yok, INSTAGRAM_PLAYWRIGHT_SESSION env de yok.")


with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=not SESSION_FILE.exists(),
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    ctx = browser.new_context(
        storage_state=_session_path(),
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    page = ctx.new_page()
    page.goto("https://www.instagram.com/magazineragmen/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    page.screenshot(path="delete_debug1.png")

    if "accounts/login" in page.url:
        browser.close()
        raise SystemExit("Session geçersiz. create_session.py ile yenile.")

    # Profil sayfasındaki ilk post linki
    post_selectors = [
        'a[href*="/p/"]',
        'div[style*="flex"] a[href*="/p/"]',
        'main a[href*="/p/"]',
    ]
    clicked = False
    for sel in post_selectors:
        try:
            page.wait_for_selector(sel, timeout=10000)
            page.locator(sel).first.click()
            clicked = True
            print(f"Post'a tıklandı: {sel}")
            break
        except Exception:
            continue

    if not clicked:
        page.screenshot(path="delete_debug_fail.png")
        browser.close()
        raise SystemExit("Profil sayfasında post bulunamadı.")

    page.wait_for_timeout(3000)
    page.screenshot(path="delete_debug2.png")

    # Üç nokta menüsü
    three_dot = page.locator('svg[aria-label="More options"]')
    three_dot.wait_for(timeout=10000)
    three_dot.click()
    page.wait_for_timeout(1000)
    page.screenshot(path="delete_debug3.png")

    # Delete menü öğesi
    page.get_by_text("Delete", exact=True).click(timeout=10000)
    page.wait_for_timeout(1000)
    page.screenshot(path="delete_debug4.png")

    # Onay butonu
    page.get_by_role("button", name="Delete").click(timeout=10000)
    page.wait_for_timeout(3000)

    print("Post silindi.")
    browser.close()
