#!/usr/bin/env python3
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

PWM_FREQ = 50          # Hz
ESC_CHANNEL = 1        # PCA9685 channel for the ESC signal

FULL_REVERSE_US = 1000
NEUTRAL_US = 1500
FULL_FORWARD_US = 2000


def us_to_duty_cycle(pulse_us: int, freq_hz: int = PWM_FREQ) -> int:
    period_us = 1_000_000 / freq_hz
    duty_fraction = pulse_us / period_us
    return int(duty_fraction * 0xFFFF)


def set_pulse(pca: PCA9685, channel: int, pulse_us: int) -> None:
    pca.channels[channel].duty_cycle = us_to_duty_cycle(pulse_us)


def calibrate_esc(pca: PCA9685) -> None:
    print("=== ESC CALIBRATION ===")
    print("Make sure wheels are off the ground.")
    time.sleep(2)

    # Many Hobbywing car ESCs use: full throttle -> full reverse -> neutral to learn endpoints
    print("1) Sending NEUTRAL...")
    set_pulse(pca, ESC_CHANNEL, NEUTRAL_US)
    time.sleep(2)

    print("2) Sending FULL THROTTLE...")
    set_pulse(pca, ESC_CHANNEL, FULL_FORWARD_US)
    time.sleep(2)

    print("3) Sending REVERSE...")
    set_pulse(pca, ESC_CHANNEL, FULL_REVERSE_US)
    time.sleep(2)

    print("Calibration sequence complete. ESC should beep and arm at neutral.")


def main() -> None:
    i2c = busio.I2C(SCL, SDA)
    pca = PCA9685(i2c, address=0x40)  # confirmed by i2cdetect

    print("Setting PCA9685 frequency to 50 Hz...")
    pca.frequency = PWM_FREQ

    try:
        calibrate_esc(pca)
    finally:
        # Always leave ESC at neutral and clean up
        set_pulse(pca, ESC_CHANNEL, NEUTRAL_US)
        pca.deinit()
        print("PCA9685 deinitialized, ESC set to neutral.")


if __name__ == "__main__":
    main()
