import os
import pygame
import config
from services import calendar_data

# Category color mapping
CATEGORY_COLORS = {
    "default": (config.LAVENDER, config.LAVENDER_PASTEL),
    "food": (config.ORANGE, config.ORANGE_PASTEL),
    "exercise": (config.CORAL, config.CORAL_PASTEL),
}


class CalendarScreen:
    def __init__(self):
        self.events = None
        self.sprite = None
        self._load_sprite()

    def _load_sprite(self):
        path = os.path.join(config.SPRITE_DIR, config.SPRITE_DEFAULT)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            self.sprite = pygame.transform.scale(
                img, (config.SPRITE_SIZE, config.SPRITE_SIZE)
            )

    def update(self):
        self.events = calendar_data.get_todays_events()
        if self.sprite is None:
            self._load_sprite()

    def draw(self, surface):
        if self.events is None:
            self.events = calendar_data.get_todays_events()

        w = config.SCREEN_WIDTH
        pad_l = 24
        pad_r = 24

        # Header
        font_header = pygame.font.SysFont("Times New Roman", 20, bold=True)
        header = font_header.render("Today's schedule", True, config.LAVENDER)
        surface.blit(header, (pad_l, 18))

        # Event cards
        card_y = 52
        card_h = 44
        card_gap = 8
        card_w = w - pad_l - pad_r

        font_time = pygame.font.SysFont("Times New Roman", 16)
        font_title = pygame.font.SysFont("Times New Roman", 17)

        for event in self.events:
            cat = event.get("category", "default")
            border_color, bg_color = CATEGORY_COLORS.get(
                cat, CATEGORY_COLORS["default"]
            )

            # Card background
            pygame.draw.rect(
                surface, bg_color,
                (pad_l, card_y, card_w, card_h),
            )
            # Left border
            pygame.draw.rect(
                surface, border_color,
                (pad_l, card_y, 3, card_h),
            )

            # Time
            time_surf = font_time.render(event["time"], True, config.GRAY_MED)
            surface.blit(time_surf, (pad_l + 12, card_y + 12))

            # Title
            title_surf = font_title.render(event["title"], True, config.BLACK)
            surface.blit(title_surf, (pad_l + 90, card_y + 12))

            card_y += card_h + card_gap

            # Stop if we'd overflow the screen
            if card_y + card_h > config.SCREEN_HEIGHT - 50:
                break

        # Sprite (bottom-left)
        self._draw_sprite(surface)

    def _draw_sprite(self, surface):
        x = 24
        y = config.SCREEN_HEIGHT - 36 - config.SPRITE_SIZE
        if self.sprite:
            surface.blit(self.sprite, (x, y))
        else:
            from screens.base_clock import _draw_placeholder
            _draw_placeholder(surface, x, y)
