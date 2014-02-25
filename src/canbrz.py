#!/usr/bin/env python
#
# This is pretty much hardcoded stuff just to demonstrate how this gauge will
# be coded.
#

import pygame
import math

# Some nice constants
BLACK = (0, 0, 0)
RED = (200, 0, 0)
LIGHTRED = (255, 200, 200)
INNERRADIUS=50  # The inner radius of the gauge needle
OUTERRADIUS=190 # The outer radius of the gauge needle
METERSTART=1.6  # The offset at which the gauge starts (40 degrees)

pygame.init()

# Drawing area
size = (640,500)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("CanBRZ")

done = False
clock = pygame.time.Clock()

# Graphics
water = pygame.image.load("../graphics/meter.png").convert()
water_warning = pygame.image.load("../graphics/meter_warning.png").convert()

# Initial values
water_blink = False
ticks=0
water_value=40
intro=True
intro_reverse=False

while not done:
    # Handle various ways to quit the program.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type is pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            done = True
        if event.type is pygame.KEYDOWN and event.key == pygame.K_q:
            done = True
        if event.type is pygame.KEYDOWN and event.key == pygame.K_f:
            pygame.display.toggle_fullscreen()

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
    else:
       water_value += 0.04 # Just for demo

    # Limit the temperature to what the gauge can handle.
    if water_value > 140:
        water_value = 140
    if water_value < 40:
        water_value = 40

    # If temperature goes above 120 degrees blink the warning lamp.
    water_blink = (water_value > 120)

    # Calculate the rotation of the needle.
    radians = (water_value - 40) / 21.37
    meter_radians = radians + METERSTART

    # Rotate all points making up the pointer
    x1 = math.cos(meter_radians + 0.03) * INNERRADIUS
    y1 = math.sin(meter_radians + 0.03) * INNERRADIUS
    x2 = math.cos(meter_radians) * OUTERRADIUS
    y2 = math.sin(meter_radians) * OUTERRADIUS
    x3 = math.cos(meter_radians - 0.03) * INNERRADIUS
    y3 = math.sin(meter_radians - 0.03) * INNERRADIUS

    # Update graphics
    screen.fill(BLACK)
    if water_blink == True and ticks < 5:
        screen.blit(water_warning, [70, 0])
    else:
        screen.blit(water, [70, 0])
    pygame.draw.polygon(screen, RED, [[320 + x1, 250 + y1],
                                      [320 + x2, 250 + y2],
                                      [320 + x3, 250 + y3]], 5)
    # Swap buffer
    pygame.display.flip()

    # Just a little trick to keep track of blinknig time
    ticks += 1
    if ticks == 10:
        ticks = 0

    # Wait for a relevant time (PAL)
    clock.tick(50)

pygame.quit()
