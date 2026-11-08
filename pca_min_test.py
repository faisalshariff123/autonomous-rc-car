import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c, address=0x40)  # we know 0x40 from i2cdetect

print("Setting frequency...")
pca.frequency = 50

print("Sweeping duty on channel 0...")
ch = pca.channels[0]
for dc in (0x0000, 0x4000, 0x8000, 0xC000, 0xFFFF):
    ch.duty_cycle = dc
    print(hex(dc))
    time.sleep(0.5)

pca.deinit()
print("Done.")
