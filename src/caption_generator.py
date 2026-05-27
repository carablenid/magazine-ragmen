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
    "KESİNLİKLE YASAK — bunları asla yazma: "
    "1) URL, link, web adresi, YouTube, Spotify veya herhangi bir site adresi. "
    "2) TV kanalı adı, gazete adı, haber sitesi adı, yayın organı adı — hiçbir medya kuruluşuna atıfta bulunma. "
    "3) 'Kanal X'te yayınlandı', 'Y sitesine göre', 'Z haberine göre' tarzı ifadeler. "
    "Caption sadece sanatçı ve olay hakkında olacak. Başka hiçbir şeye yönlendirme yok. "
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
            f"Bu bilgiyi magazin tarzında kısa bir fun fact olarak yaz. "
            f"'Kimdir?' veya 'Biliyor muydun?' tarzı soru sorma — direkt bilgiyi ver. "
            f"Haber yazmıyorsun, sahne bilgisi paylaşıyorsun. "
            f"Maksimum {CAPTION_MAX_CHARS} karakter, Türkçe."
        )
    else:
        prompt = (
            f"Sanatçı: {item['artist']}\n"
            f"Başlık: {item['title']}\n"
            f"Özet: {item.get('summary', '')[:300]}\n\n"
            f"Bu haber için Instagram caption yaz. "
            f"'Başarılı geçti', 'güzel bir etkinlikti' gibi muğlak ifadeler kullanma. "
            f"Rakam, rekor, olay, tepki gibi spesifik detay varsa onu öne çıkar. "
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
