from flight_controller import FlightController
import socket
import struct
import time
import threading
import signal
import sys

class DroneBridge:
    def __init__(self, listen_port=5555):
        self.fc = FlightController()
        self.listen_port = listen_port
        self.sock = None
        self.running = False
        self.last_packet_time = 0
        self.packet_count = 0
        self.WATCHDOG_TIMEOUT = 0.5
        
        self.network_thread = None
        self.watchdog_thread = None
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\nShutdown signal received")
        self.stop()
        sys.exit(0)
    
    def connect_fc(self):
        return self.fc.connect()
    
    def start_network(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('0.0.0.0', self.listen_port))
            self.sock.settimeout(0.1)
            print(f"Listening on UDP port {self.listen_port}")
            return True
        except Exception as e:
            print(f"Failed to start network: {e}")
            return False
    
    def _network_loop(self):
        print("Network receive loop started")
        
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                
                if len(data) == 10:
                    roll, pitch, throttle, yaw, arm = struct.unpack('<5H', data)
                    
                    self.fc.set_roll(roll)
                    self.fc.set_pitch(pitch)
                    self.fc.set_throttle(throttle)
                    self.fc.set_yaw(yaw)
                    self.fc.set_channel(self.fc.AUX1, arm)
                    
                    self.last_packet_time = time.time()
                    self.packet_count += 1
                    
                    if self.packet_count % 50 == 0:
                        status = "ARMED" if arm > 1500 else "disarmed"
                        print(f"[{status}] R:{roll:4d} P:{pitch:4d} T:{throttle:4d} Y:{yaw:4d}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Network error: {e}")
        
        print("Network loop stopped")
    
    def _watchdog_loop(self):
        print("Watchdog started")
        
        while self.running:
            time.sleep(0.1)
            
            if self.last_packet_time > 0:
                timeout = time.time() - self.last_packet_time
                
                if timeout > self.WATCHDOG_TIMEOUT:
                    print(f"\nWATCHDOG: No packets for {timeout:.1f}s - FAILSAFE!")
                    
                    self.fc.set_roll(1500)
                    self.fc.set_pitch(1500)
                    self.fc.set_throttle(1000)
                    self.fc.set_yaw(1500)
                    self.fc.disarm()
                    
                    self.last_packet_time = 0
                    print("Waiting for connection to resume...")
        
        print("Watchdog stopped")
    
    def start(self):
        if not self.running:
            self.running = True
            self.last_packet_time = 0
            
            self.fc.start()
            
            self.network_thread = threading.Thread(target=self._network_loop, daemon=True)
            self.network_thread.start()
            
            self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            self.watchdog_thread.start()
            
            print("Bridge started - waiting for commands from Mac...")
    
    def stop(self):
        if self.running:
            print("\nStopping bridge...")
            self.running = False
            
            self.fc.disarm()
            time.sleep(0.2)
            self.fc.stop()
            
            if self.network_thread:
                self.network_thread.join(timeout=1.0)
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=1.0)
            
            print("Bridge stopped")
    
    def disconnect(self):
        self.stop()
        if self.sock:
            self.sock.close()
        print("Disconnected")
    
    def run(self):
        print("\n" + "="*60)
        print("DRONE BRIDGE (Raspberry Pi)")
        print("="*60)
        print("\nWaiting for commands from Mac...")
        print("Ctrl+C to stop\n")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped by user")


def main():
    bridge = DroneBridge(listen_port=5555)
    
    print("Starting Drone Bridge on Raspberry Pi...")
    
    if not bridge.connect_fc():
        print("\nCannot start without FC connection")
        return
    
    if not bridge.start_network():
        print("\nCannot start network server")
        return
    
    try:
        import subprocess
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip = result.stdout.strip().split()[0]
        print(f"\nPi IP address: {ip}")
        print(f"On Mac, connect to: {ip}:5555\n")
    except:
        pass
    
    bridge.start()
    bridge.run()
    bridge.disconnect()
    print("\nShutdown complete")


if __name__ == "__main__":
    main()
