#!/usr/bin/env python
#
# Simple OBD-II client for the ELM327 bluetooth interface to show oil,
# temperature, water temperature, fuel presure and air flow to the
# engine. It will also contain a gear shift inidcator and a krellm-like
# diagram over throttle control.
#
# git clone git://git.code.sf.net/p/pyobd2/code pyobd2-code
#

import serial
import pygame
import math
import sys
import threading
import time
from random import randint

SAMPLE=10
REFRESH=50
INTRO_LENGTH=5

class OBD:
    def __init__(self, tty_name):
        self.dongle = serial.Serial()
        self.dongle.port = tty_name
        self.dongle.timeout = 0
        self.dongle.writeTimeout = 0
        if not tty_name.startswith('/dev/pts'):
            printf("Setting baud-rate")
            self.dongle.baudrate = 38400
        self.dongle.open()
        self.dongle.flushInput()
        self.dongle.flushOutput()

    def __exit__(self, type, value, traceback):
        self.dongle.close()

    def _send(self, string):
        self.dongle.flushInput()
        self.dongle.flushOutput()
        string_to_send = "%s \n" % string
        self.dongle.write(string_to_send)
        self.dongle.flushInput()
        self.dongle.flushOutput()
        retval = ''
        last = 'NO DATA'
        while (retval != '>' and retval != 'NO DATA'):
            if retval != string and retval != '':
                last = retval
            retval = self.dongle.readline().rstrip() # Echo
        self.dongle.flushInput()
        self.dongle.flushOutput()
        return last

    def engine_coolant_temperature(self):
        s = self._send("01 05")
        value = 0
        if s != 'NO DATA':
            print(s)
            value = int(s.split(" ")[2], 16)
        return value - 40

    def oil_temperature(self):
        s = self._send("21 01")
        value = 0
        if s != 'NO DATA':
            print(s)
            value = int(s.split(" ")[2], 16)
        return value - 40

    def fuel_pressure(self):
        s = self._send("01 0A")
        value = 0
        if s != 'NO DATA':
            print(s)
            value = int(s.split(" ")[2], 16)
        value = (value * 3.0) / 100.0
        return value * 3.0 / 100.0

    def air_flow(self):
        s = self._send("01 10")
        value = 0
        if s != 'NO DATA':
            print(s)
            value = int(s.split(" ")[2], 16) * 256 + int(s.split(" ")[3], 16)
        return value / 100.0

class DemoOBD:
    def __init__(self):
        self.value = 70.0
        self.fuel_pressure_value = 1.5

    def engine_coolant_temperature(self):
        self.value += randint(-1,1) / 5.0
        return self.value

    def oil_temperature(self):
        self.value += randint(-1,1) / 5.0
        return self.value

    def fuel_pressure(self):
        self.fuel_pressure_value += randint(-1,1) / 50.0
        return self.fuel_pressure_value

    def air_flow(self):
        self.value += randint(-1,1) / 2.0
        return self.value

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
        self.first = True

    def set(self, value, samples):
        self.old_value = self.value
        self.value = value;

        # Limit the temperature to what the gauge can handle.
        if self.value > self.max_val:
            self.value = self.max_val
        if self.value < self.min_val:
            self.value = self.min_val

        self.delta = self.value - self.old_value

        if self.delta != 0:
            self.offset = 1.0 * abs(1.0 * self.delta / (1.0 * samples))
        else:
            self.offset = 0

    def get_max(self):
        return self.max_val

    def get_min(self):
        return self.min_val

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

    def draw(self, screen, x, y, invert_warning=False):
        w = self.normal.get_width()
        h = self.normal.get_height()

        # If temperature goes above 120 degrees blink the warning lamp.
        if invert_warning == False:
            warn = (self.current_value > self.warn_val)
        else:
            warn = (self.current_value < self.warn_val)
        change = (self.old_current_value != self.current_value)
        self._calc()
        if (change == True) or (self.first == True):
            rad = self._get_rad()

            # Rotate all points making up the pointer
            self.x1 = math.cos(rad + 0.03) * self.inner_needle_radius
            self.y1 = math.sin(rad + 0.03) * self.inner_needle_radius
            self.x2 = math.cos(rad) * self.outer_needle_radius
            self.y2 = math.sin(rad) * self.outer_needle_radius
            self.x3 = math.cos(rad - 0.03) * self.inner_needle_radius
            self.y3 = math.sin(rad - 0.03) * self.inner_needle_radius

        if (change == True) or (warn == True) or (self.first == True):

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
    print ""
    print "To simulate run 'obdsim -g Random -s 42 -g gui_fltk' and give the"
    print "pts-device outputed from obdsim to the canbrz"
    print ""
    print "If you just wnat to check out the program enter 'demo' as serial"
    print "tty and you don't have to set-up a serial interface."
    exit(1)

pygame.init()
# Drawing area
size = (800,480)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("CanBRZ")


