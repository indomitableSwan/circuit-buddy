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

if sys.platform == "nRF52840": # CPBluefruit
    from audiopwmio import PWMAudioOut as AudioOut
elif sys.platform == "Atmel SAMD21": # CPExpress
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
        return 30
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

# import (sub)session lenghts, env thresholds
from config import lengths, env


global restart
restart = False

def sine(f):
    # Generate one period of sine wav.
    length = 8000 // f
    sine_wave = array.array("H", [0] * length)
    for i in range(length):
        sine_wave[i] = int(math.sin(math.pi * 2 * i / length) * (2 ** 15) + 2 ** 15)
    sine_wave = RawSample(sine_wave, sample_rate=8000)
    return sine_wave

def focus_session(length, ctr=-1):
    start = time.monotonic()

    # The time at which to stop displaying status
    # Initialized to start since we only display after a tap
    display_end = start

    rainbow = Rainbow(pixels, speed=0.1, period=length, precompute_rainbow=False)

    while time.monotonic() < start + length:
        rainbow.animate()
        if switch.value:
            check_temp()
            check_light()
            gc.collect()

        if btnA.value: # restart
            time.sleep(.5)
            return True

        if btnB.value: # skip to break
            time.sleep(.5)
            return False

        if lis3dh.tapped and ctr>=0:
            status()
            display_end = time.monotonic() + 2

        if time.monotonic() <= display_end: # Display status if tap
            pixels[0:ctr+1] = [(255,255,255)]*(ctr+1)
            pixels.show()
    return False

def rest(length, ctr=-1, color0=OLD_LACE, color1=BLUE):
    start = time.monotonic()

    # The time at which to stop displaying status
    # Initialized to start since we only display after a tap
    display_end = start

    while time.monotonic() < start + length:
        intensity = .45*math.sin(1.25*time.monotonic())+.55
        if switch.value:
            check_temp()
            check_light()
            gc.collect()

        if btnA.value: # restart
            time.sleep(.5)
            return True
        if btnB.value: # restart break
            time.sleep(.5)
            start = time.monotonic()
        if lis3dh.tapped and ctr >= 0:
            status()
            display_end=time.monotonic() + 2

        # Set fade colors
        if time.monotonic() + 15 < start + length:
            if time.monotonic() <= display_end: # Display status if tap
                pixels[0:ctr+1] = [(255,0,0)]*(ctr+1)
                pixels[ctr+1::] = [calculate_intensity(color0, intensity)]*len(pixels[ctr+1::])
            else:
                pixels.fill(calculate_intensity(color0, intensity))

        else:  # Change fade color when rest almost over
            if time.monotonic() <= display_end: # Display status if tap
                pixels[0:ctr+1] = [(255,0,0)]*(ctr+1)
                pixels[ctr+1::] = [calculate_intensity(color1, intensity)]*len(pixels[ctr+1::])
            else:
                pixels.fill(calculate_intensity(color1, intensity))

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
                        check_light()
                        gc.collect()

                    if btnA.value: # restart
                        time.sleep(.5)
                        return True

                    if btnB.value: # skip to break
                        time.sleep(.5)
                        return False

                    pixels.show()
    return False

def flow(focus = lengths['focus'], short_b = lengths['short_break'], long_b = lengths['long_break']):
    for i in range(0,4):
        print("chasing rainbows")
        if chasing_rainbow(5):
            return# restart
        gc.collect()

        print("starting focus session")
        if focus_session(focus, i):
            return # restart
        gc.collect()

        if i < 3:
            print("starting move session")
            if rest(length=short_b, ctr=i):
                return # restart
            gc.collect()
        else:
            print("starting rest session")
            if rest(length=long_b, color0=BLUEISH, color1=PINKISH):
                return # restart
            gc.collect()

def status():
    print("Status check!")
    print("temp:",fahrenheit(temp.temperature),"F")
    print("light:",analog_voltage(light),"V")

def fahrenheit(t):
    return t*1.8+32

def check_temp():
    temp_c = temp.temperature
    temp_f = fahrenheit(temp_c)

    while temp_f < 62 or temp_f > 90:
        if not switch.value:
            print("temp is", temp_f)
            return
        dac.play(sine(415), loop=True)
        time.sleep(1)
        dac.stop()

# light sensor readings as volts across resistor
def analog_voltage(adc):
    return adc.value/65335*adc.reference_voltage

def check_light():
    arr = array.array("f", [])

    for i in range(20):
        arr.append(analog_voltage(light))
    v = avg(arr)

    while v < env['dark']:
        if not switch.value:
            print("The room is too dark:", v)
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
        flow()
        gc.collect()
