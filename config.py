ARTISTS = [
    "Blok3", "Ati242", "Motive", "Uzi",
    "Şehinşah", "Ezhel", "Joker", "Deathbycamp",
    # Genişletilmiş liste
    "Ceza", "Ben Fero", "Norm Ender", "Yener Çevik",
    "Anıl Piyancı", "Hidra", "Massaka", "Heijan",
    "Şanışer", "Murda", "Allame", "Defkhan",
]

# YouTube kanal ID'leri — zamanla doldur
YOUTUBE_CHANNELS: dict[str, str] = {
    # "UCxxxxxxxxxxxxxxxx": "Blok3",
}

# Sanatçı fotoğrafı için özel arama terimleri — Türk rapper bağlamı şart
ARTIST_PHOTO_TERMS = {
    "Blok3":        "Blok3 türk rapper sahne",
    "Ati242":       "Ati242 türk rapper",
    "Motive":       "Motive türkçe rap müzisyen",
    "Uzi":          "Uzi türkçe rap sanatçısı türkiye",
    "Şehinşah":     "Şehinşah türk rapper müzisyen",
    "Ezhel":        "Ezhel türk rapper",
    "Joker":        "Joker türkçe rap",
    "Deathbycamp":  "Deathbycamp türk rapper",
    "Ceza":         "Ceza türk rapper müzisyen",
    "Ben Fero":     "Ben Fero türkçe rap",
    "Norm Ender":   "Norm Ender rapper",
    "Yener Çevik":  "Yener Çevik türkçe rap",
    "Anıl Piyancı": "Anıl Piyancı türk müzisyen",
    "Hidra":        "Hidra türkçe rap sanatçısı",
    "Massaka":      "Massaka türkçe rap",
    "Heijan":       "Heijan türk rapper",
    "Şanışer":      "Şanışer türkçe rap",
    "Murda":        "Murda türk rapper müzisyen",
    "Allame":       "Allame türkçe rap",
    "Defkhan":      "Defkhan türkçe rap",
}

# Her sanatçı için Google News arama eki — belirsiz isimler için spesifik yaz
ARTIST_SEARCH_TERMS = {
    "Blok3":        "Blok3 rap",
    "Ati242":       "Ati242",
    "Motive":       "Motive rap Türkiye",
    "Uzi":          "Uzi müzik",
    "Şehinşah":     "Şehinşah",
    "Ezhel":        "Ezhel",
    "Joker":        "Joker Türkçe rap",
    "Deathbycamp":  "Deathbycamp",
    "Ceza":         "Ceza rapper",
    "Ben Fero":     "Ben Fero",
    "Norm Ender":   "Norm Ender",
    "Yener Çevik":  "Yener Çevik",
    "Anıl Piyancı": "Anıl Piyancı",
    "Hidra":        "Hidra rap",
    "Massaka":      "Massaka rap",
    "Heijan":       "Heijan",
    "Şanışer":      "Şanışer",
    "Murda":        "Murda rapper",
    "Allame":       "Allame",
    "Defkhan":      "Defkhan",
}

# Post saatleri UTC (TR = UTC+3)
# 09:30 TR → 06:30 UTC, 13:00 TR → 10:00 UTC, 19:00 TR → 16:00 UTC
POST_SCHEDULE_UTC = [
    {"hour": 6, "minute": 30},
    {"hour": 10, "minute": 0},
    {"hour": 16, "minute": 0},
]

POSTS_PER_DAY = 3
MAX_NEWS_AGE_HOURS = 336  # 14 gün
QUEUE_MAX_AGE_DAYS = 7
PER_ARTIST_QUEUE_LIMIT = 2

IMAGE_SIZE = (1080, 1080)
FONT_PATH = "assets/fonts/Montserrat-Bold.ttf"
FONT_PATH_REGULAR = "assets/fonts/Montserrat-Regular.ttf"
LOGO_PATH = "assets/logo.png"

CAPTION_MAX_CHARS = 200
HASHTAGS = [
    "#türkçerap", "#rap", "#türkiyemüzik", "#magazineragmen",
    "#hiphop", "#müzik", "#yenimüzik"
]
