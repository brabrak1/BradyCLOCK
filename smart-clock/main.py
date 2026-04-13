#!/usr/bin/env python3
"""BradyCLOCK — Raspberry Pi smart desk clock."""

import os
import struct
import sys
import time
import subprocess

# Detect Pi: /dev/fb0 exists
# IS_PI = os.path.exists("/dev/fb1")

FB_DEV = None
if os.path.exists("/dev/fb1"):
    FB_DEV = "/dev/fb1"
elif os.path.exists("/dev/fb0"):
    FB_DEV = "/dev/fb0"

IS_PI = FB_DEV is not None

if IS_PI:
    from evdev import InputDevice, ecodes
    def find_touch_device():
        """Find the ADS7846 touchscreen input device."""
        import glob
        for path in sorted(glob.glob("/dev/input/event*")):
            dev = InputDevice(path)
            if "ADS7846" in dev.name:
                return dev
        return None
    # Set these BEFORE pygame.init()
    os.environ["SDL_VIDEODRIVER"] = "dummy" 
    os.environ["SDL_FBDEV"] = FB_DEV
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-" + str(os.getuid())
    os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)

import pygame
import config
from screens.base_clock import BaseClockScreen
from screens.weather import WeatherScreen
from screens.history import HistoryScreen
from screens.running import RunningScreen
from screens.calendar_view import CalendarScreen

def get_ip():
    try:
        result = subprocess.check_output(["hostname", "-I"]).decode().strip().split()[0]
        return result
    except Exception:
        return "No network"

def push_to_fb(surface, fb):
    """Convert a pygame surface to RGB565 and write it to the framebuffer."""
    pixels = pygame.image.tostring(surface, "RGB")
    rgb565 = bytearray(config.SCREEN_WIDTH * config.SCREEN_HEIGHT * 2)
    idx = 0
    for i in range(0, len(pixels), 3):
        r = pixels[i]
        g = pixels[i + 1]
        b = pixels[i + 2]
        rgb565[idx] = ((g & 0x1C) << 3) | (b >> 3)
        rgb565[idx + 1] = (r & 0xF8) | (g >> 5)
        idx += 2
    fb.seek(0)
    fb.write(rgb565)


def draw_nav_dots(surface, current, total):
    """Draw page indicator dots at bottom center."""
    dot_size = 6
    dot_gap = 8
    total_w = total * dot_size + (total - 1) * dot_gap
    start_x = (config.SCREEN_WIDTH - total_w) // 2
    y = config.SCREEN_HEIGHT - 18

    for i in range(total):
        x = start_x + i * (dot_size + dot_gap)
        color = config.DOT_ACTIVE if i == current else config.DOT_INACTIVE
        pygame.draw.rect(surface, color, (x, y, dot_size, dot_size))


def draw_swipe_hint(surface):
    """Draw 'swipe →' hint in bottom-right corner."""
    font = pygame.font.SysFont("Times New Roman", 12)
    hint = font.render("swipe \u2192", True, config.GRAY_LIGHT)
    surface.blit(
        hint,
        (config.SCREEN_WIDTH - 24 - hint.get_width(), config.SCREEN_HEIGHT - 16),
    )


def main():
    pygame.init()

    fb = None
    if IS_PI:
        # Dummy driver requires a display mode to be set for fonts/events
        pygame.display.set_mode((1, 1))
        screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        fb = open(FB_DEV, "wb")
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("BradyCLOCK")
    if IS_PI:
        touch_dev = find_touch_device()
        if touch_dev:
            touch_dev.grab()  # prevent events from leaking to other consumers
            abs_x = touch_dev.absinfo(ecodes.ABS_X)
            abs_y = touch_dev.absinfo(ecodes.ABS_Y)
        swipe_touch_x = None
        touch_cur_x = 0
        touch_waiting = False
    clock = pygame.time.Clock()
    screens = [
        BaseClockScreen(),
        WeatherScreen(),
        HistoryScreen(),
        RunningScreen(),
        CalendarScreen(),
    ]
    current_screen = 0
    swipe_start_x = None

    # Initial data fetch for non-clock screens
    for s in screens[1:]:
        try:
            s.update()
        except Exception:
            pass

    running = True
    last_update = 0

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_RIGHT:
                        current_screen = (current_screen + 1) % config.NUM_SCREENS
                    elif event.key == pygame.K_LEFT:
                        current_screen = (current_screen - 1) % config.NUM_SCREENS
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    swipe_start_x = event.pos[0]
                elif event.type == pygame.MOUSEBUTTONUP and swipe_start_x is not None:
                    delta = swipe_start_x - event.pos[0]
                    if delta > config.SWIPE_THRESHOLD:
                        current_screen = (current_screen + 1) % config.NUM_SCREENS
                    elif delta < -config.SWIPE_THRESHOLD:
                        current_screen = (current_screen - 1) % config.NUM_SCREENS
                    swipe_start_x = None

            # Read touch events directly from evdev (Pi only)
            if IS_PI and touch_dev:
                while True:
                    ev = touch_dev.read_one()
                    if ev is None:
                        break
                    if ev.type == ecodes.EV_ABS and ev.code == ecodes.ABS_Y:
                        touch_cur_x = config.SCREEN_WIDTH - int((ev.value - abs_y.min) / (abs_y.max - abs_y.min) * config.SCREEN_WIDTH)
                        if touch_waiting:
                            swipe_touch_x = touch_cur_x
                            touch_waiting = False
                    elif ev.type == ecodes.EV_KEY and ev.code == ecodes.BTN_TOUCH:
                        if ev.value == 1:
                            touch_waiting = True
                        elif ev.value == 0 and swipe_touch_x is not None:
                            delta = swipe_touch_x - touch_cur_x
                            if delta > config.SWIPE_THRESHOLD:
                                current_screen = (current_screen + 1) % config.NUM_SCREENS
                            elif delta < -config.SWIPE_THRESHOLD:
                                current_screen = (current_screen - 1) % config.NUM_SCREENS
                            swipe_touch_x = None

            # Periodic updates (every 30 seconds, check all screens)
            now = time.time()
            if now - last_update > 30:
                for s in screens:
                    try:
                        s.update()
                    except Exception:
                        pass
                last_update = now

            # Draw
            screen.fill(config.WHITE)
            try:
                screens[current_screen].draw(screen)
            except Exception as e:
                font = pygame.font.SysFont("Times New Roman", 16)
                err = font.render(f"Display error: {e}", True, config.GRAY_MED)
                screen.blit(err, (24, 150))

            # show IP address
            ip_font = pygame.font.SysFont("Times New Roman", 14)
            ip_text = ip_font.render(get_ip(), True, config.GRAY_MED)
            screen.blit(ip_text, (4, 4)) 

            draw_nav_dots(screen, current_screen, config.NUM_SCREENS)
            draw_swipe_hint(screen)

            if fb:
                push_to_fb(screen, fb)
            else:
                pygame.display.flip()

            clock.tick(config.FPS)
    finally:
        if fb:
            fb.close()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