water_temperature_gauge = CircularGauge(normal_image="../graphics/water_normal_small.png",
                                        warning_image="../graphics/water_warning_small.png",
                                        inner_needle_radius=22,
                                        outer_needle_radius=90,
                                        min_val=40,
                                        max_val=140,
                                        warn_val=120,
                                        min_val_degrees=269,
                                        max_val_degrees=0,
                                        needle_color=(200,0,0))
oil_temperature_gauge = CircularGauge(normal_image="../graphics/oil_normal_big.png",
                                      warning_image="../graphics/oil_warning_big.png",
                                      inner_needle_radius=45,
                                      outer_needle_radius=185,
                                      min_val=40,
                                      max_val=140,
                                      warn_val=120,
                                      min_val_degrees=269,
                                      max_val_degrees=0,
                                      needle_color=(200,0,0))
fuel_pressure_gauge = CircularGauge(normal_image="../graphics/fuel_pressure_normal_small.png",
                                    warning_image="../graphics/fuel_pressure_warning_small.png",
                                    inner_needle_radius=22,
                                    outer_needle_radius=90,
                                    min_val=0,
                                    max_val=5,
                                    warn_val=1,
                                    min_val_degrees=269,
                                    max_val_degrees=0,
                                    needle_color=(200,0,0))
air_flow_gauge = CircularGauge(normal_image="../graphics/air_flow_normal_small.png",
                               warning_image="../graphics/air_flow_normal_small.png",
                               inner_needle_radius=22,
                               outer_needle_radius=90,
                               min_val=0,
                               max_val=500,
                               warn_val=1,
                               min_val_degrees=269,
                               max_val_degrees=0,
                               needle_color=(200,0,0))


done = False
clock = pygame.time.Clock()

# "/dev/pts/21"
if sys.argv[1] == "demo":
    obd = DemoOBD()
else:
    obd = OBD(sys.argv[1])

# Update graphics
screen.fill((0,0,0))
samples = 0
ticks = 0
samples = 0

def read_from_port():
    while done == False:
        if samples > INTRO_LENGTH * 3:
            water_val = obd.engine_coolant_temperature()
            oil_val = obd.oil_temperature()
            fuel_val = obd.fuel_pressure()
            air_val = obd.air_flow()
            water_temperature_gauge.set(water_val, SAMPLE)
            oil_temperature_gauge.set(oil_val, SAMPLE)
            fuel_pressure_gauge.set(fuel_val, SAMPLE)
            air_flow_gauge.set(air_val, SAMPLE)
            time.sleep(0.5)

thread = threading.Thread(target=read_from_port)

while done == False:
#    done = True
    # Handle various ways to quit the program.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
            time.sleep(3)
        if event.type is pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            done = True
            time.sleep(3)
        if event.type is pygame.KEYDOWN and event.key == pygame.K_q:
            done = True
            time.sleep(3)
        if event.type is pygame.KEYDOWN and event.key == pygame.K_f:
            pygame.display.toggle_fullscreen()

    if ticks == 0:
        if samples == 0:
            water_temperature_gauge.set(water_temperature_gauge.get_min(),
                                        SAMPLE * 5)
            oil_temperature_gauge.set(oil_temperature_gauge.get_min(),
                                      SAMPLE * 5)
            fuel_pressure_gauge.set(fuel_pressure_gauge.get_min(), SAMPLE * 5)
            air_flow_gauge.set(air_flow_gauge.get_min(), SAMPLE * 5)
        elif samples == INTRO_LENGTH:
            water_temperature_gauge.set(water_temperature_gauge.get_max(),
                                        SAMPLE * 5)
            oil_temperature_gauge.set(oil_temperature_gauge.get_max(),
                                      SAMPLE * 5)
            fuel_pressure_gauge.set(fuel_pressure_gauge.get_max(), SAMPLE * 5)
            air_flow_gauge.set(air_flow_gauge.get_max(), SAMPLE * 5)
        elif samples == INTRO_LENGTH * 2:
            water_temperature_gauge.set(water_temperature_gauge.get_min(),
                                        SAMPLE * 5)
            oil_temperature_gauge.set(oil_temperature_gauge.get_min(),
                                      SAMPLE * 5)
            fuel_pressure_gauge.set(fuel_pressure_gauge.get_min(), SAMPLE * 5)
            air_flow_gauge.set(air_flow_gauge.get_min(), SAMPLE * 5)
            thread.start()

    screen.fill((0,0,0))
    water_temperature_gauge.draw(screen,400,0)
    oil_temperature_gauge.draw(screen,0,0)
    fuel_pressure_gauge.draw(screen,600,0, True)
    air_flow_gauge.draw(screen,500,200)
    # Swap buffer
    pygame.display.flip()

    # Wait for a relevant time (PAL)
    clock.tick(REFRESH)
    ticks += 1
    if ticks > SAMPLE:
        ticks = 0
        samples += 1

pygame.quit()
