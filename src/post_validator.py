"""
ALTIN KURALLAR — Bu kontrolü geçemeyen item asla Instagram'a gönderilmez.

Kural eklemek: bu dosyaya yaz, main.py'ye dokunma.
"""
import re
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

MAX_AGE_HOURS = 168  # 7 gün — bunun üzerindeki içerik KESİNLİKLE yayınlanmaz

# Başlıkta geçen bu fragment'lar → RED
BLACKLISTED_TITLE_FRAGMENTS = [
    "imdb",           # IMDb (büyük/küçük harf → aşağıda case-insensitive)
    "(Film)", "(Albüm)", "(Single)",
]

# Başlıkta regex eşleşmesi → RED
BLACKLISTED_TITLE_PATTERNS = [
    r"nereli\?",            # "X Nereli?" — biyografik, magazin değil
    r"\bkimdir\?",          # "X Kimdir?"
    r"kaç yaşında",         # "kaç yaşında" — biyografik soru, magazin değil
    r"gerçek adı ne",       # "gerçek adı ne" — biyografik
    r"\(\d{4}\)\s*[-–|]",  # "Şarkı Adı (2019) - Site" — eski içerik
]

BLACKLISTED_DOMAINS = [
    "imdb.com", "imdb.tr",
    "spotify.com", "open.spotify.com",
]

CAPTION_URL_PATTERN = re.compile(
    r"https?://|www\.|\.com|\.org|\.net|youtu\.be|spotify",
    re.IGNORECASE,
)

# Caption'da asla geçmemeli
CAPTION_BANNED_WORDS = ["camia"]

# Haber ajansı pasif yapıları — magazin değil, haber dili
CAPTION_PASSIVE_WORDS = [
    "açıklandı", "belirtildi", "aktarıldı", "ifade edildi",
    "paylaşıldı", "duyuruldu", "yayınlandı", "yayımlandı",
    "gerçekleştirildi", "bırakıldı", "söylendi", "bildirildi",
    "kaydedildi", "gönderildi",
]

# Medya kuruluşu adı veya atıf kalıbı
CAPTION_MEDIA_PATTERNS = [
    r"sitesine\s+göre", r"haberine\s+göre", r"kanalına\s+göre",
    r"yayınına\s+göre", r"gazetesine\s+göre",
    r"\bntv\b", r"\bcnn\s*türk\b", r"\bhabertürk\b", r"\bshow\s*tv\b",
    r"\bfox\s*tv\b", r"\bkanal\s*d\b", r"\ba\s*haber\b", r"\btrt\b",
    r"\bhürriyet\b", r"\bmilliyet\b",
    r"\bspotify\b", r"\byoutube\b",
]
_MEDIA_RE = re.compile("|".join(CAPTION_MEDIA_PATTERNS), re.IGNORECASE)


def _age_hours(item: dict) -> float:
    try:
        ref = item.get("published_at") or item.get("scraped_at")
        dt = datetime.fromisoformat(ref)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 9999


def validate_item(item: dict) -> tuple[bool, str]:
    """Post öncesi içeriği doğrular. (False, neden) döndürürse item atlanır."""
    title = item.get("title", "").lower()
    source = item.get("source_url", "")

    # 1. Yaş kontrolü — ASLA kabul edilmez
    age = _age_hours(item)
    if age > MAX_AGE_HOURS:
        return False, f"İçerik {age:.0f}s ({age/24:.1f} gün) eski — limit {MAX_AGE_HOURS}s"

    # 2. Blacklisted title fragment (case-insensitive — title zaten lower())
    for frag in BLACKLISTED_TITLE_FRAGMENTS:
        if frag.lower() in title:
            return False, f"Redlisted başlık: '{frag}' tespit edildi"

    # 3. Blacklisted title pattern
    for pattern in BLACKLISTED_TITLE_PATTERNS:
        if re.search(pattern, title, re.IGNORECASE):
            return False, f"Redlisted başlık paterni: {pattern}"

    # 4. Blacklisted domain
    for domain in BLACKLISTED_DOMAINS:
        if domain in source:
            return False, f"Redlisted kaynak: {domain}"

    return True, "OK"


def validate_caption(caption: str) -> tuple[bool, list[str]]:
    """Caption SYSTEM_PROMPT kurallarına uyuyor mu? (False, [hatalar]) döndürür."""
    errors = []
    lower = caption.lower()

    if CAPTION_URL_PATTERN.search(caption):
        errors.append("URL/link var")

    for word in CAPTION_BANNED_WORDS:
        if word in lower:
            errors.append(f"Yasak kelime: '{word}'")

    for word in CAPTION_PASSIVE_WORDS:
        if word in lower:
            errors.append(f"Pasif yapı: '{word}'")

    m = _MEDIA_RE.search(caption)
    if m:
        errors.append(f"Medya adı/atıf: '{m.group()}'")

    if errors:
        return False, errors
    return True, []
