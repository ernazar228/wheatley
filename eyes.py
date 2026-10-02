import math
import random
import sys
import time

import pygame


pygame.init()

WINDOW_SIZE = (1000, 700)
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Wheatley Eye")

clock = pygame.time.Clock()
fullscreen = False

# Animation
auto_gaze = True
mode = "idle"

gaze_x = 0.0
gaze_y = 0.0
target_x = 0.0
target_y = 0.0

blink_amount = 0.0
blink_state = 0
next_gaze_time = 0.0
next_blink_time = 0.0


def now():
    return time.monotonic()


def toggle_fullscreen():
    global screen, fullscreen

    fullscreen = not fullscreen

    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode(WINDOW_SIZE)


def choose_gaze():
    global target_x, target_y, next_gaze_time

    target_x = random.uniform(-0.38, 0.38)
    target_y = random.uniform(-0.22, 0.22)
    next_gaze_time = now() + random.uniform(1.0, 3.0)


def set_gaze(x, y):
    global target_x, target_y

    target_x = max(-0.45, min(0.45, float(x)))
    target_y = max(-0.28, min(0.28, float(y)))


def blink_now():
    global blink_state

    if blink_state == 0:
        blink_state = 1


def schedule_blink():
    global next_blink_time
    next_blink_time = now() + random.uniform(2.5, 5.5)


def set_mode(new_mode):
    global mode
    mode = new_mode


def update_animation(dt):
    global gaze_x, gaze_y
    global blink_amount, blink_state

    t = now()

    if auto_gaze and t >= next_gaze_time:
        choose_gaze()

    # Плавное движение линзы
    smooth = min(1.0, dt * 6.5)

    gaze_x += (target_x - gaze_x) * smooth
    gaze_y += (target_y - gaze_y) * smooth

    # Автоматическое моргание
    if blink_state == 0 and t >= next_blink_time:
        blink_state = 1

    if blink_state == 1:
        blink_amount += dt * 8.5

        if blink_amount >= 1.0:
            blink_amount = 1.0
            blink_state = 2

    elif blink_state == 2:
        blink_amount -= dt * 9.5

        if blink_amount <= 0.0:
            blink_amount = 0.0
            blink_state = 0
            schedule_blink()


def radial_line(
    surface,
    center,
    angle,
    radius1,
    radius2,
    color,
    width=1,
):
    x1 = center[0] + math.cos(angle) * radius1
    y1 = center[1] + math.sin(angle) * radius1

    x2 = center[0] + math.cos(angle) * radius2
    y2 = center[1] + math.sin(angle) * radius2

    pygame.draw.line(
        surface,
        color,
        (int(x1), int(y1)),
        (int(x2), int(y2)),
        width,
    )


def draw_glow(surface, center, radius):
    # Мягкое голубое свечение вокруг линзы
    glow = pygame.Surface(
        (radius * 2 + 20, radius * 2 + 20),
        pygame.SRCALPHA,
    )

    gx = radius + 10
    gy = radius + 10

    for i in range(14, 0, -1):
        r = int(radius * i / 14)

        alpha = int(
            5 + (14 - i) * 2.2
        )

        pygame.draw.circle(
            glow,
            (30, 120, 255, alpha),
            (gx, gy),
            r,
        )

    surface.blit(
        glow,
        (center[0] - gx, center[1] - gy),
    )


