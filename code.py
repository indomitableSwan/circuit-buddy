# SPDX-FileCopyrightText: 2024 C. M. Swanson
#
# This code borrows from:
# Adafruit's adafruit_circuitplayground/circuit_playground_base.py
# SPDX-FileCopyrightText: 2016 Scott Shawcroft for Adafruit Industries
# SPDX-FileCopyrightText: 2017-2019 Kattni Rembor for Adafruit Industries
# SPDX-FileCopyrightText: 2022 Ryan Keith for Adafruit Industries
#
# CircuitPython NeoPixel tutorial (https://learn.adafruit.com/adafruit-circuit-playground-express/circuitpython-neopixel)
# SPDX-FileCopyrightText: 2017 John Edgar Park for Adafruit Industries

# Other resources:
# Multi-tasking with CiruitPython tutorial by Tim C (https://learn.adafruit.com/multi-tasking-with-circuitpython)
# Adafruit Circuit Playground Express tutorial by lady ada (https://learn.adafruit.com/adafruit-circuit-playground-express)
# JADE and OLD_LACE color values from adafruit_led_animation.color module documentation
#
#
# SPDX-License-Identifier: MIT

import gc
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.color import calculate_intensity
from adafruit_thermistor import Thermistor
import adafruit_lis3dh
import array
from audiocore import RawSample
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
import math
import neopixel
from rainbowio import colorwheel
import time
import analogio
import sys

if sys.platform == "nRF52840":
    from audiopwmio import PWMAudioOut as AudioOut
elif sys.platform == "Atmel SAMD21":
    from audioio import AudioOut
else:
    raise Exception("Platform not recognized")

gc.collect()

pixels = neopixel.NeoPixel(board.NEOPIXEL, 10, brightness = 0.05, auto_write=False)

switch = DigitalInOut(board.SLIDE_SWITCH)
switch.direction = Direction.INPUT
switch.pull = Pull.UP

btnA = DigitalInOut(board.BUTTON_A)
btnA.direction = Direction.INPUT
btnA.pull = Pull.DOWN

btnB = DigitalInOut(board.BUTTON_B)
btnB.direction = Direction.INPUT
btnB.pull = Pull.DOWN

# Define sensors:
temp = Thermistor(
    board.TEMPERATURE, 10000, 10000, 25, 3950
    )

light = analogio.AnalogIn(board.LIGHT)

#accelerometer
i2c = busio.I2C(board.ACCELEROMETER_SCL, board.ACCELEROMETER_SDA)
int1 = DigitalInOut(board.ACCELEROMETER_INTERRUPT)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(
        i2c, address=0x19, int1=int1
        )
lis3dh.range = adafruit_lis3dh.RANGE_8_G

# set sensitivity for tap detection
# higher values are less sensitive
def threshold():
    if sys.platform == "nRF52840":
        return 20
    elif sys.platform == "Atmel SAMD21":
        return 20
    else:
        raise Exception("Platform not recognized")

# detect double taps
lis3dh.set_tap(
    tap=2,
    threshold=threshold(),
    time_latency=50
    )

# Define audio
speaker_enable = DigitalInOut(board.SPEAKER_ENABLE)
speaker_enable.switch_to_output(value=True)
dac = AudioOut(board.SPEAKER)

# colors
PINKISH = (255, 0, 255)
BLUEISH = (0, 255, 255)
BLUE = (0, 0, 255)
OLD_LACE = (253, 245, 230)
JADE= (0, 255, 40)

# (sub)session lengths
FOCUS = 20 * 60
SHORT_BREAK = 7 * 60
LONG_BREAK = 15 * 60

def sine(f):
    # Generate one period of sine wav.
    length = 8000 // f
    sine_wave = array.array("H", [0] * length)
    for i in range(length):
        sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
    sine_wave = RawSample(sine_wave, sample_rate=8000)
    return sine_wave

