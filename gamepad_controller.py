import socket
import struct
import time
import pygame

# --- CONFIGURATION ---
PI_IP = "192.168.1.179"
PI_PORT = 5555

# CONFIRMED AXIS MAPPING (Based on your test)
AXIS_ROLL     = 0  # Left Stick X
AXIS_PITCH    = 1  # Left Stick Y
AXIS_YAW      = 3  # Right Stick X
AXIS_THROTTLE = 4  # Right Stick Y

# Deadzone to stop drift
DEADZONE = 0.05

class GamepadController:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            print("No gamepad found! Connect one via Bluetooth/USB.")
            exit(1)
        
        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        print(f"\n🎮 Connected: {self.joy.get_name()}")
        print(f"📡 Target: {PI_IP}:{PI_PORT}")
        print("---------------------------------------------------")
        print("Controls:")
        print("  Left Stick:  Pitch & Roll")
        print("  Right Stick: Throttle & Yaw")
        print("  [A] Button:  ARM / DISARM")
        print("  [B] Button:  Quit")
        print("---------------------------------------------------")
        print("⚠️  IMPORTANT: Hold Right Stick DOWN to Arm! ⚠️")
        print("---------------------------------------------------\n")
        
        self.running = True
        self.armed = False
        
    def map_value(self, value, axis_type):
        # Apply deadzone
        if abs(value) < DEADZONE:
            value = 0.0
            
        if axis_type == 'throttle':
            # Stick UP (-1) = 2000 (Full)
            # Stick CENTER (0) = 1500 (Half)
            # Stick DOWN (+1) = 1000 (Idle)
            # Formula: 1500 - (value * 500)
            return int(1500 - (value * 500))
        
        elif axis_type == 'pitch':
            # Stick UP (-1) = 1000 (Nose Down / Forward)
            # Stick DOWN (+1) = 2000 (Nose Up / Back)
            return int(1500 + (value * 500))
            
        else:
            # Roll/Yaw: Left (-1) = 1000, Right (+1) = 2000
            return int(1500 + (value * 500))

    def run(self):
        clock = pygame.time.Clock()
        
        try:
            while self.running:
                # 1. Process Buttons
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0: # A Button (Arm)
                            self.armed = not self.armed
                            if self.armed:
                                print("\n>>> ARMING REQUESTED <<<")
                            else:
                                print("\n>>> DISARMED <<<")
                                
                        if event.button == 1: # B Button (Quit)
                            self.running = False
                            
                # 2. Read Sticks
                roll_val  = self.joy.get_axis(AXIS_ROLL)
                pitch_val = self.joy.get_axis(AXIS_PITCH)
                yaw_val   = self.joy.get_axis(AXIS_YAW)
                throt_val = self.joy.get_axis(AXIS_THROTTLE)
                
                # 3. Map to MSP 1000-2000
                roll = self.map_value(roll_val, 'roll')
                pitch = self.map_value(pitch_val, 'pitch')
                yaw = self.map_value(yaw_val, 'yaw')
                throttle = self.map_value(throt_val, 'throttle')
                
                # 4. Handle Arming Logic
                # Betaflight safety: If throttle > 1050, it won't arm.
                # If we are "ARMED" locally, but throttle is high, warn the user.
                
                real_arm_value = 1000
                status_msg = "[DISARMED]"
                
                if self.armed:
                    if throttle > 1100:
                        # Safety Warning: Throttle too high to arm!
                        status_msg = "⚠️ LOWER THROTTLE TO ARM! ⚠️"
                        real_arm_value = 1000 # Force disarm for safety until stick is down
                    else:
                        status_msg = " [ARMED]  "
                        real_arm_value = 1800
                
                # 5. Send Packet
                data = struct.pack('<5H', roll, pitch, throttle, yaw, real_arm_value)
                self.sock.sendto(data, (PI_IP, PI_PORT))
                
                # 6. Print Status Line
                print(f"\r{status_msg} R:{roll:4} P:{pitch:4} T:{throttle:4} Y:{yaw:4}", end="")
                
                clock.tick(50) # 50Hz
                
        except KeyboardInterrupt:
            print("\nForce Quit")
        finally:
            self.sock.close()
            pygame.quit()
            print("\nConnection Closed.")

if __name__ == "__main__":
    GamepadController().run()
