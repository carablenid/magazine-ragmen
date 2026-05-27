"""
Yerel makinede bir kez çalıştır.
Gerçek Chrome açılır → Instagram'a giriş yap → session kaydedilir.

    python create_session.py
"""
import json
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("playwright_session.json")

print("Chrome açılıyor — @magazineragmen olarak giriş yap.")
print("2FA / güvenlik kodu varsa tamamla.\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, channel="chrome")
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto("https://www.instagram.com/accounts/login/")

    input("✅ Instagram ana sayfasına geçince ENTER'a bas...")

    if "login" in page.url:
        print("❌ Hâlâ login sayfasındasın. Giriş tamamlanmadı.")
        browser.close()
        exit(1)

    ctx.storage_state(path=str(OUT))
    browser.close()

b64 = base64.b64encode(OUT.read_bytes()).decode()
Path("session_b64.txt").write_text(b64, encoding="utf-8")

print(f"✅ Session kaydedildi → {OUT}")
print("Base64 çıktısı → session_b64.txt")
print(f"\nİlk 80 karakter: {b64[:80]}...")
