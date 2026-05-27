import os
import anthropic

from config import CAPTION_MAX_CHARS, HASHTAGS

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = (
    "Sen 'Magazine Rağmen' adlı Türkiye rap sahnesinin magazin Instagram sayfasının "
    "editörüsün. Kısa, sert, bilgi odaklı Türkçe captions yazıyorsun. "
    "Sahte coşku yok, aşırı samimiyet yok — soğukkanlı, mesafeli bir gazetecilik tonu. "
    "Okuyucuyla arkadaş gibi konuşma; haber ver. "
    "Emoji kullanabilirsin ama azı karar. "
    "Hashtag EKLEME — onlar ayrıca eklenecek."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    return _client


def generate_caption(item: dict) -> str:
    client = _get_client()

    if item.get("is_fun_fact"):
        prompt = (
            f"Sanatçı: {item['artist']}\n"
            f"Konu: {item['title']}\n"
            f"Özet: {item.get('summary', '')[:300]}\n\n"
            f"Bu bilgiyi 'Fun Fact:' veya 'Biliyor muydun?' formatında ilgi çekici bir "
            f"Instagram caption olarak sun. Güncel haber gibi değil, eğlenceli bir bilgi "
            f"paylaşımı olarak yaz. Maksimum {CAPTION_MAX_CHARS} karakter, Türkçe."
        )
    else:
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

    tags = " ".join(HASHTAGS[:5])
    artist_tag = "#" + item["artist"].lower().replace(" ", "").replace("ş", "s").replace("ı", "i")
    return f"{caption}\n\n{artist_tag} {tags}"
