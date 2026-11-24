# Micropython imports
from machine import Pin, PWM
import neopixel

# Built-in imports
import time
import sys

print(sys.version)          # Shows Python syntax version (e.g., 3.4.0)
print(sys.implementation)   # Shows MicroPython version tuple (e.g., (1, 24, 1, ''))

###############
# Input Setup #
###############
brakeOrTurnSensePin     = Pin(34, Pin.IN)
turnSensePin            = Pin(35, Pin.IN) # This signal must be created and routed from the steering column of the corvette to the ESP32.  It is not currently available.
runningLightsSensePin   = Pin(32, Pin.IN)
reverseSensePin         = Pin(33, Pin.IN) # This signal must be created and routed from the rear backup light of the corvette to the ESP32.  It is not currently available.

######################
# COB PWM Attributes #
######################
freq = 500
highDuty = 0.05
minPwmValue = 0
maxPwmValue = 1023
dimPwmValue = int(maxPwmValue * highDuty)  # Calculate the dimPwmValue based on the maxPwmValue and highDuty

################
# Output Setup #
################
# Proof of life LED
heartBeatLedPin         = Pin(2, Pin.OUT)
# WS2812B RGB LED Data Pin
rgbLedDataPin           = Pin(4, Pin.OUT)
# Hardware PWM for COB LED
cobLedPwmPin            = PWM(Pin(22), freq=freq, duty=0)

# Store variables outside the function
blinkerState = 0  # Initialize the blinkerState variable to 0
blinkerPrevTime = time.ticks_ms()  # Initialize the blinkerPrevTime variable to the current time in milliseconds
blinkerFreq = 1.0
blinkerPeriod = 1 / blinkerFreq

# Function to toggle the heartBeatLedPin every second
def updateBlinker():
    
    # Declare the variables as global to modify them within the function
    global blinkerState
    global blinkerPrevTime

    # Get the current time in milliseconds
    blinkerCurrTime = time.ticks_ms()

    if (time.ticks_diff(blinkerCurrTime, blinkerPrevTime) >= blinkerPeriod * 500):  # Check if the heartbeat period has passed
        blinkerState ^= 1  # Toggle the blinkerState variable (0 becomes 1, and 1 becomes 0)
        heartBeatLedPin.value(blinkerState)  # Set the heartBeatLedPin to the blinkerState variable
        blinkerPrevTime = blinkerCurrTime  # Update the blinkerPrevTime to the current time

# Function to update the COB PWM logic based on the value control passed in.
# 0 == No Running lights, not currently braking.
# 1 == Running lights (half brightness) OR actively turning and turn signal is in the dim portion
# 2 == Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
def updateCobPwm(control):

    # Solid Off (No Running lights and not currently braking - COB off)
    if (control == 0):
        cobLedPwmPin.duty(minPwmValue)  # Turn cobLedPwmPin off

    # Solid Dim (Running lights - COB at half brightness)
    elif (control == 1):
        cobLedPwmPin.duty(dimPwmValue)  # Turn cobLedPwmPin on at dim brightness

    # Solid Bright (Currently braking - COB full brightness)
    elif (control == 2):
        cobLedPwmPin.duty(maxPwmValue)  # Turn cobLedPwmPin on full brightness

    # Toggle between OFF and Full Brightness
    elif (control == 3):
        if (blinkerState == 0):
            cobLedPwmPin.duty(minPwmValue)  # Turn cobLedPwmPin off
        else:
            cobLedPwmPin.duty(maxPwmValue)  # Turn cobLedPwmPin on full brightness

    # Toggle between DIM and Full Brightness
    elif (control == 4):
        if (blinkerState == 0):
            cobLedPwmPin.duty(dimPwmValue)  # Turn cobLedPwmPin off
        else:
            cobLedPwmPin.duty(maxPwmValue)  # Turn cobLedPwmPin on full brightness

    else:
        print("Error: Invalid control value passed to updateCobPwm() function. Control value must be 0, 1, or 2.")
        cobLedPwmPin.duty(maxPwmValue)  # Turn cobLedPwmPin off in case of error

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

# Function to update the Neopixel logic based on the value control passed in.
# 0 == No Running lights, not currently braking.
# 1 == Running lights (half brightness) OR actively turning and turn signal is in the dim portion
# 2 == Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
# 3 == Currently reversing and brake signal not active while running lights on
# 4 == Currently reversing and brake signal active
# 5 == Currently reversing and brake signal not active while running lights not on
def updateNeopixel(control):
    if (control == 0): # No Running lights, not currently braking
        neopixelArray.fill((0, 0, 0))
        neopixelArray.write()

    elif (control == 1): # Running lights (half brightness) OR actively turning and turn signal is in the dim portion
        neopixelArray.fill((128, 0, 0))
        neopixelArray.write()

    elif (control == 2): # Currently braking (full brightness) OR actively turning and turn signal is in the bright portion
        neopixelArray.fill((255, 0, 0))
        neopixelArray.write()

    elif (control == 3): # Currently reversing and brake signal not active while running lights on
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

    elif (control == 4): # Currently reversing and brake signal active
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

    elif (control == 5): # Currently reversing and brake signal not active while running lights not on
        # Clear the array 
        neopixelArray.fill((0, 0, 0))
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

# Input decoding function to read the input pins and return a 4-bit value representing the state of the inputs
def readInputs():

    return (
        (reverseSensePin.value() << 3) |
        (brakeOrTurnSensePin.value() << 2) |
        (turnSensePin.value() << 1) |
        runningLightsSensePin.value()
    )

