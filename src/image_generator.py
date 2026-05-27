import io
import logging
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config import IMAGE_SIZE, FONT_PATH, FONT_PATH_REGULAR, LOGO_PATH
from src.photo_finder import find_artist_photo

log = logging.getLogger(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MagazineRagmenBot/1.0)"}

W, H = IMAGE_SIZE
GRADIENT_START_Y = int(H * 0.45)  # gradyan bu Y'den başlar


def _download_image(url: str) -> Image.Image | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        return img
    except Exception as e:
        log.warning("Görsel indirilemedi (%s): %s", url, e)
        return None


def _fallback_background(artist: str) -> Image.Image:
    img = Image.new("RGBA", IMAGE_SIZE, (15, 15, 20, 255))
    draw = ImageDraw.Draw(img)
    # Subtle grid pattern
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(30, 30, 40, 255), width=1)
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(30, 30, 40, 255), width=1)
    return img


def _crop_to_square(img: Image.Image) -> Image.Image:
    iw, ih = img.size
    side = min(iw, ih)
    left = (iw - side) // 2
    top = (ih - side) // 2
    img = img.crop((left, top, left + side, top + side))
    return img.resize(IMAGE_SIZE, Image.LANCZOS)


def _add_gradient(img: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    gradient_h = H - GRADIENT_START_Y
    for y in range(gradient_h):
        alpha = int(220 * (y / gradient_h) ** 1.4)
        draw.rectangle(
            [(0, GRADIENT_START_Y + y), (W, GRADIENT_START_Y + y + 1)],
            fill=(0, 0, 0, alpha),
        )
    return Image.alpha_composite(img, overlay)


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    path = FONT_PATH if bold else FONT_PATH_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        log.warning("Font bulunamadı, varsayılan kullanılıyor.")
        return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _add_logo(img: Image.Image) -> Image.Image:
    logo_path = Path(LOGO_PATH)
    if not logo_path.exists():
        return img
    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = 120
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        padding = 28
        pos = (W - logo_size - padding, padding)
        img.paste(logo, pos, logo)
    except Exception as e:
        log.warning("Logo eklenemedi: %s", e)
    return img


def create_post_image(item: dict) -> Image.Image:
    # 1. Arka plan görseli — önce DuckDuckGo'dan sanatçı fotoğrafı, yoksa fallback
    bg = find_artist_photo(item["artist"])
    if bg is None and item.get("image_url"):
        bg = _download_image(item["image_url"])
        if bg is not None:
            bg = _crop_to_square(bg)
    if bg is None:
        bg = _fallback_background(item["artist"])

    # RGBA'ya çevir
    bg = bg.convert("RGBA")

    # 2. Gradyan overlay
    canvas = _add_gradient(bg)

    # 3. Metin
    draw = ImageDraw.Draw(canvas)
    padding = 48

    # Sanatçı adı (üst-sol, küçük)
    artist_font = _load_font(36, bold=False)
    artist_text = item["artist"].upper()
    draw.text(
        (padding, H - 220),
        artist_text,
        font=artist_font,
        fill=(200, 200, 200, 255),
    )

    # Başlık (ana metin)
    title_font = _load_font(52, bold=True)
    max_w = W - padding * 2
    lines = _wrap_text(item["title"], title_font, max_w)
    lines = lines[:3]  # max 3 satır
    y = H - 180
    for line in lines:
        draw.text((padding, y), line, font=title_font, fill=(255, 255, 255, 255))
        bbox = draw.textbbox((0, 0), line, font=title_font)
        y += (bbox[3] - bbox[1]) + 8

    # 4. Logo
    canvas = _add_logo(canvas)

    return canvas.convert("RGB")


def save_image(img: Image.Image, path: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "JPEG", quality=92, optimize=True)
    return path
