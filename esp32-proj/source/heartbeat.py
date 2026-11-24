from machine import Pin, PWM
import time

print("STEP 1: Imports successful")

heartBeatLedPin = Pin(2, Pin.OUT)
print("STEP 2: GPIO initialized")

freq = 500

cobLedPwmPin = PWM(Pin(22), freq=freq, duty=0)
print("STEP 3: PWM initialized")

while True:
    heartBeatLedPin.value(1)
    print("Heartbeat ON")
    time.sleep(1)

    heartBeatLedPin.value(0)
    print("Heartbeat OFF")
    time.sleep(1)