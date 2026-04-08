import os
import pygame
import config
from services import history_api


class HistoryScreen:
    def __init__(self):
        self.data = None
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
        self.data = history_api.fetch_history()
        if self.sprite is None:
            self._load_sprite()

    def draw(self, surface):
        if self.data is None:
            self.data = history_api.fetch_history()

        w = config.SCREEN_WIDTH
        d = self.data
        pad_l = 24
        pad_r = 24

        # Header
        font_header = pygame.font.SysFont("Times New Roman", 18)
        header = font_header.render("On this day in history", True, config.SAGE)
        surface.blit(header, (pad_l, 18))

        # Offline indicator
        if d.get("offline"):
            font_sm = pygame.font.SysFont("Times New Roman", 12)
            off = font_sm.render("offline", True, config.GRAY_LIGHT)
            surface.blit(off, (w - pad_r - off.get_width(), 22))

        # Date
        font_date = pygame.font.SysFont("Times New Roman", 26, bold=True)
        date_surf = font_date.render(d["date_label"], True, config.BLACK)
        surface.blit(date_surf, (pad_l, 44))

        # Event cards
        events = d.get("events", [])
        card_y = 82
        card_h = 52
        card_gap = 8
        card_w = w - pad_l - pad_r

        font_year = pygame.font.SysFont("Times New Roman", 15, bold=True)
        font_text = pygame.font.SysFont("Times New Roman", 14)

        for event in events[:3]:
            # Card background
            pygame.draw.rect(
                surface, config.SAGE_PASTEL,
                (pad_l, card_y, card_w, card_h),
            )
            # Left border
            pygame.draw.rect(
                surface, config.SAGE,
                (pad_l, card_y, 3, card_h),
            )

            # Year and text
            year_str = event["year"]
            text_str = event["text"]
            year_surf = font_year.render(f"{year_str} \u2014 ", True, config.SAGE)
            surface.blit(year_surf, (pad_l + 10, card_y + 6))

            # Wrap text to fit
            max_text_w = card_w - 20
            line = f"{year_str} \u2014 {text_str}"
            _draw_wrapped_text(
                surface, font_text, line, pad_l + 10, card_y + 6,
                max_text_w, card_h - 10, config.SAGE, (51, 51, 51)
            )

            card_y += card_h + card_gap

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


def _draw_wrapped_text(surface, font, text, x, y, max_w, max_h, year_color, text_color):
    """Render text with year in accent color and rest in dark gray, wrapping lines."""
    # Split at the dash to color year differently
    parts = text.split(" \u2014 ", 1)
    if len(parts) == 2:
        year_part = parts[0] + " \u2014 "
        desc_part = parts[1]
    else:
        year_part = ""
        desc_part = text

    # Render year portion
    year_surf = font.render(year_part, True, year_color)
    surface.blit(year_surf, (x, y))
    year_w = year_surf.get_width()

    # Render description, wrapping if needed
    words = desc_part.split()
    line = ""
    cur_x = x + year_w
    cur_y = y
    line_h = font.get_linesize()

    for word in words:
        test = line + word + " "
        test_surf = font.render(test, True, text_color)
        if cur_x + test_surf.get_width() > x + max_w:
            if line:
                line_surf = font.render(line, True, text_color)
                surface.blit(line_surf, (cur_x, cur_y))
            cur_y += line_h
            cur_x = x
            line = word + " "
            if cur_y - y + line_h > max_h:
                return
        else:
            line = test

    if line:
        line_surf = font.render(line.rstrip(), True, text_color)
        surface.blit(line_surf, (cur_x, cur_y))
