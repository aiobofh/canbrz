#!/usr/bin/env python
#
# This is pretty much hardcoded stuff just to demonstrate how this gauge will
# be coded.
#

import pygame
import math

BLACK = (0, 0, 0)
RED = (200, 0, 0)
LIGHTRED = (255, 200, 200)

INNERRADIUS=50
OUTERRADIUS=190

pygame.init()

size = (640,500)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("CanBRZ")

done = False
clock = pygame.time.Clock()

water = pygame.image.load("../graphics/meter.png").convert()
water_warning = pygame.image.load("../graphics/meter_warning.png").convert()

water_blink = False
ticks=0
angle=1.6
angle=3.14 * 2
water_value=40
intro=True
intro_reverse=False

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
    screen.fill(BLACK)

    water_value = 140 if water_value > 140
    water_value = 40 if water_value < 40

    water_blink = (water_value > 120)

    if water_blink == True and ticks < 5:
        screen.blit(water_warning, [70, 0])
    else:
        screen.blit(water, [70, 0])

    angle = (water_value - 40) / 21.37

    percent = angle + 1.6

    # Rotate all points making up the pointer
    x0 = math.cos(percent) * (INNERRADIUS + 2)
    y0 = math.sin(percent) * (INNERRADIUS + 2)
    x1 = math.cos(percent + 0.03) * INNERRADIUS
    y1 = math.sin(percent + 0.03) * INNERRADIUS
    x2 = math.cos(percent) * OUTERRADIUS
    y2 = math.sin(percent) * OUTERRADIUS
    x3 = math.cos(percent - 0.03) * INNERRADIUS
    y3 = math.sin(percent - 0.03) * INNERRADIUS
    x4 = math.cos(percent) * (OUTERRADIUS - 2)
    y4 = math.sin(percent) * (OUTERRADIUS - 2)

    pygame.draw.polygon(screen, RED, [[320 + x1, 250 + y1],
                                      [320 + x2, 250 + y2],
                                      [320 + x3, 250 + y3]], 5)
    pygame.draw.aaline(screen,
                       LIGHTRED,
                       [320 + x0, 250 + y0], [320 + x4, 250 + y4], True)

    # Swap buffer
    pygame.display.flip()

    ticks += 1
    if ticks == 10:
        ticks = 0
    if ticks % 2 == 0:
        pass

    # Silly BRZ style intro sequence.
    if intro == True:
        if intro_reverse == False and water_value < 140:
            water_value += 1
            if water_value == 140:
                intro_reverse = True
        elif intro_reverse == True and water_value > 40:
            water_value -= 1
            if water_value == 40:
                intro_reverse = False
                intro = False

    # Wait for a relevant time (PAL)
    clock.tick(50)

pygame.quit()
