import socket
import struct
import time

PI_IP = "192.168.1.179"
PI_PORT = 5555

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1500, arm=1000):
    data = struct.pack('<5H', roll, pitch, throttle, yaw, arm)
    sock.sendto(data, (PI_IP, PI_PORT))
    print(f"Sent: R={roll:4d} P={pitch:4d} T={throttle:4d} Y={yaw:4d} A={arm:4d}  ({len(data)} bytes)")

try:
    print("Testing RC connection to Pi\n")
    
    # Test 1: Neutral, disarmed
    print("1. Neutral + disarmed (should see R/P/Y=1500, T=1000)")
    for _ in range(5):
        send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1500, arm=1000)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Test 2: Roll right, disarmed
    print("\n2. Roll right + disarmed (should see R=1800, P/Y=1500)")
    for _ in range(5):
        send_rc(roll=1800, pitch=1500, throttle=1000, yaw=1500, arm=1000)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Test 3: Pitch forward, disarmed
    print("\n3. Pitch forward + disarmed (should see P=1200, R/Y=1500)")
    for _ in range(5):
        send_rc(roll=1500, pitch=1200, throttle=1000, yaw=1500, arm=1000)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Test 4: Yaw left, disarmed
    print("\n4. Yaw left + disarmed (should see Y=1200, R/P=1500)")
    for _ in range(5):
        send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1200, arm=1000)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Test 5: Arm signal only
    print("\n5. Arm signal (should see A=1800, rest neutral)")
    for _ in range(5):
        send_rc(roll=1500, pitch=1500, throttle=1000, yaw=1500, arm=1800)
        time.sleep(0.1)
    time.sleep(0.5)
    
    # Test 6: Throttle ramp while armed
    print("\n6. Throttle ramp + armed (should see T go 1000→1200, A=1800)")
    for t in range(1000, 1201, 50):
        send_rc(roll=1500, pitch=1500, throttle=t, yaw=1500, arm=1800)
        time.sleep(0.1)
    
    print("\n✓ Test complete\n")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    sock.close()
