# SPDX-FileCopyrightText: 2024 C. M. Swanson
#
# This code borrows from:
# Adafruit's adafruit_circuitplayground/circuit_playground_base.py
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
from adafruit_thermistor import Thermistor
import array # freeish
from audiocore import RawSample
from audioio import AudioOut
import board
from digitalio import DigitalInOut, Direction, Pull
import math
import neopixel
from rainbowio import colorwheel
import time
import analogio
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
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60

global restart
restart = False

def sine():
    # Generate one period of sine wav.
    length = 8000 // 415
    sine_wave = array.array("H", [0] * length)
    for i in range(length):
        sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
    sine_wave = RawSample(sine_wave, sample_rate=8000)
    return sine_wave

def focus_session(length):
    start = time.monotonic()

    rainbow = Rainbow(pixels, speed=0.1, period=length, precompute_rainbow=False)

    while time.monotonic() < start + length:
        rainbow.animate()
        if switch.value:
            check_temp()

        if btnA.value: # restart
            time.sleep(.5)
            return True

        if btnB.value: # skip to break
            time.sleep(.5)
            return False
    return False

def rest(length, color0=OLD_LACE, color1=BLUE):
    start = time.monotonic()

    while time.monotonic() < start + length:
        if switch.value:
            check_temp()

        if btnA.value: # restart
            time.sleep(.5)
            return True
        if btnB.value: # restart break
            time.sleep(.5)
            start = time.monotonic()
        if time.monotonic() + 15 < start + length:

            pixels.fill(color0)
            pixels.show()

        else:  # warn rest almost over
            pixels.fill(color1)
            pixels.show()
    return False

def chasing_rainbow(length):
    start = time.monotonic()

    while time.monotonic() < start + length:
        for j in range(255):
            for i in range(10):
                start_time = time.monotonic()

                rc_index = (i * 256 // 10) + j * 5
                pixels[i] = colorwheel(rc_index & 255)

                while time.monotonic() <= start_time + length/2550:
                    if switch.value:
                        check_temp()

                    if btnA.value: # restart
                        time.sleep(.5)
                        return True

                    if btnB.value: # skip to break
                        time.sleep(.5)
                        return False

                    pixels.show()
    return False

def session(focus = FOCUS, short_b = SHORT_BREAK, long_b = LONG_BREAK):
    for i in range(0,4):
        if chasing_rainbow(5):
            return# restart
        gc.collect()

        print("starting focus session")
        if focus_session(FOCUS):
            return # restart
        gc.collect()

        if i < 3:
            print("starting short break session")
            if rest(SHORT_BREAK, PINKISH, BLUEISH):
                return # restart
            gc.collect()
        else:
            print("starting long break session")
            if rest(LONG_BREAK):
                return # restart
            gc.collect()

def check_temp():
    temp_c = temp.temperature
    temp_f = temp_c * 1.8 + 32

    while temp_f < 62 or temp_f > 90:
        if not switch.value:
            print("temp is", temp_f)
            return
        dac.play(sine(), loop=True)
        time.sleep(1)
        dac.stop()

def check_light():
    print((light.value, ))
    time.sleep(0.1)

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
        session(30, 20, 20)
        gc.collect()




