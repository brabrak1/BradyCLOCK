import datetime

# Personal
BIRTHDAY = datetime.date(2008, 3, 19)

# Location (for weather API)
LAT = 37.37
LON = -122.16
TIMEZONE = "America/Los_Angeles"

# Display
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 30
NUM_SCREENS = 5

# Refresh intervals (seconds)
WEATHER_REFRESH = 1800      # 30 minutes
HISTORY_REFRESH = 86400     # 24 hours
RUNNING_REFRESH = 3600      # 1 hour
CALENDAR_REFRESH = 900      # 15 minutes

# Swipe threshold (pixels)
SWIPE_THRESHOLD = 50

# Colors
WHITE = (255, 255, 255)
BLACK = (34, 34, 34)           # #222
GRAY_DARK = (85, 85, 85)      # #555
GRAY_MED = (153, 153, 153)    # #999
GRAY_LIGHT = (170, 170, 170)  # #aaa
GRAY_HINT = (204, 204, 204)   # #ccc
DIVIDER = (221, 221, 221)     # #ddd
DIVIDER_LIGHT = (238, 238, 238)  # #eee
PLACEHOLDER_BG = (240, 240, 240)  # #f0f0f0

# Dot indicators
DOT_ACTIVE = (136, 136, 136)  # #888
DOT_INACTIVE = (204, 204, 204)  # #ccc

# Weather accent
ORANGE = (224, 138, 60)        # #E08A3C
ORANGE_PASTEL = (255, 245, 235)  # #FFF5EB
BLUE_COOL = (141, 184, 204)   # #8DB8CC

# History accent
SAGE = (107, 143, 113)        # #6B8F71
SAGE_PASTEL = (242, 247, 243)  # #F2F7F3

# Running accent
CORAL = (196, 122, 106)       # #C47A6A
CORAL_LIGHT = (212, 160, 147)  # #D4A093
CORAL_PASTEL = (253, 242, 239)  # #FDF2EF
CORAL_BORDER = (232, 213, 207)  # #E8D5CF

# Calendar accent
LAVENDER = (139, 127, 181)    # #8B7FB5
LAVENDER_PASTEL = (245, 243, 250)  # #F5F3FA

# Google Calendar
CALENDAR_CREDENTIALS = "client_secret.json"
CALENDAR_TOKEN = "token.json"
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Sprite
SPRITE_SIZE = 32
SPRITE_DIR = "assets/sprites/"
SPRITE_DEFAULT = "brady_default.png"
SPRITE_RUNNING = "brady_running.png"
SPRITE_UMBRELLA = "brady_umbrella.png"
SPRITE_SUNGLASSES = "brady_sunglasses.png"
