#!/usr/bin/env python3
"""BradyCLOCK — Raspberry Pi smart desk clock."""

import os
import select as select_mod
import sys
import time

import numpy as np

# Detect Pi: /dev/fb1 exists
IS_PI = os.path.exists("/dev/fb1")

if IS_PI:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import config
from screens.base_clock import BaseClockScreen
from screens.weather import WeatherScreen
from screens.history import HistoryScreen
from screens.running import RunningScreen
from screens.calendar_view import CalendarScreen


def push_to_fb(surface, fb):
    """Convert a pygame surface to RGB565 and write it to the framebuffer."""
    pixels = pygame.image.tostring(surface, "RGB")
    arr = np.frombuffer(pixels, dtype=np.uint8).reshape(-1, 3)
    r = arr[:, 0].astype(np.uint16)
    g = arr[:, 1].astype(np.uint16)
    b = arr[:, 2].astype(np.uint16)
    rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    fb.seek(0)
    fb.write(rgb565.astype("<u2").tobytes())


def find_touchscreen():
    """Find the touchscreen evdev device on the Pi."""
    try:
        from evdev import InputDevice, ecodes, list_devices
    except ImportError:
        return None

    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities()
        if ecodes.EV_ABS in caps:
            name = dev.name.lower()
            if "touch" in name or "ads7846" in name or "tsc" in name:
                return dev
    # Fallback: return first device with ABS capability
    for path in list_devices():
        dev = InputDevice(path)
        caps = dev.capabilities()
        if ecodes.EV_ABS in caps:
            return dev
    return None


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
    touch_dev = None
    touch_x = None      # X position at finger down
    touch_x_last = None  # Most recent X position

    if IS_PI:
        from evdev import ecodes

        print(f"Pi mode: SDL_VIDEODRIVER={os.environ.get('SDL_VIDEODRIVER')}")
        pygame.display.set_mode((1, 1))
        screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        print(f"Surface created: {screen.get_size()}")
        fb = open("/dev/fb1", "wb", buffering=0)
        # Push a white frame immediately to confirm fb1 works
        screen.fill((255, 255, 255))
        push_to_fb(screen, fb)
        print("Framebuffer: wrote initial white frame to /dev/fb1")
        pygame.mouse.set_visible(False)
        touch_dev = find_touchscreen()
        if touch_dev:
            print(f"Touchscreen found: {touch_dev.name} ({touch_dev.path})")
        else:
            print("Warning: No touchscreen device found")
    else:
        screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
        )
        pygame.display.set_caption("BradyCLOCK")

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
            # Pygame events (keyboard on desktop, quit)
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

            # Evdev touch events (Pi only)
            if touch_dev:
                r, _, _ = select_mod.select([touch_dev], [], [], 0)
                if r:
                    for event in touch_dev.read():
                        if event.type == ecodes.EV_ABS and event.code == ecodes.ABS_X:
                            touch_x_last = event.value
                            if touch_x is None:
                                touch_x = event.value
                        elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                            if event.value == 1:
                                # Finger down
                                touch_x = None
                            elif event.value == 0 and touch_x is not None and touch_x_last is not None:
                                # Finger up — check swipe
                                delta = touch_x - touch_x_last
                                if abs(delta) > config.SWIPE_THRESHOLD:
                                    if delta > 0:
                                        current_screen = (current_screen + 1) % config.NUM_SCREENS
                                    else:
                                        current_screen = (current_screen - 1) % config.NUM_SCREENS
                                touch_x = None

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

            draw_nav_dots(screen, current_screen, config.NUM_SCREENS)
            draw_swipe_hint(screen)

            if fb:
                try:
                    push_to_fb(screen, fb)
                except Exception as e:
                    print(f"Framebuffer write error: {e}")
            else:
                pygame.display.flip()

            clock.tick(config.FPS)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if fb:
            fb.close()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
