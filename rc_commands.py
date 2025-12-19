import socket
import struct
import time

# change these
PI_IP = "192.168.1.179"  # Replace with ur Pi's IP
PI_PORT = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1500, arm=1000):
    #Send RC values to Pi
    data = struct.pack('<5H', roll, pitch, throttle, yaw, arm)
    sock.sendto(data, (PI_IP, PI_PORT))
    print(f"Sent: R={roll} P={pitch} T={throttle} Y={yaw} ARM={arm}")

try:
    print("Testing RC connection to Pi")
    
    # Test 1: Disarmed, low throttle
    print("\n1. Disarmed (low throttle)")
    for _ in range(10):
        send_rc(throttle=1000, arm=1000)
        time.sleep(0.1)
    
    # Test 2: Arm
    print("\n2. Arming")
    for _ in range(10):
        send_rc(throttle=1000, arm=1800)
        time.sleep(0.1)
    
    # Test 3: Throttle ramp
    print("\n3. Ramping throttle :o")
    for t in range(1000, 1500, 50):
        send_rc(throttle=t, arm=1800)
        time.sleep(0.1)
    
    # Test 4: Lower throttle
    print("\n4. Lowering throttle")
    for t in range(1500, 1000, -50):
        send_rc(throttle=t, arm=1800)
        time.sleep(0.1)
    
    # Test 5: Disarm
    print("\n5. Disarming")
    for _ in range(10):
        send_rc(throttle=1000, arm=1000)
        time.sleep(0.1)
    
    print("\nTest complete")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()
