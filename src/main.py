import logging
import os
import tempfile

from dotenv import load_dotenv

load_dotenv()

from config import POSTS_PER_DAY
from src.scraper import scrape_all
from src.caption_generator import generate_caption
from src.image_generator import create_post_image, save_image
from src.instagram_poster import post_photo
from src.queue_manager import (
    add_items, queue_size, pop_items, mark_as_posted, clean_old_items
)
from src.vault_logger import log_post
from src.scraper import _clean_title
from src.post_validator import validate_item, validate_caption

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger(__name__)

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


def run():
    log.info("=== Magazine Rağmen — çalışma başladı ===")
    clean_old_items()

    # Kuyrukta yeterli haber yoksa scrape et
    if queue_size() < POSTS_PER_DAY:
        log.info("Kuyruk dolduruluyor, scrape başlıyor...")
        fresh = scrape_all()
        added = add_items(fresh)
        log.info("%d yeni haber kuyruğa eklendi.", added)

    # Bu çalışmada 1 post at — altın kural validasyonu geçmesi şart
    items = pop_items(5)  # birden fazla çek, geçemeyen atlanacak
    if not items:
        log.warning("Yayınlanacak haber yok. Çalışma bitti.")
        return

    item = None
    for candidate in items:
        ok, reason = validate_item(candidate)
        if ok:
            item = candidate
            # Kullanılmayanları geri koy
            unused = [c for c in items if c["id"] != candidate["id"]]
            if unused:
                add_items(unused)
            break
        else:
            log.warning("ALTIN KURAL — item reddedildi: %s | Sebep: %s", candidate["title"][:60], reason)

    if item is None:
        log.warning("Kuyruktan geçen içerik yok. Çalışma bitti.")
        return

    # Mevcut kuyruktaki eski başlıklardan kaynak adını temizle
    item["title"] = _clean_title(item["title"])
    log.info("İşleniyor: %s — %s", item["artist"], item["title"])

    # Caption
    try:
        caption = generate_caption(item)
        ok, reason = validate_caption(caption)
        if not ok:
            log.warning("ALTIN KURAL — caption reddedildi: %s", reason)
            caption = f"{item['artist'].upper()} — {item['title'][:120]}\n\n#magazineragmen #türkçerap"
    except Exception as e:
        log.error("Caption üretilemedi: %s", e)
        caption = f"{item['title']}\n\n#magazineragmen #türkçerap"

    # Görsel
    try:
        img = create_post_image(item)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            img_path = save_image(img, tmp.name)
    except Exception as e:
        log.error("Görsel oluşturulamadı: %s", e)
        mark_as_posted([])
        return

    if DRY_RUN:
        log.info("[DRY RUN] Post atılmadı.")
        log.info("[DRY RUN] Caption: %s", caption)
        log.info("[DRY RUN] Görsel: %s", img_path)
        mark_as_posted([item])
        return

    # Instagram'a gönder
    try:
        post_photo(img_path, caption)
        mark_as_posted([item])
        log_post(item)
        log.info("=== Başarıyla tamamlandı. ===")
    except Exception as e:
        import traceback
        log.error("Post gönderilemedi: %s\n%s", e, traceback.format_exc())
        add_items([item])


if __name__ == "__main__":
    run()
