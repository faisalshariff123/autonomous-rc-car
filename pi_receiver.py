import socket, time
import board, busio, adafruit_pca9685

i2c = busio.I2C(board.SCL, board.SDA)
pwm = adafruit_pca9685.PCA9685(i2c)
pwm.frequency = 50

def us_to_duty(us):
    return int((us / 20000.0) * 65535)

NEUTRAL_DR      = us_to_duty(1500)
NEUTRAL_ST = us_to_duty(1600) # put in 1600 as the neutral value isntead of 1500  due to servo not being centered for some reason at 1500
STEER_LEFT   = us_to_duty(2000)
STEER_RIGHT  = us_to_duty(1000)
THROTTLE_FWD = us_to_duty(2000)
THROTTLE_REV = us_to_duty(1300)
STEER_CH, THROTTLE_CH = 0, 1

# Arm ESC
pwm.channels[STEER_CH].duty_cycle    = NEUTRAL_ST
pwm.channels[THROTTLE_CH].duty_cycle = NEUTRAL_DR
time.sleep(2)
print("Armed!")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))

log = open('dataset.csv', 'w')
log.write('timestamp,steering,throttle\n')

while True:
    data, _ = sock.recvfrom(64)
    cmd = data.decode().strip()
    steer_cmd, throttle_cmd = cmd.split(",")

    steering = NEUTRAL_ST
    throttle  = NEUTRAL_DR

    if steer_cmd   == "L": steering = STEER_LEFT
    elif steer_cmd == "R": steering = STEER_RIGHT
    if throttle_cmd == "F": throttle = THROTTLE_FWD
    elif throttle_cmd == "B": throttle = THROTTLE_REV

    pwm.channels[STEER_CH].duty_cycle    = steering
    pwm.channels[THROTTLE_CH].duty_cycle = throttle
    log.write(f'{time.time()},{steering},{throttle}\n')
    log.flush()