# Create cobSelect and cobSelectR variables to be used in the following case statements
cobSelect  = 0b0000  # Initialize cobSelect variable to No Reverse, No Brake, No Turn, No Running lights
cobSelectR = 0b0000  # Initialize cobSelectR variable to No Reverse, No Brake, No Turn, No Running lights
cobControl = 0

# Create neopixelSelect and neopixelSelectR variables to be used in the following case statements
neopixelSelect  = 0b0000  # Initialize neopixelSelect variable to No Reverse, No Brake, No Turn, No Running lights
neopixelSelectR = 0b0000  # Initialize neopixelSelectR variable to No Reverse, No Brake, No Turn, No Running lights
neopixelControl = 0

while True:

    # Call updateBlinker() function every loop no matter what
    updateBlinker()
    
    # Build the data value used for the following case statements
    neopixelSelect = readInputs()

    # Mask out the reverse bit for COB control, only keeping the combined brake & turn, turn, and running light bits
    cobSelect = neopixelSelect & 0b0111

    # Only run the following code if cobSelect has changed
    if (cobSelectR != cobSelect):
        cobSelectR = cobSelect
        updateCobCase = True
    else:
        updateCobCase = False

    # We want to dynamically call updateCobPwm if the value has not changed AND if the control value is one of the two toggling values
    if (updateCobCase == False):
        # Previously set cobControl value is one of the blinking turn states
        if (cobControl == 3 or cobControl == 4):
            updateCobPwm(cobControl) # Call updateCobPwm with previous value
        # Previously set cobControl value is not one of the blinking turn states
        else:
            None

    elif (updateCobCase == True):  # Only run the following code if cobSelect has changed

        # No Brake / Turn combined, Turn, no Running Lights 
        #   OR
        # Brake / Turn combined, Turn, no Running Lights
        if (cobSelect == 0b0010 or cobSelect == 0b0110):
            # COB should toggle between OFF and ON
            cobControl = 3

        # No Brake / Turn combined, Turn, Running Lights 
        #   OR
        # Brake / Turn combined, Turn, Running Lights
        elif (cobSelect == 0b0011 or cobSelect == 0b0111):
            # COB should toggle between DIM and ON
            cobControl = 4

        # No Brake / Turn combined, No Turn, no Running Lights
        elif (cobSelect == 0b0000):
            # COB should be Solid OFF
            cobControl = 0
        
        # No Brake / Turn combined, No Turn, Running Lights
        elif (cobSelect == 0b0001):
            # COB should be Solid DIM
            cobControl = 1
        
        # Brake / Turn combined, No Turn, no Running Lights
        #   OR
        # Brake / Turn combined, No Turn, Running Lights
        elif (cobSelect == 0b0100 or cobSelect == 0b0101): 
            # COB should be Solid ON
            cobControl = 2
        
        updateCobPwm(cobControl)        # Update the COB PWM based on the new cobControl value

    if (neopixelSelect != neopixelSelectR):  # Only run the following code if neopixelSelect has changed
        neopixelSelectR = neopixelSelect
        updateNeopixelCase = True
    else:
        updateNeopixelCase = False

    if (updateNeopixelCase == True):  # Only run the following code if neopixelSelect has changed
        if (neopixelSelect == 0b0111):  # No Reverse, Brake / Turn, Turn, Running lights
            neopixelControl = 2

        elif (neopixelSelect == 0b0101):  # No Reverse, Brake / Turn, No Turn, Running lights
            neopixelControl = 2

        elif (neopixelSelect == 0b0011):  # No Reverse, No Brake / Turn, Turn, Running lights
            neopixelControl = 1

        elif (neopixelSelect == 0b0001):  # No Reverse, No Brake / Turn, No Turn, Running lights
            neopixelControl = 1

        elif (neopixelSelect == 0b0110):  # No Reverse, Brake / Turn, Turn, No Running lights
            neopixelControl = 2

        elif (neopixelSelect == 0b0100):  # No Reverse, Brake / Turn, No Turn, No Running lights
            neopixelControl = 2

        elif (neopixelSelect == 0b0010):  # No Reverse, No Brake / Turn, Turn, No Running lights
            neopixelControl = 0

        elif (neopixelSelect == 0b0000):  # No Reverse, No Brake / Turn, No Turn, No Running lights
            neopixelControl = 0

        elif (neopixelSelect == 0b1111):  # Reverse, Brake / Turn, Turn, Running lights
            neopixelControl = 4

        elif (neopixelSelect == 0b1101):  # Reverse, Brake / Turn, No Turn, Running lights
            neopixelControl = 4

        elif (neopixelSelect == 0b1011):  # Reverse, No Brake / Turn, Turn, Running lights
            neopixelControl = 3

        elif (neopixelSelect == 0b1001):  # Reverse, No Brake / Turn, No Turn, Running lights
            neopixelControl = 3

        elif (neopixelSelect == 0b1110):  # Reverse, Brake / Turn, Turn, No Running lights
            neopixelControl = 4

        elif (neopixelSelect == 0b1100):  # Reverse, Brake / Turn, No Turn, No Running lights
            neopixelControl = 4

        elif (neopixelSelect == 0b1010):  # Reverse, No Brake / Turn, Turn, No Running lights
            neopixelControl = 5

        elif (neopixelSelect == 0b1000):  # Reverse, No Brake / Turn, No Turn, No Running lights
            neopixelControl = 5

        updateNeopixel(neopixelControl) # Update the Neopixel based on the new neopixelControl value
    
    # Small polling delay to avoid running the loop too fast, which is not necessary for this application
    time.sleep(0.005)  # Delay for 5 milliseconds
