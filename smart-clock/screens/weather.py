import os
import pygame
import config
from services import weather_api


class WeatherScreen:
    def __init__(self):
        self.data = None
        self.sprite = None
        self._load_sprite()

    def _get_sprite_name(self):
        if self.data and weather_api.is_rainy(self.data.get("code", 0)):
            return config.SPRITE_UMBRELLA
        if self.data and self.data.get("code", 0) == 0:
            return config.SPRITE_SUNGLASSES
        return config.SPRITE_DEFAULT

    def _load_sprite(self):
        name = self._get_sprite_name()
        path = os.path.join(config.SPRITE_DIR, name)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            self.sprite = pygame.transform.scale(
                img, (config.SPRITE_SIZE, config.SPRITE_SIZE)
            )
        else:
            # Try default fallback
            fallback = os.path.join(config.SPRITE_DIR, config.SPRITE_DEFAULT)
            if os.path.exists(fallback):
                img = pygame.image.load(fallback).convert_alpha()
                self.sprite = pygame.transform.scale(
                    img, (config.SPRITE_SIZE, config.SPRITE_SIZE)
                )
            else:
                self.sprite = None

    def update(self):
        self.data = weather_api.fetch_weather()
        self._load_sprite()

    def draw(self, surface):
        if self.data is None:
            self.data = weather_api.fetch_weather()

        w = config.SCREEN_WIDTH
        d = self.data
        pad_l = 24
        pad_r = 24

        # Header
        font_header = pygame.font.SysFont("Times New Roman", 20, bold=True)
        header = font_header.render("Today's weather", True, config.ORANGE)
        surface.blit(header, (pad_l, 18))

        # Offline indicator
        if d.get("offline"):
            font_sm = pygame.font.SysFont("Times New Roman", 12)
            off = font_sm.render("offline", True, config.GRAY_LIGHT)
            surface.blit(off, (w - pad_r - off.get_width(), 22))

        # Temperature
        font_temp = pygame.font.SysFont("Times New Roman", 56, bold=True)
        temp_str = f'{d["temp"]}\u00b0F'
        temp_surf = font_temp.render(temp_str, True, config.BLACK)
        surface.blit(temp_surf, (pad_l, 46))

        # Condition
        code = d["code"]
        symbol = weather_api.get_condition_symbol(code)
        cond_text = weather_api.get_condition_text(code)
        accent = config.BLUE_COOL if weather_api.is_rainy(code) else config.ORANGE
        font_cond = pygame.font.SysFont("Times New Roman", 18)
        cond_surf = font_cond.render(f"{symbol} {cond_text}", True, accent)
        surface.blit(cond_surf, (pad_l, 108))

        # High/Low and wind on the right
        font_info = pygame.font.SysFont("Times New Roman", 16)
        hl_str = f'H: {d["high"]}\u00b0  L: {d["low"]}\u00b0'
        hl_surf = font_info.render(hl_str, True, config.GRAY_DARK)
        surface.blit(hl_surf, (w - pad_r - hl_surf.get_width(), 60))

        wind_str = f'Wind: {d["wind"]} mph'
        wind_surf = font_info.render(wind_str, True, config.GRAY_DARK)
        surface.blit(wind_surf, (w - pad_r - wind_surf.get_width(), 80))

        # Clothing advice box
        advice = weather_api.get_clothing_advice(d["temp"], code)
        box_y = 136
        box_h = 32
        box_w = w - pad_l - pad_r
        pygame.draw.rect(
            surface, config.ORANGE_PASTEL,
            (pad_l, box_y, box_w, box_h),
        )
        pygame.draw.rect(
            surface, config.ORANGE,
            (pad_l, box_y, 3, box_h),
        )
        font_advice = pygame.font.SysFont("Times New Roman", 14)
        advice_surf = font_advice.render(advice, True, config.ORANGE)
        surface.blit(advice_surf, (pad_l + 10, box_y + 8))

        # Hourly section
        font_label = pygame.font.SysFont("Times New Roman", 14, bold=True)
        hourly_label = font_label.render("Hourly", True, config.GRAY_DARK)
        surface.blit(hourly_label, (pad_l, 180))

        hourly = d.get("hourly", [])
        if hourly:
            col_w = (w - pad_l - pad_r) // 6
            bar_max_h = 50
            temps = [h["temp"] for h in hourly]
            t_min = min(temps) - 2
            t_max = max(temps) + 2
            t_range = max(t_max - t_min, 1)

            font_hr = pygame.font.SysFont("Times New Roman", 13)
            font_temp_sm = pygame.font.SysFont("Times New Roman", 14, bold=True)

            for i, h in enumerate(hourly):
                cx = pad_l + i * col_w + col_w // 2
                bar_top = 200

                # Hour label
                hr_surf = font_hr.render(h["hour"], True, config.GRAY_DARK)
                surface.blit(hr_surf, (cx - hr_surf.get_width() // 2, bar_top))

                # Temperature text
                t_surf = font_temp_sm.render(
                    f'{h["temp"]}\u00b0', True, config.BLACK
                )
                surface.blit(t_surf, (cx - t_surf.get_width() // 2, bar_top + 16))

                # Color bar
                bar_h = max(
                    4, int((h["temp"] - t_min) / t_range * bar_max_h)
                )
                bar_color = config.ORANGE if h["temp"] >= 65 else config.BLUE_COOL
                bar_y = bar_top + 36 + (bar_max_h - bar_h)
                bar_w = col_w - 16
                pygame.draw.rect(
                    surface, bar_color,
                    (cx - bar_w // 2, bar_y, bar_w, bar_h),
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
