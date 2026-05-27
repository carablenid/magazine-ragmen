"""HTML logosunu 500x500 PNG'ye çevirir → assets/logo.png"""
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML_PATH = Path(r"c:\Users\tumer\Downloads\Magazine Ra_men PP.html").resolve()
OUT_PATH = Path("assets/logo.png")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 600, "height": 600})
    page.goto(f"file:///{HTML_PATH.as_posix()}")
    page.wait_for_timeout(2000)  # Google Fonts yüklensin

    element = page.locator(".pp")
    element.screenshot(path=str(OUT_PATH))
    browser.close()

from PIL import Image, ImageDraw
img = Image.open(str(OUT_PATH)).convert("RGBA")
w, h = img.size
mask = Image.new("L", (w, h), 0)
ImageDraw.Draw(mask).ellipse((0, 0, w, h), fill=255)
img.putalpha(mask)
img.save(str(OUT_PATH))

print(f"Logo kaydedildi: {OUT_PATH}")
