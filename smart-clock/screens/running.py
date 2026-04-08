import os
import pygame
import config
from services import smashrun_data


class RunningScreen:
    def __init__(self):
        self.data = None
        self.sprite = None
        self._load_sprite()

    def _load_sprite(self):
        # Prefer running sprite, fall back to default
        for name in (config.SPRITE_RUNNING, config.SPRITE_DEFAULT):
            path = os.path.join(config.SPRITE_DIR, name)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.sprite = pygame.transform.scale(
                    img, (config.SPRITE_SIZE, config.SPRITE_SIZE)
                )
                return
        self.sprite = None

    def update(self):
        self.data = smashrun_data.get_weekly_data()
        if self.sprite is None:
            self._load_sprite()

    def draw(self, surface):
        if self.data is None:
            self.data = smashrun_data.get_weekly_data()

        w = config.SCREEN_WIDTH
        d = self.data
        pad_l = 24
        pad_r = 24

        # Header
        font_header = pygame.font.SysFont("Times New Roman", 20, bold=True)
        header = font_header.render("This week's running", True, config.CORAL)
        surface.blit(header, (pad_l, 18))

        # Stats boxes
        stats = [
            (str(d["total_miles"]), "miles"),
            (str(d["num_runs"]), "runs"),
            (d["avg_pace"], "avg pace"),
        ]
        box_y = 52
        box_h = 60
        box_w = (w - pad_l - pad_r - 16) // 3
        font_big = pygame.font.SysFont("Times New Roman", 28, bold=True)
        font_label = pygame.font.SysFont("Times New Roman", 14)

        for i, (value, label) in enumerate(stats):
            bx = pad_l + i * (box_w + 8)
            # Box bg
            pygame.draw.rect(
                surface, config.CORAL_PASTEL,
                (bx, box_y, box_w, box_h),
            )
            # Box border
            pygame.draw.rect(
                surface, config.CORAL_BORDER,
                (bx, box_y, box_w, box_h), 1,
            )
            # Value
            val_surf = font_big.render(value, True, config.BLACK)
            surface.blit(
                val_surf,
                (bx + (box_w - val_surf.get_width()) // 2, box_y + 8),
            )
            # Label
            lbl_surf = font_label.render(label, True, config.GRAY_MED)
            surface.blit(
                lbl_surf,
                (bx + (box_w - lbl_surf.get_width()) // 2, box_y + 40),
            )

        # Bar chart
        daily = d.get("daily", [0] * 7)
        days = ["M", "T", "W", "T", "F", "S", "S"]
        chart_y = 132
        chart_h = 100
        bar_area_w = w - pad_l - pad_r
        col_w = bar_area_w // 7
        max_miles = max(daily) if max(daily) > 0 else 1

        font_day = pygame.font.SysFont("Times New Roman", 13)

        # "Daily breakdown" label
        font_sub = pygame.font.SysFont("Times New Roman", 14)
        sub_surf = font_sub.render("Daily breakdown", True, config.GRAY_MED)
        surface.blit(sub_surf, (pad_l, chart_y - 16))

        bar_bottom = chart_y + chart_h - 20

        for i, miles in enumerate(daily):
            cx = pad_l + i * col_w + col_w // 2
            bar_w = col_w - 16

            if miles > 0:
                bar_h = max(6, int((miles / max_miles) * (chart_h - 30)))
                bar_y = bar_bottom - bar_h
                pygame.draw.rect(
                    surface, config.CORAL_LIGHT,
                    (cx - bar_w // 2, bar_y, bar_w, bar_h),
                )
            else:
                # Thin line for no-run days
                pygame.draw.line(
                    surface, config.DIVIDER,
                    (cx - bar_w // 2, bar_bottom - 1),
                    (cx + bar_w // 2, bar_bottom - 1),
                    2,
                )

            # Day label
            day_surf = font_day.render(days[i], True, config.GRAY_DARK)
            surface.blit(
                day_surf,
                (cx - day_surf.get_width() // 2, bar_bottom + 4),
            )

        # Sprite (bottom-right)
        self._draw_sprite(surface)

    def _draw_sprite(self, surface):
        x = config.SCREEN_WIDTH - 24 - config.SPRITE_SIZE
        y = config.SCREEN_HEIGHT - 36 - config.SPRITE_SIZE
        if self.sprite:
            surface.blit(self.sprite, (x, y))
        else:
            from screens.base_clock import _draw_placeholder
            _draw_placeholder(surface, x, y)
