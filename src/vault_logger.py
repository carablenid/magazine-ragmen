"""
Her başarılı post sonrası kaynak bilgisini iki yere yazar:
  1. data/post_log.md  — repo'ya commit edilir (GitHub Actions dahil her ortamda)
  2. Obsidian vault (KAYNAKLAR.md) — sadece yerelde path varsa
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

REPO_LOG = Path("data/post_log.md")
OBSIDIAN_LOG = Path(r"C:\Users\tumer\Documents\Obsidian\InstaProject\KAYNAKLAR.md")

_HEADER = "# Post Kaynakları — Magazine Rağmen\n\n"


def _append(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(_HEADER, encoding="utf-8")
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)


def log_post(item: dict, post_number: int | None = None) -> None:
    posted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    num = f"#{post_number} " if post_number else ""
    line = (
        f"## {num}{posted_at} — {item['artist']}\n"
        f"**Başlık:** {item['title']}\n"
        f"**Kaynak:** {item.get('source_url', 'bilinmiyor')}\n\n"
    )
    try:
        _append(REPO_LOG, line)
        log.info("Kaynak repo log'una yazıldı.")
    except Exception as e:
        log.warning("Repo log yazılamadı: %s", e)

    if OBSIDIAN_LOG.parent.exists():
        try:
            _append(OBSIDIAN_LOG, line)
            log.info("Kaynak Obsidian vault'a yazıldı.")
        except Exception as e:
            log.warning("Obsidian vault yazılamadı: %s", e)