# Fade animation
class Fade:
    def __init__(self, length, start, color0=OLD_LACE, color1=BLUE):
        self.start=start
        self.length=length
        self.color0=color0
        self.color1=color1

    def animate(self):
        intensity = .45*math.sin(1.25*time.monotonic())+.55

        if time.monotonic() + 15 < self.start + self.length:
            pixels.fill(calculate_intensity(self.color0, intensity))
        else:  # warn rest almost over
            pixels.fill(calculate_intensity(self.color1, intensity))

# Rainbow chase animation
# Warning: does not support multi-tasking that changes neopixel display
class RainbowChase:
    def __init__(self, length, start, j=0):
        self.start=start
        self.length=length
        self.j = j

    def animate(self):
        if time.monotonic() < self.start + self.length:
            for i in range(10):
                start_time= time.monotonic()

                rc_index = (i * 256 // 10) + self.j * 5
                pixels[i] = colorwheel(rc_index & 255)

                while time.monotonic() <= start_time + self.length/2550:
                    pixels.show()
            self.j+=1
            if self.j == 255:
                self.j=0

def session(length, start, anim, ctr=-1):
    display_status = False # Boolean for status check

    while time.monotonic() < start + length:
        # Main display
        anim.animate()

        # Check sensors
        if switch.value:
            check_temp()
            check_light()
            gc.collect()
        if btnA.value: # restart
            print("Go back to main!")
            time.sleep(.5)
            return True
        if btnB.value: # skip ahead
            print("Skipping to next session!")
            time.sleep(.5)
            return False
        if lis3dh.tapped and ctr >= 0:
            print("Status check!")
            t = time.monotonic()
            display_status = True

        # Display status briefly if boolean set
        if display_status:
            if time.monotonic() >= t + 2:
                display_status = False
            else:
                pixels[0:ctr+1] = [(255, 0, 0) if isinstance(anim, Fade)
                else (255, 255, 255)]*(ctr+1)
        pixels.show()
    return False

def flow(focus = FOCUS, short_b = SHORT_BREAK, long_b = LONG_BREAK):
    for i in range(0,4):

        print("chasing rainbows")
        start = time.monotonic()
        chase = RainbowChase(length=10, start=start)
        if session(length=10, start=start, anim=chase):
            return# restart
        gc.collect()

        print("starting focus session")
        start = time.monotonic()
        rainbow = Rainbow(pixels, speed=0.1, period=focus, precompute_rainbow=False)
        if session(length=focus, start=start, anim=rainbow, ctr=i):
            return # restart
        gc.collect()

        if i < 3:
            print("starting move session")
            start = time.monotonic()
            fade = Fade(length=short_b, start=start)
            if session(length=short_b, start=start, anim=fade, ctr=i):
                return # restart
            gc.collect()
        else:
            print("starting rest session")
            start = time.monotonic()
            fade = Fade(length=long_b, start=start, color0=BLUEISH, color1=PINKISH)
            if session(length=long_b, start=start, anim=fade):
                return # restart
            gc.collect()

def check_temp():
    temp_c = temp.temperature
    temp_f = temp_c * 1.8 + 32

    while temp_f < 62 or temp_f > 90:
        if not switch.value:
            print("temp is", temp_f)
            return
        dac.play(sine(415), loop=True)
        time.sleep(1)
        dac.stop()

def check_light():
    arr = array.array("H", [])
    for i in range(20):
        arr.append(light.value)
    v = avg(arr)
    while v < 30000:
        if not switch.value:
            print("light value is low:", v)
            return
        pixels.fill(calculate_intensity(JADE, math.sin(1.25*time.monotonic())))
        pixels.show()

def avg(arr):
    sum = 0
    for v in arr:
        sum += v
    return sum/len(arr)

while True:
    pixels.fill(JADE)
    pixels.show()
    gc.collect()

    if switch.value: # left is true
        check_temp()
        check_light()
    gc.collect()

    if btnA.value:
        time.sleep(.5)
        flow(45, 45, 45)
        gc.collect()
