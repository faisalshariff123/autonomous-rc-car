import serial
import struct
import time
import threading

class FlightController:
    MSP_HEADER = b'$M<'
    MSP_SET_RAW_RC = 200
    MSP_RC = 105
    
    ROLL = 0
    PITCH = 1
    THROTTLE = 2
    YAW = 3
    AUX1 = 4
    
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        self.channels = [1500, 1500, 1000, 1500] + [1000] * 12

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(2)
            print(f"[FC] Connected to {self.port}")
            return True
        except Exception as e:
            print(f"[FC] Connection Failed: {e}")
            return False

    def start(self):
        if not self.ser:
            print("[FC] Not connected.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        print("[FC] Control loop started (50Hz)")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        if self.ser and self.ser.is_open:
            self.ser.close()
        print("[FC] Disconnected")

    def set_channel(self, index, value):
        value = max(1000, min(2000, int(value)))
        with self.lock:
            if 0 <= index < len(self.channels):
                self.channels[index] = value

    def set_throttle(self, value):
        self.set_channel(self.THROTTLE, value)

    def set_yaw(self, value):
        self.set_channel(self.YAW, value)

    def set_pitch(self, value):
        self.set_channel(self.PITCH, value)

    def set_roll(self, value):
        self.set_channel(self.ROLL, value)
        
    def arm(self):
        print("[FC] Arming...")
        self.set_channel(self.AUX1, 1800)
        
    def disarm(self):
        print("[FC] Disarming...")
        self.set_channel(self.AUX1, 1000)
        self.set_throttle(1000)

    def _checksum(self, data):
        xor = 0
        for b in data: xor ^= b
        return xor

    def _send_packet(self, cmd, payload):
        size = len(payload)
        pkt_data = bytes([size, cmd]) + payload
        checksum = self._checksum(pkt_data)
        packet = self.MSP_HEADER + pkt_data + bytes([checksum])
        try:
            self.ser.write(packet)
        except serial.SerialException:
            pass

    def _update_loop(self):
        while self.running:
            start_time = time.time()
            with self.lock:
                payload = struct.pack('<16H', *self.channels)
            self._send_packet(self.MSP_SET_RAW_RC, payload)
            elapsed = time.time() - start_time
            sleep_time = max(0, 0.02 - elapsed)
            time.sleep(sleep_time)

if __name__ == "__main__":
    fc = FlightController()
    if fc.connect():
        try:
            fc.start()
            
            fc.set_throttle(1000)
            fc.disarm()
            time.sleep(1)

            print("Test: Ramping Throttle...")
            for t in range(1000, 1500, 10):
                fc.set_throttle(t)
                time.sleep(0.05)
                
            print("Test: Holding 1500...")
            time.sleep(1)
            
            print("Test: Lowering Throttle...")
            fc.set_throttle(1000)
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("Interrupted!")
        finally:
            fc.stop()