def draw_eye(surface):
    width, height = surface.get_size()

    center_x = width // 2
    center_y = height // 2

    base = min(width, height)

    # Размеры механического глаза
    outer_radius = int(base * 0.33)
    metal_radius = int(base * 0.285)
    black_radius = int(base * 0.235)
    lens_radius = int(base * 0.17)

    # Тёмный фон
    surface.fill((2, 3, 5))

    # ==========================================
    # МЕТАЛЛИЧЕСКИЙ КОРПУС
    # ==========================================

    pygame.draw.circle(
        surface,
        (170, 174, 178),
        (center_x, center_y),
        outer_radius,
    )

    pygame.draw.circle(
        surface,
        (105, 109, 114),
        (center_x, center_y),
        int(outer_radius * 0.91),
    )

    pygame.draw.circle(
        surface,
        (55, 59, 64),
        (center_x, center_y),
        int(outer_radius * 0.82),
    )

    # Металлическое кольцо

    pygame.draw.circle(
        surface,
        (205, 208, 210),
        (center_x, center_y),
        metal_radius,
        max(2, base // 150),
    )

    pygame.draw.circle(
        surface,
        (45, 48, 53),
        (center_x, center_y),
        int(metal_radius * 0.91),
    )

    # ==========================================
    # РАДИАЛЬНЫЕ МЕХАНИЧЕСКИЕ ДЕТАЛИ
    # ==========================================

    for i in range(18):
        angle = (
            2 * math.pi * i / 18.0
            + math.radians(4)
        )

        radial_line(
            surface,
            (center_x, center_y),
            angle,
            int(metal_radius * 0.80),
            int(metal_radius * 0.95),
            (75, 80, 85),
            max(1, base // 280),
        )

    # ==========================================
    # БОЛТЫ / КРЕПЛЕНИЯ
    # ==========================================

    for degrees in (30, 150, 270):
        angle = math.radians(degrees)

        bolt_x = int(
            center_x
            + math.cos(angle)
            * metal_radius
            * 0.78
        )

        bolt_y = int(
            center_y
            + math.sin(angle)
            * metal_radius
            * 0.78
        )

        bolt_radius = max(
            3,
            int(base * 0.012),
        )

        pygame.draw.circle(
            surface,
            (38, 41, 45),
            (bolt_x, bolt_y),
            bolt_radius + 2,
        )

        pygame.draw.circle(
            surface,
            (120, 124, 127),
            (bolt_x, bolt_y),
            bolt_radius,
        )

    # ==========================================
    # ЧЁРНАЯ ВНУТРЕННЯЯ КАМЕРА
    # ==========================================

    pygame.draw.circle(
        surface,
        (13, 15, 18),
        (center_x, center_y),
        black_radius,
    )

    pygame.draw.circle(
        surface,
        (3, 5, 8),
        (center_x, center_y),
        int(black_radius * 0.88),
    )

    # ==========================================
    # ПОЛОЖЕНИЕ СВЕТОВОЙ ЛИНЗЫ
    # ==========================================

    lens_x = int(
        center_x
        + gaze_x * lens_radius * 0.62
    )

    lens_y = int(
        center_y
        + gaze_y * lens_radius * 0.62
    )

    lens_center = (
        lens_x,
        lens_y,
    )

    # ==========================================
    # СВЕЧЕНИЕ
    # ==========================================

    draw_glow(
        surface,
        lens_center,
        int(lens_radius * 1.35),
    )

    # ==========================================
    # ВНЕШНИЙ СИНИЙ КОНТУР ЛИНЗЫ
    # ==========================================

    pygame.draw.circle(
        surface,
        (8, 34, 76),
        lens_center,
        lens_radius + int(base * 0.015),
    )

    pygame.draw.circle(
        surface,
        (17, 70, 145),
        lens_center,
        int(lens_radius * 0.92),
    )

    # ==========================================
    # РАДИАЛЬНЫЕ ЛИНИИ ВНУТРИ ЛИНЗЫ
    # ==========================================

    for i in range(24):

        angle = (
            2 * math.pi * i / 24.0
        )

        radial_line(
            surface,
            lens_center,
            angle,
            int(lens_radius * 0.25),
            int(lens_radius * 0.88),
            (30, 120, 220),
            max(1, base // 260),
        )

    # ==========================================
    # СВЕТЯЩАЯСЯ ЦЕНТРАЛЬНАЯ ЧАСТЬ
    # ==========================================

    pygame.draw.circle(
        surface,
        (50, 155, 255),
        lens_center,
        int(lens_radius * 0.70),
    )

    pygame.draw.circle(
        surface,
        (75, 190, 255),
        lens_center,
        int(lens_radius * 0.48),
    )

    # Центр
    center_radius = int(
        lens_radius * 0.24
    )

    if mode == "surprised":
        center_radius = int(
            center_radius * 1.18
        )

    elif mode == "thinking":
        center_radius = int(
            center_radius * 0.90
        )

    pygame.draw.circle(
        surface,
        (175, 235, 255),
        lens_center,
        center_radius,
    )

    pygame.draw.circle(
        surface,
        (230, 250, 255),
        lens_center,
        max(
            2,
            int(center_radius * 0.62),
        ),
    )

    # ==========================================
    # БЛИК
    # ==========================================

    highlight_x = (
        lens_x
        - int(lens_radius * 0.24)
    )

    highlight_y = (
        lens_y
        - int(lens_radius * 0.28)
    )

    pygame.draw.circle(
        surface,
        (245, 255, 255),
        (
            highlight_x,
            highlight_y,
        ),
        max(
            2,
            int(lens_radius * 0.10),
        ),
    )

    # ==========================================
    # МЕХАНИЧЕСКИЕ ВЕКИ
    # ==========================================

    if blink_amount > 0.0:

        lid_height = int(
            base * 0.23
            * blink_amount
        )

        # Верхняя створка

        pygame.draw.rect(
            surface,
            (7, 9, 12),
            (
                center_x - outer_radius,
                center_y - outer_radius,
                outer_radius * 2,
                lid_height,
            ),
        )

        # Нижняя створка

        pygame.draw.rect(
            surface,
            (7, 9, 12),
            (
                center_x - outer_radius,
                center_y + outer_radius - lid_height,
                outer_radius * 2,
                lid_height,
            ),
        )


choose_gaze()
schedule_blink()

running = True

while running:

    dt = (
        clock.tick(60)
        / 1000.0
    )

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        elif event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                running = False

            elif event.key == pygame.K_F11:

                toggle_fullscreen()

            elif event.key == pygame.K_SPACE:

                blink_now()

            elif event.key == pygame.K_a:

                auto_gaze = not auto_gaze

            elif event.key == pygame.K_LEFT:

                set_gaze(
                    -0.45,
                    target_y,
                )

            elif event.key == pygame.K_RIGHT:

                set_gaze(
                    0.45,
                    target_y,
                )

            elif event.key == pygame.K_UP:

                set_gaze(
                    target_x,
                    -0.28,
                )

            elif event.key == pygame.K_DOWN:

                set_gaze(
                    target_x,
                    0.28,
                )

            elif event.key == pygame.K_1:

                set_mode("idle")

            elif event.key == pygame.K_2:

                set_mode("talking")

            elif event.key == pygame.K_3:

                set_mode("thinking")

            elif event.key == pygame.K_4:

                set_mode("surprised")

    update_animation(dt)

    draw_eye(screen)

    pygame.display.flip()


pygame.quit()
sys.exit()