# CircuitBuddy Overview

CircuitBuddy helps you be mindful of your environment and wellness while still allowing you to focus on projects. This is built with my specific use case in mind; please feel free to make your own modifications.

The code is designed to run on the [Circuit Playground Express](https://learn.adafruit.com/adafruit-circuit-playground-express/) and the [CircuitPlayground Bluefruit](https://learn.adafruit.com/adafruit-circuit-playground-bluefruit/). Adafruit provides a very good guide to getting your hardware setup with the code loaded, so I won't repeat those instructions in detail here, but [see notes below](#setting-up-your-device).

Current features:
- _Temperature alerts_: If the board's switch is set to "true" (left) and the onboard temperature sensor reads below 62 Fahrenheit ("Go put on socks!") or above 90 Fahrenheit ("You forgot to turn on the AC!"), the board plays an audio alert. The audio quality is suprememly irritating, so first flip the switch to "false" (right) and then address the problem.
- _Light alerts_: If the board's switch is set to "true" (left) and the onboard light sensor detects that the room is dark, the neopixels will give a colorful display that transitions through various shades of green and blue. Either enjoy the display or flip the switch to "false" (right). Note: once you fix the lighting, you have to reset by flipping the switch to false and then true again.
- _Quasi pomodoro timer_: Divides your session into parts and gives you a visual display of the passing time and session flow using the onboard neopixels. The session types are as follows:
    - Go Chasing Rainbows: When Button A is pressed, a rainbow chase animation is briefly displayed to allow you to settle in to focus.
    - Focus: The board will slowly cycle through colors of the rainbow. The default time is set to 20 minutes.
    - Move: The board will display a pulsing off-white color until the subsession is almost done, when the color will switch to blue. Take a break, get up and move! The default time is set to 7 minutes.
    - Rest: The board will display a pulsing bluish teal color until the subsession is almost done, when the color will switch to pinkish. Take a longer break, move more, go do your laundry or get lunch started! The default time is 15 minutes.
    
    The session flow is: Chasing Rainbows, Focus, Move, Focus, Move, Focus, Move, Focus, Rest.

# Usage, customization and caveats
Some features will probably change; it's a mix between dev convenience and intended functionality right now. Currently:
- A good signal that the board is working is if the neopixels are jade in color. From here you can:
    - Press Button A to start a session flow.
    - Press the reset button to restart the board. It's a good idea to do this after each session flow, because time drifts! This is a fundamental constraint of the hardware.
- Go back to the main display at any time by pressing Button A. This may change because it's useful for development, but allows you to skip Move/Rest subsessions.
- Skip ahead from a Focus subsession to Move or Rest (depending on where you are in the flow) by pressing Button B.
- Restart a Move or Rest subsession by pressing Button B. 

There is currently no support built in for adjusting your settings from the defaults. But you can manually change them!

# Setting up your device
## Dependencies
-  adafruit_thermistor.mpy
-  neopixel.mpy
-  adafruit_led_animation

Put these dependencies in the device's library folder, `lib`.

## Circuit Playground Bluefruit
Save `code.py` on your device, at the top level.

## Circuit Playground Express
This device is more resource-constrained than the Bluefruit, so we have to compress the code using the [mpy-cross toolchain](https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library?view=all#mpy-3106477). Put the `buddy.mpy` library file in the device's libary folder, `lib`, then create a `code.py` file at the top level that contains the line:
`import buddy`.

If you want to change defaults or customize the code, you'll have to use the mpy-cross toolchain to build the new version of `buddy.mpy` yourself.

# Contributions, Licenses, etc.

[SPDX MIT license](https://spdx.org/licenses/MIT.html) applies. Contributions are welcome. 