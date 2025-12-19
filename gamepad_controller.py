# gamepad_controller.py
import socket
import struct
import time
import threading
import pygame

"""try:
    import pygame
except ImportError:
    print("Installing pygame")
    import subprocess
    subprocess.check_call(['pip3', 'install', 'pygame'])
    import pygame"""

# cChange these
PI_IP = "192.168.1.179"  
PI_PORT = 5555

class GamepadController:
    def __init__(self, pi_ip, pi_port):
        self.pi_ip = pi_ip
        self.pi_port = pi_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        pygame.init()
        pygame.joystick.init()
        
        # Find gamepad
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
            print("No gamepad found")
            exit(1)
        
        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        print(f"Found gamepad: {self.joy.get_name()}")
        
        self.running = True
        self.armed = False
    
    def send_rc(self, roll=1500, pitch=1500, throttle=1000, yaw=1500, arm=1000):
        data = struct.pack('<5H', int(roll), int(pitch), int(throttle), int(yaw), int(arm))
        self.sock.sendto(data, (self.pi_ip, self.pi_port))
    
    def map_analog(self, value, center=1500, min_val=1000, max_val=2000):
        # Map joystick axis (-1.0 to 1.0) to RC range (1000-2000)
        return center + (value * (max_val - center))
    
    def run(self):
        clock = pygame.time.Clock()
        
        print("\nGamepad Controls:")
        print("  Right Stick: Throttle (up) and Yaw (left/right)")
        print("  Left Stick:  Roll (left/right) and Pitch (up/down)")
        print("  A Button:    Arm/Disarm")
        print("  B Button:    Exit\n")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0:  # A button
                        self.armed = not self.armed
                        print(f"{'ARMED' if self.armed else 'DISARMED'}")
                    elif event.button == 1:  # B button
                        print("Exiting...")
                        self.running = False
            
            # Read analog sticks
            # Left stick: Roll (axis 0), Pitch (axis 1)
            # Right stick: Yaw (axis 2), Throttle (axis 3)
            
            roll_axis = self.joy.get_axis(0)  # -1 to 1
            pitch_axis = -self.joy.get_axis(1)  # Invert so up is negative
            yaw_axis = self.joy.get_axis(2)
            throttle_axis = -self.joy.get_axis(3)  # Invert so up is negative
            
            # Map to RC values (1000-2000, center 1500)
            roll = self.map_analog(roll_axis, center=1500, min_val=1000, max_val=2000)
            pitch = self.map_analog(pitch_axis, center=1500, min_val=1000, max_val=2000)
            yaw = self.map_analog(yaw_axis, center=1500, min_val=1000, max_val=2000)
            throttle = self.map_analog(throttle_axis, center=1000, min_val=1000, max_val=2000)
            
            arm = 1800 if self.armed else 1000
            
            self.send_rc(roll, pitch, throttle, yaw, arm)
            
           
            print(f"\rR:{roll:5.0f} P:{pitch:5.0f} T:{throttle:5.0f} Y:{yaw:5.0f} {'[ARMED]' if self.armed else '[disarmed]'}", end='', flush=True)
            
            clock.tick(50)  # 50Hz
        
        pygame.quit()
        self.sock.close()

if __name__ == "__main__":
    controller = GamepadController(PI_IP, PI_PORT)
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nShutdown")
    except Exception:
        print(f"\n An error occured:{Exception}")
