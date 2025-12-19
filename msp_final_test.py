import serial, struct, time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
time.sleep(2)

def send_msp(cmd, payload):
    data = bytes([len(payload), cmd]) + payload
    xor = 0
    for b in data: xor ^= b
    pkt = b'$M<' + data + bytes([xor])
    ser.write(pkt)

def read_response():
    ser.reset_input_buffer()
    send_msp(105, b'')
    time.sleep(0.1)
    if ser.in_waiting:
        return ser.read(ser.in_waiting)
    return b''

print("Sending Throttle 1800 (CORRECT ORDER)...")
for _ in range(50):
    # Order: Roll, Pitch, THROTTLE, YAW (CORRECT!)
    payload = struct.pack('<8H', 1500, 1500, 1800, 1500, 1000, 1000, 1000, 1000)
    send_msp(200, payload)
    time.sleep(0.02)

resp = read_response()
print(f"Hex Response: {resp.hex()}")
print("\nLooking for '0807' in position 3 (bytes 12-13)...")
