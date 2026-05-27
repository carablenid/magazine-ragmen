ARTISTS = [
    "Blok3", "Ati242", "Motive", "Uzi",
    "Şehinşah", "Ezhel", "Joker", "Deathbycamp",
]

# YouTube kanal ID'leri — zamanla doldur
YOUTUBE_CHANNELS: dict[str, str] = {
    # "UCxxxxxxxxxxxxxxxx": "Blok3",
}

# Her sanatçı için Google News arama eki
ARTIST_SEARCH_TERMS = {
    "Blok3": "Blok3 rap",
    "Ati242": "Ati242",
    "Motive": "Motive rap Türkiye",
    "Uzi": "Uzi müzik",
    "Şehinşah": "Şehinşah",
    "Ezhel": "Ezhel",
    "Joker": "Joker Türkçe rap",
    "Deathbycamp": "Deathbycamp",
}

# Post saatleri UTC (TR = UTC+3)
# 09:30 TR → 06:30 UTC, 13:00 TR → 10:00 UTC, 19:00 TR → 16:00 UTC
POST_SCHEDULE_UTC = [
    {"hour": 6, "minute": 30},
    {"hour": 10, "minute": 0},
    {"hour": 16, "minute": 0},
]

POSTS_PER_DAY = 3
MAX_NEWS_AGE_HOURS = 48
QUEUE_MAX_AGE_DAYS = 7

IMAGE_SIZE = (1080, 1080)
FONT_PATH = "assets/fonts/Montserrat-Bold.ttf"
FONT_PATH_REGULAR = "assets/fonts/Montserrat-Regular.ttf"
LOGO_PATH = "assets/logo.png"

CAPTION_MAX_CHARS = 200
HASHTAGS = [
    "#türkçerap", "#rap", "#türkiyemüzik", "#magazineragmen",
    "#hiphop", "#müzik", "#yenimüzik"
]
