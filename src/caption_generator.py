import os
import anthropic

from config import CAPTION_MAX_CHARS, HASHTAGS

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = (
    "Sen 'Magazine Rağmen' adlı Türkiye rap sahnesinin magazin Instagram sayfasının editörüsün. "
    "Bu bir HABER sayfası DEĞİL — magazin sayfası. İkisi arasındaki fark hayati. "

    "HABER dili YASAK — şu yapılar kesinlikle yasak: "
    "'X şehrinde konser verdi', 'etkinlik gerçekleşti', 'sahneye çıktı', "
    "'coşkuyla karşılandı', 'başarılı bir gece', 'güzel vakit geçirildi'. "
    "Bunlar gazete dili — kullanırsan caption çöpe gider. "

    "MAGAZİN dili nasıl olur — şu yapıları kullan: "
    "Tepkiyi öne çıkar: 'Kocaeli bunu yıllarca konuşacak!', 'Herkes bunu bekliyordu ama böylesi...', "
    "'Sormayın, o gece neler oldu neler.' "
    "Sanatçının sözü veya anı varsa direkt merkeze al. "
    "Rakam veya rekor varsa onu vurgula: '40 bin kişi', 'ilk kez'. "

    "YAPI: İlk cümle kanca — merak, gerilim veya sürpriz. "
    "İkinci cümle detay veya tepki. Toplam maksimum 2 cümle. "

    "YASAK KELİMELER: 'camia', 'başarılı', 'güzel', 'verimli', 'coşkuyla'. "

    "KESİNLİKLE YASAK: "
    "1) URL, link, site adresi, YouTube, Spotify. "
    "2) TV kanalı, gazete, haber sitesi adı — hiçbir medya kuruluşu. "
    "3) 'Göre', 'sitesine göre', 'haberine göre' tarzı atıf. "
    "4) Pasif fiil: 'bırakıldı', 'açıklandı', 'gerçekleştirildi', 'paylaşıldı'. "
    "Caption sadece sanatçı ve olay — başka hiçbir şeye yönlendirme yok. "
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
