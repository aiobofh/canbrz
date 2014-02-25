#!/usr/bin/env python
#
# This is pretty much hardcoded stuff just to demonstrate how this gauge will
# be coded.
#

import serial
import pygame
import math
import sys

SAMPLE=10
REFRESH=50

class OBD:
    def __init__(self, tty_name):
        self.dongle = serial.Serial()
        self.dongle.port = tty_name
        self.dongle.open()
        self.dongle.flushInput()
        self.dongle.flushOutput()

    def engine_coolant_temperature(self):
        self.dongle.write("01 05\n")
        retval = self.dongle.readline() # Echo
        retval = self.dongle.readline() # New Line
        retval = self.dongle.readline() # Something
        retval = self.dongle.readline() # The value
        (foo,bar,val) = retval.split(" ")
        return int(val, 16)-40

class CircularGauge:
    def __init__(self,
                 normal_image,
                 warning_image,
                 inner_needle_radius,
                 outer_needle_radius,
                 min_val,
                 max_val,
                 warn_val,
                 min_val_degrees,
                 max_val_degrees,
                 needle_color):
        self.normal = pygame.image.load(normal_image).convert()
        self.warning = pygame.image.load(warning_image).convert()
        self.inner_needle_radius = inner_needle_radius
        self.outer_needle_radius = outer_needle_radius
        self.min_val = min_val
        self.max_val = max_val
        self.warn_val = warn_val
        self.min_val_degrees = min_val_degrees
        self.max_val_degrees = max_val_degrees
        self.needle_color = needle_color
        self.ticks = 0
        self.delta = 0
        self.old_value = min_val
        self.value = min_val
        self.current_value = min_val
        self.old_current_value = min_val
        self.gauge_range = self.max_val - self.min_val

    def set(self, value):
        self.old_value = self.value
        self.value = value;

        # Limit the temperature to what the gauge can handle.
        if self.value > self.max_val:
            self.value = self.max_val
        if self.value < self.min_val:
            self.value = self.min_val

        self.delta = self.value - self.old_value

        if self.delta != 0:
            self.offset = 1.0 * abs(1.0 * self.delta / (1.0 * SAMPLE))
        else:
            self.offset = 0

    def get(self):
        return self.value

    def _calc(self):
        self.old_current_value = self.current_value
        if self.delta < 0 and self.current_value > self.value:
            self.current_value -= self.offset
            if self.current_value < self.min_val:
                self.current_value = self.min_val
        elif self.delta > 0 and self.current_value < self.value:
            self.current_value += self.offset
            if self.current_value > self.max_val:
                self.current_value = self.max_val
        else:
            self.delta = 0
            self.offset = 0

    def _get_rad(self):
        # Calculate the sector making up the gauge-scale.
        value = (self.current_value - self.min_val) / self.gauge_range

        if self.min_val_degrees == 0:
            min_rad = (3.14 * 2)
        else:
            min_rad = (3.14 * 2) / (360.0 / self.min_val_degrees)
        if self.max_val_degrees == 0:
            max_rad = (3.14 * 2)
        else:
            max_rad = (3.14 * 2) / (360.0 / self.max_val_degrees)
        rad = ((3.14 * 2) - (max_rad - min_rad)) * value - min_rad
        return rad

    def draw(self, screen, x, y):
        w = self.normal.get_width()
        h = self.normal.get_height()

        # If temperature goes above 120 degrees blink the warning lamp.
        warn = (self.current_value > self.warn_val)

        self._calc()
        if self.old_current_value != self.current_value:
            rad = self._get_rad()

            # Rotate all points making up the pointer
            self.x1 = math.cos(rad + 0.03) * self.inner_needle_radius
            self.y1 = math.sin(rad + 0.03) * self.inner_needle_radius
            self.x2 = math.cos(rad) * self.outer_needle_radius
            self.y2 = math.sin(rad) * self.outer_needle_radius
            self.x3 = math.cos(rad - 0.03) * self.inner_needle_radius
            self.y3 = math.sin(rad - 0.03) * self.inner_needle_radius

        if (self.old_current_value != self.current_value) or (warn == True):

            if warn == True and self.ticks < 5:
                screen.blit(self.warning, [x, y])
            else:
                screen.blit(self.normal, [x, y])

            pygame.draw.polygon(screen, self.needle_color,
                                [[x + w/2 + self.x1, y + h/2 + self.y1],
                                 [x + w/2 + self.x2, y + h/2 + self.y2],
                                 [x + w/2 + self.x3, y + h/2 + self.y3]],
                                5)

        self.ticks += 1

        if self.ticks > 10:
            self.ticks = 0

if len(sys.argv) != 2:
    print "canbrz <serial tty>"
    exit(1)

pygame.init()
# Drawing area
size = (800,600)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("CanBRZ")


water_gauge = CircularGauge(normal_image="../graphics/meter.png",
                            warning_image="../graphics/meter_warning.png",
                            inner_needle_radius=50,
                            outer_needle_radius=190,
                            min_val=40,
                            max_val=140,
                            warn_val=120,
                            min_val_degrees=269,
                            max_val_degrees=0,
                            needle_color=(200,0,0))

done = False
clock = pygame.time.Clock()

# "/dev/pts/21"
obd = OBD(sys.argv[1])

# Update graphics
screen.fill((0,0,0))

ticks = 0
while not done:
#    done = True
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

    if ticks == 0:
        val = obd.engine_coolant_temperature()
        water_gauge.set(val)

    water_gauge.draw(screen,0,0)
    # Swap buffer
    pygame.display.flip()

    # Wait for a relevant time (PAL)
    clock.tick(REFRESH)
    ticks += 1
    if ticks > SAMPLE:
        ticks = 0

pygame.quit()
