# Micropython imports
from machine import Pin
import neopixel

# Built-in imports
import time
import threading

# Input Setup
brakeOrTurnSensePin     = Pin(34, Pin.IN)
turnSensePin            = Pin(35, Pin.IN) # This signal must be created and routed from the steering column of the corvette to the ESP32.  It is not currently available.
runningLightsSensePin   = Pin(32, Pin.IN)

# Output Setup
cobLedPwmPin            = Pin(2, Pin.OUT)
rgbLedDataPin           = Pin(4, Pin.OUT)

# COB PWM Attributes
freq = 500
period = 1/freq
highDuty = 0.4
highDelay = period * highDuty
lowDelay = period * (1 - highDuty)

class CobPwmControlClass:
    def __init__(self):
        # 0 == No Running lights, not currently braking.
        # 1 == Running lights (half brightness) OR actively turning and turn signal is in the dim portion
        # 2 == Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
        self.cobControl = 0  # Initialize cobControl variable to No Running lights, not currently braking

    # Threaded function to run the COB PWM logic based on the value of self.cobControl
    def runCobPwm(self):
        match self.cobControl:
            case 0:                         # No Running lights, not currently braking
                cobLedPwmPin.value(0)       # Turn cobLedPwmPin off

            case 1:                         # Running lights (half brightness) OR actively turning and turn signal is in the dim portion
                cobLedPwmPin.value(1)       # Turn cobLedPwmPin on
                time.sleep(highDelay)       # High delay predetermined by duty cycle
                cobLedPwmPin.value(0)       # Turn cobLedPwmPin off
                time.sleep(lowDelay)        # Low delay predetermined by duty cycle

            case 2:                         # Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
                cobLedPwmPin.value(1)       # Turn cobLedPwmPin on full brightness

# WS2812 LED Array Attributes
#           [33]    [32]    [31]    [30]    [29]    [28]
#
#       [21]    [22]    [23]    [24]    [25]    [26]    [27]
#
#   [20]    [19]    [18]    [17]    [16]    [15]    [14]    [13]
#
#       [ 6]    [ 7]    [ 8]    [ 9]    [10]    [11]    [12]
#
#           [ 5]    [ 4]    [ 3]    [ 2]    [ 1]    [ 0]
neopixelCount = 34
neopixelArray = neopixel.NeoPixel(rgbLedDataPin, neopixelCount)

class NeopixelControlClass:
    def __init__(self):
        self.neopixelControl = 0  # Initialize neopixelControl variable

    def runNeopixel(self):
        match self.neopixelControl:
            case 0:                             # No Running lights, not currently braking
                neopixelArray.fill((0, 0, 0))
                neopixelArray.write()

            case 1:                             # Running lights (half brightness) OR actively turning and turn signal is in the dim portion
                neopixelArray.fill((128, 0, 0))
                neopixelArray.write()

            case 2:                             # Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
                neopixelArray.fill((255, 0, 0))
                neopixelArray.write()

            case 3:                             # Currently reversing and brake signal not active
                # Fill whole array with dimmed red lights
                neopixelArray.fill((128, 0, 0))
                # Overwrite the middle circle with white lights to indicate reversing.
                neopixelArray[ 8] = (255, 255, 255)
                neopixelArray[ 9] = (255, 255, 255)
                neopixelArray[10] = (255, 255, 255)
                neopixelArray[15] = (255, 255, 255)
                neopixelArray[16] = (255, 255, 255)
                neopixelArray[17] = (255, 255, 255)
                neopixelArray[18] = (255, 255, 255)
                neopixelArray[23] = (255, 255, 255)
                neopixelArray[24] = (255, 255, 255)
                neopixelArray[25] = (255, 255, 255)
                neopixelArray.write()

            case 4:                             # Currently reversing and brake signal active
                # Fill whole array with bright red lights
                neopixelArray.fill((255, 0, 0))
                # Overwrite the middle circle with white lights to indicate reversing.
                neopixelArray[ 8] = (255, 255, 255)
                neopixelArray[ 9] = (255, 255, 255)
                neopixelArray[10] = (255, 255, 255)
                neopixelArray[15] = (255, 255, 255)
                neopixelArray[16] = (255, 255, 255)
                neopixelArray[17] = (255, 255, 255)
                neopixelArray[18] = (255, 255, 255)
                neopixelArray[23] = (255, 255, 255)
                neopixelArray[24] = (255, 255, 255)
                neopixelArray[25] = (255, 255, 255)
                neopixelArray.write()

# Create our classes to be used in the following case statements
cobPwmClass     = CobPwmControlClass()
neopixelClass   = NeopixelControlClass()

# Create threads to run the COB PWM and Neopixel logic in parallel
cobPwmThread     = threading.Thread(target=cobPwmClass.runCobPwm)
neopixelThread   = threading.Thread(target=neopixelClass.runNeopixel)

# Start threads
cobPwmThread.start()
neopixelThread.start()

# Create caseSelect and caseSelectR variables to be used in the following case statements
caseSelect  = 0b000  # Initialize caseSelect variable to No Brake, No Turn, No Running lights
caseSelectR = 0b000  # Initialize caseSelectR variable to No Brake, No Turn, No Running lights

while True:

    # Build the data value used for the following case statements
    caseSelect = brakeOrTurnSensePin.value() << 2 |  turnSensePin.value() << 1 | runningLightsSensePin.value()

    if (caseSelect != caseSelectR):  # Only run the following code if caseSelect has changed
        caseSelectR = caseSelect
        updateCaseSelect = True
    else:
        updateCaseSelect = False

    if (updateCaseSelect == True):  # Only run the following code if caseSelect has changed
        match caseSelect:
            case 0b111:  # Brake / Turn, Turn, Running lights
                cobPwmClass.cobControl          = 2
                neopixelClass.neopixelControl   = 2

            case 0b101:  # Brake / Turn, No Turn, Running lights
                cobPwmClass.cobControl          = 2
                neopixelClass.neopixelControl   = 2

            case 0b011:  # No Brake / Turn, Turn, Running lights
                cobPwmClass.cobControl          = 1
                neopixelClass.neopixelControl   = 1

            case 0b001:  # No Brake / Turn, No Turn, Running lights
                cobPwmClass.cobControl          = 1
                neopixelClass.neopixelControl   = 1

            case 0b110:  # Brake / Turn, Turn, No Running lights
                cobPwmClass.cobControl          = 2
                neopixelClass.neopixelControl   = 2

            case 0b100:  # Brake / Turn, No Turn, No Running lights
                cobPwmClass.cobControl          = 2
                neopixelClass.neopixelControl   = 2

            case 0b010:  # No Brake / Turn, Turn, No Running lights
                cobPwmClass.cobControl          = 0
                neopixelClass.neopixelControl   = 0

            case 0b000:  # No Brake / Turn, No Turn, No Running lights
                cobPwmClass.cobControl          = 0
                neopixelClass.neopixelControl   = 0
