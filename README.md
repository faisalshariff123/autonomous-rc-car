# Pi-Betaflight WiFi Control System — Complete Technical Deep Dive

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Networking Layer](#networking-layer)
3. [Serial Communication & MSP Protocol](#serial-communication--msp-protocol)
4. [Flight Controller (flight_controller.py)](#flight_controllerpydetailed-breakdown)
5. [Bridge Server (drone_bridge.py)](#drone_bridgepydetailed-breakdown)
6. [Gamepad Controller (gamepad_controller.py)](#gamepad_controllerpydetailed-breakdown)
7. [Data Flow Examples](#data-flow-examples)
8. [Failsafe & Safety Mechanisms](#failsafe--safety-mechanisms)

---

## System Architecture Overview

Your drone control system has **three layers**:

```
┌─────────────────────────────────────────────────────────┐
│ LAYER 1: INPUT (Mac + Gamepad)                          │
│ gamepad_controller.py reads joystick axes,              │
│ converts to RC values (1000-2000), sends UDP packets    │
└─────────────────────────────────────────────────────────┘
                          ↓ WiFi UDP
                    192.168.1.179:5555
                          ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 2: BRIDGE (Raspberry Pi Zero 2W)                  │
│ drone_bridge.py listens on UDP port 5555,               │
│ unpacks RC values, forwards to flight_controller.py     │
└─────────────────────────────────────────────────────────┘
                          ↓ USB Serial
                    /dev/ttyACM0 (115200 baud)
                          ↓
┌─────────────────────────────────────────────────────────┐
│ LAYER 3: FLIGHT CONTROLLER (HAKRC F405 V2)             │
│ Betaflight FC receives MSP commands,                    │
│ updates motor speeds via ESCs (via PWM/DShot)           │
└─────────────────────────────────────────────────────────┘
```

**Why this architecture?**
- **Separation of concerns:** Input, bridge, FC are independent
- **Flexibility:** You can swap gamepad for keyboard, or UDP for TCP, without touching FC code
- **Failsafe:** The bridge watches for dropped packets; if none arrive for 0.5s, it disarms

---

## Networking Layer

### UDP Protocol Fundamentals

**What is UDP?**
- **U**ser **D**atagram **P**rotocol — a connectionless protocol (vs. TCP which is connection-oriented)
- **Fire and forget:** Send a packet, don't wait for confirmation
- **Fast but unreliable:** No guarantee packet arrives, but very low latency
- **Perfect for drones:** We don't care if packet #42 gets lost; we only care about the latest stick position

**Your packet structure:**
```
Byte Layout (10 bytes total):
[0-1]   Roll (unsigned short, little-endian) = 1000-2000
[2-3]   Pitch (unsigned short, little-endian) = 1000-2000
[4-5]   Throttle (unsigned short, little-endian) = 1000-2000
[6-7]   Yaw (unsigned short, little-endian) = 1000-2000
[8-9]   Arm (unsigned short, little-endian) = 1000 (disarmed) or 1800 (armed)
```

**Example hex dump:**
```
Mac sends: Roll=1500, Pitch=1500, Throttle=1000, Yaw=1500, Arm=1000

In binary (little-endian):
Roll:     1500 = 0x05DC → bytes: DC 05
Pitch:    1500 = 0x05DC → bytes: DC 05
Throttle: 1000 = 0x03E8 → bytes: E8 03
Yaw:      1500 = 0x05DC → bytes: DC 05
Arm:      1000 = 0x03E8 → bytes: E8 03

Full packet: [DC 05 DC 05 E8 03 DC 05 E8 03]
```

**Why little-endian?**
- Modern CPUs (x86, ARM) are little-endian: least-significant byte comes first
- `struct.pack('<5H', ...)` the `'<'` means "little-endian"
- If you used `'>'` (big-endian), 1500 would become 1277 on the Pi!

### UDP Socket Creation (drone_bridge.py excerpt)

```python
self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
self.sock.bind(('0.0.0.0', self.listen_port))
self.sock.settimeout(0.1)
```

**Breakdown:**
- `AF_INET` → IPv4 (not IPv6)
- `SOCK_DGRAM` → UDP datagram (not `SOCK_STREAM` which is TCP)
- `bind(('0.0.0.0', 5555))` → Listen on all interfaces, port 5555
  - `0.0.0.0` means "any IP address on this machine"
  - Allows you to send from any IP (Mac, phone, etc.)
- `settimeout(0.1)` → Don't block forever waiting for packets
  - If no packet arrives in 100ms, raise `socket.timeout` exception
  - This allows the watchdog to check if connection is dead

---

## Serial Communication & MSP Protocol

### What is MSP?

**MSP** = **MultiWii Serial Protocol**
- Betaflight's native protocol for communicating over USB/UART
- Structured binary format (not ASCII)
- Request-Response model (though we only send, don't wait for responses)

### MSP Packet Structure

Every MSP message follows this format:

```
Byte 0-1:   Header "$M"  (always 0x24 0x4D in ASCII)
Byte 2:     Direction '<' (0x3C) = to FC, '>' (0x3E) = from FC
Byte 3:     Payload Size (number of bytes in Data section)
Byte 4:     Command ID (what do you want to do?)
Byte 5...N: Data (payload, command-specific)
Byte N+1:   Checksum (XOR of all bytes from size to last data byte)
```

**Example: Send MSP_SET_RAW_RC to set 8 channels**

```python
# We want to set: R=1500, P=1500, T=1000, Y=1500, Aux1=1800, rest=1000

Byte 0-1:   Header = "$M" = 0x24 0x4D
Byte 2:     Direction = '<' = 0x3C (to FC)
Byte 3:     Size = 16 (8 channels × 2 bytes each)
Byte 4:     Command = 200 (MSP_SET_RAW_RC)
Byte 5-6:   Channel 0 (Roll) = 1500 = 0xDC05 → [0xDC, 0x05]
Byte 7-8:   Channel 1 (Pitch) = 1500 = 0xDC05 → [0xDC, 0x05]
Byte 9-10:  Channel 2 (Throttle) = 1000 = 0xE803 → [0xE8, 0x03]
Byte 11-12: Channel 3 (Yaw) = 1500 = 0xDC05 → [0xDC, 0x05]
Byte 13-14: Channel 4 (Aux1 ARM) = 1800 = 0x08,0x07 → [0x08, 0x07]
Byte 15-16: Channel 5 = 1000 = 0xE803 → [0xE8, 0x03]
Byte 17-18: Channel 6 = 1000 = 0xE803 → [0xE8, 0x03]
Byte 19-20: Channel 7 = 1000 = 0xE803 → [0xE8, 0x03]
Byte 21:    Checksum = XOR(Size, Cmd, Ch0_L, Ch0_H, ..., Ch7_H)
```

### Checksum Calculation

```python
def calculate_checksum(size, cmd, data):
    checksum = size ^ cmd  # XOR all bytes
    for byte in data:
        checksum ^= byte
    return checksum
```

**Why XOR?**
- Self-inverse: `a ^ b ^ b = a` (if any bit flips, checksum breaks)
- Simple CRC alternative for low-bandwidth protocols
- Detects single-bit errors

---

## flight_controller.py — Detailed Breakdown

This script runs **on the Raspberry Pi** and manages the physical connection to the Flight Controller.

### Full Script with Annotations

```python
import serial
import struct
import time
import threading

class FlightController:
    """
    Manages USB serial connection to HAKRC F405 V2 Betaflight FC.
    Sends MSP commands to update stick positions in real-time.
    """
    
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        """
        Initialize the FC connection (but don't open it yet).
        
        Args:
            port: USB serial port (/dev/ttyACM0 on Linux, /dev/cu.* on Mac)
            baudrate: 115200 is standard for Betaflight
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.running = False
        
        # Storage for current stick values
        # Channels: 0=Roll, 1=Pitch, 2=Throttle, 3=Yaw, 4=Aux1, 5-7=Aux
        self.channels = [1500, 1500, 1000, 1500, 1000, 1000, 1000, 1000]
        
        # Control loop state
        self.control_thread = None
        self.update_ready = threading.Event()  # Signals when new data arrived
    
    def connect(self):
        """
        Open the serial port and verify FC is responding.
        
        Returns:
            True if connected, False if failed
        """
        try:
            # Open USB serial connection
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(0.5)  # Wait for FC to initialize (critical!)
            
            # Send an MSP command to verify connection
            # MSP_API_VERSION (cmd=1) is a safe read-only query
            self.request_api_version()
            
            print(f"[FC] Connected to {self.port} at {self.baudrate} baud")
            return True
            
        except Exception as e:
            print(f"[FC] Failed to connect: {e}")
            return False
    
    def request_api_version(self):
        """
        Send MSP_API_VERSION (cmd 1) to verify FC responds.
        This is non-critical but helps confirm communication.
        """
        try:
            # Build MSP packet for API_VERSION
            cmd = 1
            payload = b''  # No payload needed for read commands
            packet = self._build_msp_packet(cmd, payload)
            self.serial.write(packet)
            
            # Try to read response (don't wait too long)
            response = self.serial.read(100)
            if response and b'$M' in response:
                print("[FC] API check passed")
            
        except Exception as e:
            print(f"[FC] API check warning: {e}")
    
    def _build_msp_packet(self, cmd, data):
        """
        Build a complete MSP packet for transmission.
        
        Formula:
            Header (2) + Direction (1) + Size (1) + Cmd (1) + Data (n) + Checksum (1)
        
        Args:
            cmd: MSP command ID (1-255)
            data: Payload bytes (empty for read, populated for write)
        
        Returns:
            bytes: Complete packet ready to send
        """
        size = len(data)
        
        # Calculate checksum: XOR of (size ^ cmd ^ all_data_bytes)
        checksum = size ^ cmd
        for byte in data:
            checksum ^= byte
        
        # Assemble packet: $M < size cmd data checksum
        packet = b'$M'  # Header
        packet += b'<'  # Direction (to FC)
        packet += bytes([size])  # Payload size
        packet += bytes([cmd])  # Command ID
        packet += data  # Payload
        packet += bytes([checksum])  # Checksum
        
        return packet
    
    def _build_raw_rc_packet(self, channels):
        """
        Build MSP_SET_RAW_RC packet (cmd 200).
        This is THE critical function for controlling the drone.
        
        Args:
            channels: List of 8 channel values [Roll, Pitch, Throttle, Yaw, Aux1, Aux2, Aux3, Aux4]
                     Each value: 1000-2000 (PWM microseconds)
        
        Returns:
            bytes: Complete MSP packet
        """
        # Pack 8 channels as unsigned shorts (little-endian)
        # '<8H' means: little-endian, 8 unsigned shorts
        data = struct.pack('<8H', *channels)
        
        # Now build MSP wrapper around this data
        cmd = 200  # MSP_SET_RAW_RC
        size = len(data)  # Should be 16
        
        checksum = size ^ cmd
        for byte in data:
            checksum ^= byte
        
        packet = b'$M<'
        packet += bytes([size, cmd])
        packet += data
        packet += bytes([checksum])
        
        return packet
    
    def set_roll(self, value):
        """Set channel 0 (Roll). Value: 1000-2000."""
        self.channels[0] = max(1000, min(2000, value))
    
    def set_pitch(self, value):
        """Set channel 1 (Pitch). Value: 1000-2000."""
        self.channels[1] = max(1000, min(2000, value))
    
    def set_throttle(self, value):
        """Set channel 2 (Throttle). Value: 1000-2000."""
        self.channels[2] = max(1000, min(2000, value))
    
    def set_yaw(self, value):
        """Set channel 3 (Yaw). Value: 1000-2000."""
        self.channels[3] = max(1000, min(2000, value))
    
    def set_channel(self, channel_num, value):
        """Set arbitrary channel (0-7). Value: 1000-2000."""
        if 0 <= channel_num < 8:
            self.channels[channel_num] = max(1000, min(2000, value))
    
    def disarm(self):
        """Safety function: Set Aux1 to 1000 (disarmed)."""
        self.channels[4] = 1000  # Aux1 = 1000 = disarmed
    
    def start(self):
        """
        Start the 50Hz control loop in a background thread.
        """
        if not self.running:
            self.running = True
            
            # Launch control thread
            self.control_thread = threading.Thread(
                target=self._control_loop,
                daemon=True
            )
            self.control_thread.start()
    
    def _control_loop(self):
        """
        Send MSP_SET_RAW_RC commands at 50Hz in a background thread.
        
        Why background thread?
            - Main thread (drone_bridge.py) needs to listen for UDP packets
            - Control loop can't block waiting for USB responses
            - Threading allows both to run concurrently
        """
        print("[FC] Control loop started (50Hz)")
        
        while self.running:
            try:
                # Build packet with current channel values
                packet = self._build_raw_rc_packet(self.channels)
                
                # Send to FC
                self.serial.write(packet)
                
                # 50Hz = 1 packet every 20ms
                time.sleep(0.02)
                
            except Exception as e:
                if self.running:
                    print(f"[FC] Control loop error: {e}")
    
    def stop(self):
        """Cleanly shut down FC connection."""
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        if self.serial:
            self.serial.close()
```

### Key Concepts Explained

**1. Threading Model**

```
Main Thread (drone_bridge.py)          Background Thread (_control_loop)
└─ Listen for UDP packets                └─ Send MSP commands at 50Hz
   ├─ Receive packet
   ├─ Call fc.set_roll(value)
   ├─ Call fc.set_pitch(value)          Meanwhile in background:
   └─ Return immediately                ├─ Read self.channels
                                        ├─ Build MSP packet
                                        ├─ Send via USB
                                        └─ Sleep 20ms
```

**Why this works:** The setters just update `self.channels[]` (fast), while the control loop continuously sends (no waiting).

**2. Struct Packing: `'<8H'`**

```python
struct.pack('<8H', 1500, 1500, 1000, 1500, 1000, 1000, 1000, 1000)
```

- `<` = Little-endian byte order
- `8H` = 8 unsigned short integers (2 bytes each)
- Input: 8 Python ints (1000-2000)
- Output: 16 binary bytes ready for MSP

**3. Why 50Hz?**
- Drones need **stable, continuous updates**
- 50Hz = 20ms interval = smooth control
- Too slow (10Hz) = jerky response
- Too fast (1000Hz) = wastes bandwidth, FC can't process that fast

---

## drone_bridge.py — Detailed Breakdown

This script runs **on the Raspberry Pi** and acts as the **bridge between WiFi (UDP) and USB (Serial)**.

### Full Script with Annotations

```python
#!/usr/bin/env python3
"""
Drone Bridge: WiFi UDP ↔ Flight Controller USB
Listens on UDP 5555, forwards commands to FC via flight_controller.py
"""

from flight_controller import FlightController
import socket
import struct
import time
import threading
import signal
import sys

class DroneBridge:
    """
    Acts as middleware:
    1. Listens for UDP packets from Mac
    2. Unpacks RC values
    3. Forwards to flight_controller.py
    4. Monitors connection with watchdog failsafe
    """
    
    def __init__(self, listen_port=5555):
        """
        Args:
            listen_port: UDP port to listen on (5555 is default)
        """
        # Flight controller instance
        self.fc = FlightController()
        
        # Network settings
        self.listen_port = listen_port
        self.sock = None
        self.running = False
        
        # Connection monitoring
        self.last_packet_time = 0  # Timestamp of last packet received
        self.packet_count = 0      # Total packets received (for logging)
        self.WATCHDOG_TIMEOUT = 0.5  # If no packet for 500ms, failsafe
        
        # Threads
        self.network_thread = None
        self.watchdog_thread = None
        
        # Signal handlers for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """
        Handle Ctrl+C gracefully.
        Ensures drone is disarmed before shutdown.
        """
        print("\nShutdown signal received")
        self.stop()
        sys.exit(0)
    
    def connect_fc(self):
        """
        Attempt to connect to flight controller.
        Returns: True if successful
        """
        return self.fc.connect()
    
    def start_network(self):
        """
        Initialize UDP socket and bind to port.
        
        Why 0.1s timeout?
            - Without timeout, recvfrom() blocks forever
            - 0.1s allows watchdog to check every 100ms
            - If packet hasn't arrived in 500ms, disarm
        
        Returns: True if socket created successfully
        """
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(('0.0.0.0', self.listen_port))
            self.sock.settimeout(0.1)  # Non-blocking with 100ms timeout
            print(f"Listening on UDP port {self.listen_port}")
            return True
        except Exception as e:
            print(f"Failed to start network: {e}")
            return False
    
    def _network_loop(self):
        """
        Main network receive loop (runs in background thread).
        
        Flow:
        1. Block on recvfrom() for up to 100ms
        2. If packet arrives:
           a. Unpack 10 bytes into 5 unsigned shorts
           b. Update FC channels
           c. Record timestamp for watchdog
        3. If timeout:
           a. Continue loop (watchdog checks connection)
        """
        print("Network receive loop started")
        
        while self.running:
            try:
                # Try to receive one packet
                # recvfrom(bufsize) returns (data, address)
                data, addr = self.sock.recvfrom(1024)
                
                # Only process if packet is exactly 10 bytes
                if len(data) == 10:
                    # Unpack: '<5H' = 5 unsigned shorts, little-endian
                    roll, pitch, throttle, yaw, arm = struct.unpack('<5H', data)
                    
                    # Update flight controller channels
                    self.fc.set_roll(roll)
                    self.fc.set_pitch(pitch)
                    self.fc.set_throttle(throttle)
                    self.fc.set_yaw(yaw)
                    self.fc.set_channel(4, arm)  # Channel 4 = Aux1 = ARM
                    
                    # Record when we received this packet
                    self.last_packet_time = time.time()
                    self.packet_count += 1
                    
                    # Log every 50th packet (at 50Hz, that's ~once per second)
                    if self.packet_count % 50 == 0:
                        status = "ARMED" if arm > 1500 else "disarmed"
                        print(f"[{status}] R:{roll:4d} P:{pitch:4d} T:{throttle:4d} Y:{yaw:4d}")
                
            except socket.timeout:
                # No packet in 100ms timeout — this is normal, continue
                continue
            except Exception as e:
                if self.running:
                    print(f"Network error: {e}")
        
        print("Network loop stopped")
    
    def _watchdog_loop(self):
        """
        Failsafe watchdog (runs in background thread).
        
        Purpose: If WiFi/packets stop arriving, disarm immediately.
        
        Scenario:
            - You're flying with arm=1800
            - WiFi drops (packet loss)
            - Watchdog detects 500ms of silence
            - Watchdog sets all channels to safe defaults
            - Drone disarms (aux1=1000)
            - Throttle = 1000 (idle)
            
        Why separate thread?
            - Watchdog must check independently of packet arrival
            - Network thread might be stuck waiting for packet
            - Watchdog runs every 100ms regardless
        """
        print("Watchdog started")
        
        while self.running:
            time.sleep(0.1)  # Check every 100ms
            
            # Only care if we've ever received a packet
            if self.last_packet_time > 0:
                # Calculate time since last packet
                timeout = time.time() - self.last_packet_time
                
                # Trigger failsafe if silent for 500ms
                if timeout > self.WATCHDOG_TIMEOUT:
                    print(f"\nWATCHDOG: No packets for {timeout:.1f}s - FAILSAFE!")
                    
                    # Force-set all channels to safe state
                    self.fc.set_roll(1500)      # Center
                    self.fc.set_pitch(1500)     # Center
                    self.fc.set_throttle(1000)  # Idle
                    self.fc.set_yaw(1500)       # Center
                    self.fc.disarm()            # Aux1 = 1000
                    
                    # Reset timer to avoid spamming messages
                    self.last_packet_time = 0
                    print("Waiting for connection to resume...")
        
        print("Watchdog stopped")
    
    def start(self):
        """
        Start both network and watchdog threads.
        """
        if not self.running:
            self.running = True
            self.last_packet_time = 0
            
            # Start FC control loop
            self.fc.start()
            
            # Start network thread
            self.network_thread = threading.Thread(
                target=self._network_loop,
                daemon=True
            )
            self.network_thread.start()
            
            # Start watchdog thread
            self.watchdog_thread = threading.Thread(
                target=self._watchdog_loop,
                daemon=True
            )
            self.watchdog_thread.start()
            
            print("Bridge started - waiting for commands from Mac...")
    
    def stop(self):
        """
        Cleanly shut down: disarm, stop threads, close connections.
        """
        if self.running:
            print("\nStopping bridge...")
            self.running = False
            
            # Force disarm before shutdown
            self.fc.disarm()
            time.sleep(0.2)
            
            # Stop FC
            self.fc.stop()
            
            # Wait for threads to finish
            if self.network_thread:
                self.network_thread.join(timeout=1.0)
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=1.0)
            
            print("Bridge stopped")
    
    def disconnect(self):
        """Final cleanup."""
        self.stop()
        if self.sock:
            self.sock.close()
        print("Disconnected")
    
    def run(self):
        """Main loop (mostly idle while threads do the work)."""
        print("\n" + "="*60)
        print("DRONE BRIDGE (Raspberry Pi)")
        print("="*60)
        print("\nWaiting for commands from Mac...")
        print("Ctrl+C to stop\n")
        
        try:
            while self.running:
                time.sleep(1)  # Just keep the main thread alive
        except KeyboardInterrupt:
            print("\nStopped by user")


def main():
    """Entry point."""
    bridge = DroneBridge(listen_port=5555)
    
    print("Starting Drone Bridge on Raspberry Pi...")
    
    # Connect to FC
    if not bridge.connect_fc():
        print("\nCannot start without FC connection")
        return
    
    # Start UDP listener
    if not bridge.start_network():
        print("\nCannot start network server")
        return
    
    # Print IP address for reference
    try:
        import subprocess
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip = result.stdout.strip().split()[0]
        print(f"\nPi IP address: {ip}")
        print(f"On Mac, connect to: {ip}:5555\n")
    except:
        pass
    
    # Start bridge
    bridge.start()
    bridge.run()
    bridge.disconnect()
    print("\nShutdown complete")


if __name__ == "__main__":
    main()
```

### Key Architectural Decisions

**1. Three-Thread Design**

```
Main Thread
├─ Orchestration
├─ Signal handling
└─ Keeps process alive

Network Thread
├─ Waits for UDP packets (blocking)
├─ Unpacks RC values
└─ Updates FC channels (fast operation)

Watchdog Thread
├─ Checks time since last packet every 100ms
├─ If silent > 500ms, triggers failsafe
└─ Runs independently (doesn't block on network)
```

**Why not just one thread?**
- Network thread can't check watchdog if stuck on `recvfrom()`
- Separate watchdog guarantees disarm happens even if WiFi drops
- Professional drone firmware does this exact pattern

**2. Struct Unpacking: `'<5H'`**

```python
roll, pitch, throttle, yaw, arm = struct.unpack('<5H', data)
```

- **Must match** gamepad_controller.py's `struct.pack('<5H', ...)`
- If one uses `'<5H'` and other uses `'>5H'`, values get swapped/corrupted
- 10 bytes → 5 unsigned shorts
- Little-endian ensures both Mac and Pi interpret bytes the same way

---

## gamepad_controller.py — Detailed Breakdown

This script runs **on your Mac** and sends joystick commands over WiFi.

### Full Script with Deep Annotations

```python
import socket
import struct
import time
import pygame

# Configuration (these could be command-line args)
PI_IP = "192.168.1.179"
PI_PORT = 5555

# Joystick axis mapping (CONFIRMED for your gamepad)
AXIS_ROLL     = 0  # Left Stick X (left = -1, right = +1)
AXIS_PITCH    = 1  # Left Stick Y (up = -1, down = +1)
AXIS_YAW      = 3  # Right Stick X (left = -1, right = +1)
AXIS_THROTTLE = 4  # Right Stick Y (up = -1, down = +1)

DEADZONE = 0.05  # Ignore joystick movements < 5% to prevent drift


class GamepadController:
    """
    Reads Xbox/PlayStation-style gamepad input.
    Converts joystick axes (-1 to +1) into RC PWM values (1000-2000).
    Sends UDP packets to Pi at 50Hz.
    """
    
    def __init__(self):
        """Initialize socket and pygame joystick."""
        # UDP socket (same as drone_bridge, but sender instead of receiver)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Pygame joystick
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("No gamepad found! Connect one via Bluetooth/USB.")
            exit(1)
        
        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        print(f"\n🎮 Connected: {self.joy.get_name()}")
        
        self.running = True
        self.armed = False
        
    def map_value(self, value, axis_type):
        """
        Convert joystick axis value (-1 to +1) into RC PWM (1000-2000).
        
        The math:
            - Joystick neutral = 0.0
            - Joystick left/up = -1.0
            - Joystick right/down = +1.0
            
            For Roll/Yaw (left-right):
                -1.0 (left) → 1000 (full left)
                 0.0 (center) → 1500 (center)
                +1.0 (right) → 2000 (full right)
                Formula: 1500 + (value * 500)
            
            For Throttle (up-down):
                -1.0 (up) → 2000 (full throttle)
                 0.0 (center) → 1500 (half throttle)
                +1.0 (down) → 1000 (idle)
                Formula: 1500 - (value * 500)
            
            For Pitch (up-down):
                -1.0 (up/forward) → 1000 (pitch forward = nose down in most conventions)
                 0.0 (center) → 1500 (center)
                +1.0 (down/back) → 2000 (pitch back = nose up)
                Formula: 1500 + (value * 500)
        
        Args:
            value: Joystick axis reading (-1.0 to +1.0)
            axis_type: 'throttle', 'pitch', or 'standard' (roll/yaw)
        
        Returns:
            int: PWM value (1000-2000)
        """
        # Apply deadzone: if movement is tiny, treat as zero (prevents drift)
        if abs(value) < DEADZONE:
            value = 0.0
        
        if axis_type == 'throttle':
            # Throttle: up (-1) → full (2000), down (+1) → idle (1000)
            # Formula: 1500 - (value * 500)
            return int(1500 - (value * 500))
        
        elif axis_type == 'pitch':
            # Pitch: up (-1) → 1000, down (+1) → 2000
            # Formula: 1500 + (value * 500)
            return int(1500 + (value * 500))
        
        else:  # 'standard' for roll/yaw
            # Roll/Yaw: left (-1) → 1000, right (+1) → 2000
            # Formula: 1500 + (value * 500)
            return int(1500 + (value * 500))
    
    def run(self):
        """
        Main loop: Read gamepad, send UDP packets at 50Hz.
        
        Flow each iteration:
        1. Check for button presses (A = arm/disarm)
        2. Read all 4 joystick axes
        3. Map to PWM values (1000-2000)
        4. Clamp to legal range
        5. Pack into binary struct
        6. Send UDP packet
        7. Print status
        8. Sleep 20ms (50Hz)
        """
        clock = pygame.time.Clock()
        
        print("Ready! Press 'A' to Arm.\n")
        
        try:
            while self.running:
                # ===== STEP 1: Handle Button Presses =====
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0:  # A Button (Xbox)
                            self.armed = not self.armed
                            if self.armed:
                                print("\n>>> ARMING REQUESTED <<<")
                            else:
                                print("\n>>> DISARMED <<<")
                        
                        if event.button == 1:  # B Button (Xbox)
                            self.running = False
                
                # ===== STEP 2: Read Joystick Axes =====
                # pygame.event.pump() is necessary to update joystick state
                pygame.event.pump()
                
                roll_val  = self.joy.get_axis(AXIS_ROLL)
                pitch_val = self.joy.get_axis(AXIS_PITCH)
                yaw_val   = self.joy.get_axis(AXIS_YAW)
                throt_val = self.joy.get_axis(AXIS_THROTTLE)
                
                # ===== STEP 3: Map to PWM Values =====
                roll = self.map_value(roll_val, 'standard')
                pitch = self.map_value(pitch_val, 'pitch')
                yaw = self.map_value(yaw_val, 'standard')
                throttle = self.map_value(throt_val, 'throttle')
                
                # ===== STEP 4: Safety Clamp (defensive programming) =====
                # Even though map_value should return 1000-2000,
                # always clamp to prevent FC from rejecting values
                roll = max(1000, min(2000, roll))
                pitch = max(1000, min(2000, pitch))
                yaw = max(1000, min(2000, yaw))
                throttle = max(1000, min(2000, throttle))
                
                # ===== STEP 5: Determine ARM Signal =====
                # Safety rule: Only send arm=1800 if:
                # 1. User pressed A button (self.armed == True)
                # 2. Throttle is below 1100 (safety lockout)
                
                real_arm_value = 1000  # Default: disarmed
                status_msg = "[DISARMED]"
                
                if self.armed:
                    if throttle > 1100:
                        # Safety violation: throttle too high to arm
                        status_msg = "⚠️ LOWER THROTTLE TO ARM! ⚠️"
                        real_arm_value = 1000  # Force disarm
                    else:
                        # Safe to send arm signal
                        status_msg = " [ARMED]  "
                        real_arm_value = 1800
                
                # ===== STEP 6: Pack Binary Struct =====
                # struct.pack('<5H', r, p, t, y, a)
                # '<' = little-endian
                # '5H' = 5 unsigned shorts
                # Result: 10 bytes ready to send
                data = struct.pack('<5H', roll, pitch, throttle, yaw, real_arm_value)
                
                # ===== STEP 7: Send UDP Packet =====
                self.sock.sendto(data, (PI_IP, PI_PORT))
                
                # ===== STEP 8: Print Status =====
                print(f"\r{status_msg} R:{roll:4} P:{pitch:4} T:{throttle:4} Y:{yaw:4}", end="")
                
                # ===== STEP 9: Maintain 50Hz Rate =====
                clock.tick(50)  # Sleep to achieve 50Hz (20ms per iteration)
        
        finally:
            # Cleanup
            self.sock.close()
            pygame.quit()
            print("\nConnection Closed.")


if __name__ == "__main__":
    GamepadController().run()
```

### Critical Insights

**1. Joystick Axis Mapping**

Your gamepad axes (confirmed by your testing):
```
Axis 0: Left Stick X (Roll)
Axis 1: Left Stick Y (Pitch)
Axis 3: Right Stick X (Yaw)
Axis 4: Right Stick Y (Throttle)
```

Why axis 2 is missing: Axis 2 is typically a trigger (L2/LT), which reads as a continuous value (-1 to +1).

**2. PWM Value Convention**

```
Standard RC Convention:
1000 µs = Minimum (full left, down, idle)
1500 µs = Center (neutral)
2000 µs = Maximum (full right, up, full throttle)

Your gamepad ranges:
-1.0 to +1.0

Mapping formula:
center_value + (joystick * range)

For roll: 1500 + (value * 500)  → 1000 to 2000 ✓
For throttle: 1500 - (value * 500)  → 1000 to 2000 ✓ (inverted!)
```

**3. Safety Lockout**

```python
if throttle > 1100:
    real_arm_value = 1000  # Force disarm
else:
    real_arm_value = 1800  # Safe to arm
```

This implements a **hardware-level safety feature**: Betaflight won't arm if throttle > ~1050. By checking in the gamepad script, you prevent sending bad commands at all.

---

## Data Flow Examples

### Example 1: Gentle Roll Right

**On Mac (gamepad_controller.py):**
```
User moves Left Stick right (position: +0.5)

AXIS_ROLL = 0
roll_val = joy.get_axis(0) = 0.5
roll = map_value(0.5, 'standard')
     = int(1500 + (0.5 * 500))
     = int(1500 + 250)
     = int(1750)
     = 1750

Packet: struct.pack('<5H', 1750, 1500, 1000, 1500, 1800)
Binary:  [56 06] [DC 05] [E8 03] [DC 05] [08 07]
         (1750)  (1500)  (1000)  (1500)  (1800)
```

**Over WiFi (UDP):**
- Mac sends 10 bytes to 192.168.1.179:5555

**On Pi (drone_bridge.py):**
```
socket.recvfrom(1024) → receives 10 bytes
struct.unpack('<5H', data)
  → (1750, 1500, 1000, 1500, 1800)

fc.set_roll(1750)
fc.set_pitch(1500)
fc.set_throttle(1000)
fc.set_yaw(1500)
fc.set_channel(4, 1800)  # ARM
```

**In Flight Controller (flight_controller.py):**
```
Background thread runs every 20ms:

self.channels = [1750, 1500, 1000, 1500, 1800, 1000, 1000, 1000]

_build_raw_rc_packet(self.channels)
  → struct.pack('<8H', 1750, 1500, 1000, 1500, 1800, 1000, 1000, 1000)
  → builds MSP packet with 8 channels

MSP_SET_RAW_RC command sent to FC over USB

FC receives MSP command:
  → Channel 0 (Roll) = 1750
  → FC applies correction: "I want right roll"
  → Increases right motor speed
  → Decreases left motor speed
  → Drone rolls right
```

### Example 2: Failsafe Triggered

**Scenario: WiFi drops while flying**

**At t=0ms:**
- Last packet received at time=0
- Everything normal

**At t=450ms:**
- No new packets (WiFi dead)
- last_packet_time still = 0
- Bridge still sending old commands (1750, 1500, 1000, 1500, 1800)

**At t=500ms:**
- Watchdog thread checks: `timeout = current_time - last_packet_time = 0.5s`
- Timeout > WATCHDOG_TIMEOUT (0.5s) → **TRIGGER FAILSAFE**

```python
fc.set_roll(1500)        # Center
fc.set_pitch(1500)       # Center
fc.set_throttle(1000)    # Idle
fc.set_yaw(1500)         # Center
fc.disarm()              # aux1 = 1000

# Next MSP packet has:
# channels = [1500, 1500, 1000, 1500, 1000, 1000, 1000, 1000]

# FC sees Aux1 = 1000 → DISARMED
# FC sees Throttle = 1000 → IDLE
# → Motors stop
```

**Why this works:**
- FC respects Aux1 value more than anything else
- Disarm immediately cuts motor commands
- Throttle at 1000 ensures even if motors spin, it's at minimum

---

## Failsafe & Safety Mechanisms

### Three Layers of Failsafe

**Layer 1: Watchdog (Application Level)**
```
Location: drone_bridge.py _watchdog_loop()
Triggers: No UDP packets for 500ms
Action: Force all channels to safe state, disarm
Response Time: ~100ms (checked every 100ms)
```

**Layer 2: Betaflight FC Safety (Firmware Level)**
```
Location: Inside FC hardware
Triggers: Multiple conditions:
  - Aux1 (ch4) < 1700 → Disarmed
  - Gyro detects crash
  - Accelerometer detects free-fall
Action: Motors stop
Response Time: Immediate (hardware)
```

**Layer 3: Throttle Safety (Gamepad Level)**
```
Location: gamepad_controller.py map_value()
Triggers: User tries to arm with throttle > 1100
Action: Don't send arm signal even if A button pressed
Response Time: Immediate (local)
Rationale: Prevents accidental armed-with-throttle scenario
```

### Full Failsafe Sequence

```
WiFi Drops
    ↓
Watchdog detects 500ms silence
    ↓
Watchdog forces:
  - Roll=1500, Pitch=1500, Yaw=1500
  - Throttle=1000
  - Aux1=1000 (DISARM)
    ↓
Next MSP packet (every 20ms) contains disarm signal
    ↓
FC sees Aux1=1000
    ↓
FC immediately:
  - Stops reading RC input
  - Stops sending PWM to motors
  - Motors coast to stop
```

**Why this is robust:**
- 3 independent layers (application, firmware, input)
- Even if one fails, others catch the problem
- No single point of failure
- Designed like real aircraft failsafes

---

## Summary: The Complete Picture

```
┌─────────────────────────────────────────────────────────┐
│ YOUR SYSTEM IN ONE DIAGRAM                              │
└─────────────────────────────────────────────────────────┘

Mac (gamepad_controller.py)
├─ Read: Joystick axes (-1 to +1)
├─ Calculate: Roll=1500+val*500, Pitch, Yaw, Throttle
├─ Pack: struct.pack('<5H', R, P, T, Y, ARM)
└─ Send: UDP to 192.168.1.179:5555

                    WiFi UDP
                        ↓
                    10 bytes

Raspberry Pi (drone_bridge.py)
├─ Receive: UDP packet
├─ Unpack: struct.unpack('<5H', data)
├─ Update: fc.set_roll(), fc.set_pitch(), etc.
└─ Watchdog: Check if packets arriving (disarm if silent)

                USB Serial /dev/ttyACM0
                    115200 baud
                        ↓

Flight Controller (flight_controller.py + FC hardware)
├─ Background Thread: Every 20ms:
│  ├─ Build MSP_SET_RAW_RC with 8 channels
│  ├─ Send to FC via USB
│  └─ Sleep 20ms
│
└─ FC Firmware (Betaflight):
   ├─ Receive MSP command
   ├─ Parse 8 channel values
   ├─ Check: Is Aux1 > 1700? (If no, stay disarmed)
   ├─ If armed: Apply PID control
   └─ Send PWM to ESCs → Motors spin
```

---

## Key Takeaways

1. **Struct packing is critical**: `'<5H'` on both sides, or values corrupt
2. **Threading is necessary**: Network blocks; FC sends continuously
3. **Failsafe is multi-layer**: Watchdog + FC safety + input validation
4. **MSP is a wrapper**: Binary format with header, checksum, checksum
5. **50Hz is the magic number**: Fast enough for smooth control, slow enough for reliable RF
6. **Joystick mapping is convention**: -1 to +1 → 1000 to 2000 PWM
7. **Threadsafety matters**: All three threads access `self.channels[]` concurrently (but that's okay since it's just reads/writes of ints)
