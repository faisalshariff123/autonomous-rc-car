import socket
import struct
import time
import pygame

# --- CONFIGURATION ---
PI_IP = "x"
PI_PORT = 5555

# AXIS MAPPIN
AXIS_ROLL     = 0
AXIS_PITCH    = 1
AXIS_YAW      = 3
AXIS_THROTTLE = 4 

DEADZONE = 0.05

class GamepadController:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            print("No gamepad found!")
            exit(1)
        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        self.running = True
        self.armed = False
        
    def map_value(self, value, axis_type):
        if abs(value) < DEADZONE: value = 0.0
        if axis_type == 'throttle':
            return int(1500 - (value * 500)) # Up(-1)=2000, Down(+1)=1000
        elif axis_type == 'pitch':
            return int(1500 + (value * 500)) # Up(-1)=1000, Down(+1)=2000
        else:
            return int(1500 + (value * 500))

    def run(self):
        print("\nCONTROLLER READY")
        print("--------------------------------")
        print("  Hold Right Stick DOWN")
        print("  Press [A] to Arm")
        print("--------------------------------\n")
        
        # Initialize throttle so it exists for the first loop
        throttle = 1000 
        
        try:
            while self.running:
                # 1. READ STICKS FIRST (so we have current values)
                pygame.event.pump() # Force update
                
                roll = self.map_value(self.joy.get_axis(AXIS_ROLL), 'roll')
                pitch = self.map_value(self.joy.get_axis(AXIS_PITCH), 'pitch')
                yaw = self.map_value(self.joy.get_axis(AXIS_YAW), 'yaw')
                throttle = self.map_value(self.joy.get_axis(AXIS_THROTTLE), 'throttle')

                # 2. HANDLE BUTTONS
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 0: # A Button (Arm Toggle)
                            if self.armed:
                                self.armed = False
                                print("\n>>> DISARMED <<<")
                            else:
                                # ONLY CHECK THROTTLE WHEN TRYING TO ARM
                                if throttle < 1100:
                                    self.armed = True
                                    print("\n>>> ARMED (Ready to Fly!) <<<")
                                else:
                                    print("\nUH OH SAFETY BLOCK: Lower throttle to arm!")
                                    
                        if event.button == 1: # B Button (Quit)
                            self.running = False

                # 3. SAFETY CLAMP
                # dont send illegal MSP values
                roll = max(1000, min(2000, roll))
                pitch = max(1000, min(2000, pitch))
                yaw = max(1000, min(2000, yaw))
                throttle = max(1000, min(2000, throttle))
                
                # 4. SEND COMMAND
                arm_value = 1800 if self.armed else 1000
                data = struct.pack('<5H', roll, pitch, throttle, yaw, arm_value)
                self.sock.sendto(data, (PI_IP, PI_PORT))
                
                # 5. PRINT STATUS
                status = "ARMED!!" if self.armed else "Disarmed :/"
                print(f"\r{status} | R:{roll} P:{pitch} Y:{yaw} T:{throttle}   ", end="")
                
                time.sleep(0.02) # 50Hz
                
        finally:
            self.sock.close()
            pygame.quit()

if __name__ == "__main__":
    GamepadController().run()
