import datetime
import os
import pygame
import config


class BaseClockScreen:
    def __init__(self):
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
        # Clock reads time each frame, no async data to fetch
        if self.sprite is None:
            self._load_sprite()

    def draw(self, surface):
        w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT

        now = datetime.datetime.now()
        today = datetime.date.today()

        # Time
        time_str = now.strftime("%-I:%M %p")
        font_time = pygame.font.SysFont("Times New Roman", 72, bold=True)
        time_surf = font_time.render(time_str, True, config.BLACK)
        time_y = 50
        surface.blit(
            time_surf,
            ((w - time_surf.get_width()) // 2, time_y),
        )

        # Day of Brady's life
        day_num = (today - config.BIRTHDAY).days + 1
        font_sub = pygame.font.SysFont("Times New Roman", 18)
        life_str = f"Day {day_num:,} of Brady's life"
        life_surf = font_sub.render(life_str, True, config.GRAY_MED)
        life_y = time_y + time_surf.get_height() + 8
        surface.blit(
            life_surf,
            ((w - life_surf.get_width()) // 2, life_y),
        )

        # Divider
        div_y = life_y + life_surf.get_height() + 12
        div_x = (w - 60) // 2
        pygame.draw.line(surface, config.DIVIDER, (div_x, div_y), (div_x + 60, div_y))

        # Day of week
        font_day = pygame.font.SysFont("Times New Roman", 22)
        dow_str = today.strftime("%A")
        dow_surf = font_day.render(dow_str, True, config.GRAY_DARK)
        dow_y = div_y + 12
        surface.blit(
            dow_surf,
            ((w - dow_surf.get_width()) // 2, dow_y),
        )

        # Full date
        date_str = today.strftime("%B %-d, %Y")
        date_surf = font_sub.render(date_str, True, config.GRAY_MED)
        date_y = dow_y + dow_surf.get_height() + 4
        surface.blit(
            date_surf,
            ((w - date_surf.get_width()) // 2, date_y),
        )

        # Sprite
        self._draw_sprite(surface)

    def _draw_sprite(self, surface):
        x = 24
        y = config.SCREEN_HEIGHT - 36 - config.SPRITE_SIZE
        if self.sprite:
            surface.blit(self.sprite, (x, y))
        else:
            _draw_placeholder(surface, x, y)


def _draw_placeholder(surface, x, y):
    s = config.SPRITE_SIZE
    rect = pygame.Rect(x, y, s, s)
    pygame.draw.rect(surface, config.PLACEHOLDER_BG, rect)
    # Dashed border
    dash_len = 4
    gap = 3
    color = config.GRAY_HINT
    for side in [
        ((x, y), (x + s, y)),            # top
        ((x, y + s), (x + s, y + s)),    # bottom
        ((x, y), (x, y + s)),            # left
        ((x + s, y), (x + s, y + s)),    # right
    ]:
        _draw_dashed_line(surface, color, side[0], side[1], dash_len, gap)


def _draw_dashed_line(surface, color, start, end, dash, gap):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(abs(dx), abs(dy))
    if length == 0:
        return
    step = dash + gap
    for i in range(0, length, step):
        frac_start = i / length
        frac_end = min((i + dash) / length, 1.0)
        sx = start[0] + dx * frac_start
        sy = start[1] + dy * frac_start
        ex = start[0] + dx * frac_end
        ey = start[1] + dy * frac_end
        pygame.draw.line(surface, color, (int(sx), int(sy)), (int(ex), int(ey)))
