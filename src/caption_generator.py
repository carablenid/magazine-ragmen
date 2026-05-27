import os
import anthropic

from config import CAPTION_MAX_CHARS, HASHTAGS

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = (
    "Sen 'Magazine Rağmen' adlı Türkiye rap sahnesinin magazin Instagram sayfasının "
    "editörüsün. Kısa, enerjik, sokak diline yakın Türkçe captions yazıyorsun. "
    "Abartılı veya sahte coşku yok — doğal, direkt bir ses tonu. "
    "Emoji kullanabilirsin ama aşırıya kaçma. "
    "Hashtag EKLEME — onlar ayrıca eklenecek."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    return _client


def generate_caption(item: dict) -> str:
    client = _get_client()

    prompt = (
        f"Sanatçı: {item['artist']}\n"
        f"Başlık: {item['title']}\n"
        f"Özet: {item.get('summary', '')[:300]}\n\n"
        f"Bu haber için Instagram caption yaz. "
        f"Maksimum {CAPTION_MAX_CHARS} karakter, Türkçe."
    )

    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    caption = resp.content[0].text.strip()

    # hashtag'leri ekle
    tags = " ".join(HASHTAGS[:5])
    artist_tag = "#" + item["artist"].lower().replace(" ", "").replace("ş", "s").replace("ı", "i")
    return f"{caption}\n\n{artist_tag} {tags}"
