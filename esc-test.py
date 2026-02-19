import time
from adafruit_pca9685 import PCA9685
import board
import busio

# ===============================
# SETUP I2C + PCA9685
# ===============================

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # 50Hz for ESC

ESC_CHANNEL = 0

# ===============================
# HELPER FUNCTION
# ===============================

def microseconds_to_duty_cycle(microseconds):
    # PCA9685 is 16-bit (0–65535)
    pulse_length = 1_000_000 / 50  # period in µs (50Hz)
    duty_cycle = int((microseconds / pulse_length) * 65535)
    return duty_cycle

def set_esc_pulse(microseconds):
    duty = microseconds_to_duty_cycle(microseconds)
    pca.channels[ESC_CHANNEL].duty_cycle = duty
    print(f"Sent {microseconds} µs")

# ===============================
# TEST SEQUENCE
# ===============================

print("Initializing ESC...")

# Neutral (important for ESC arming)
set_esc_pulse(1500)
time.sleep(3)

print("Forward test")
set_esc_pulse(2000)
time.sleep(2)

print("Back to neutral")
set_esc_pulse(1500)
time.sleep(2)

print("Reverse test")
set_esc_pulse(1000)
time.sleep(2)

print("Stopping")
set_esc_pulse(1500)

pca.deinit()
