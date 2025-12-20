import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No gamepad found.")
    exit(1)

joy = pygame.joystick.Joystick(0)
joy.init()

print(f"Controller: {joy.get_name()}")
print(f"Total axes: {joy.get_numaxes()}\n")
print("Move each stick slowly and watch which axis changes:\n")

try:
    while True:
        pygame.event.pump()
        
        # Print all axes every loop
        print("\r", end="")
        for i in range(joy.get_numaxes()):
            val = joy.get_axis(i)
            bar = "█" * int(abs(val) * 10) if abs(val) > 0.1 else " "
            print(f"A{i}: {val:>6.2f} {bar}  ", end="")
        
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n\nDone!")
