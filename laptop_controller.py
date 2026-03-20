import pygame, socket, time

UDP_IP   = "10.0.0.140"  # , Pi IP 
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("RC Car Controller")
print("WASD to drive. Close window to quit.")

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    steering = "N"
    throttle  = "N"

    if keys[pygame.K_a]: steering = "L"
    elif keys[pygame.K_d]: steering = "R"

    if keys[pygame.K_w]: throttle = "F"
    elif keys[pygame.K_s]: throttle = "B"

    msg = f"{steering},{throttle}"
    sock.sendto(msg.encode(), (UDP_IP, UDP_PORT))
    clock.tick(50)  # 50Hz

sock.sendto(b"N,N", (UDP_IP, UDP_PORT))
pygame.quit()

