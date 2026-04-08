import pygame
import sys
from entities.vehicle import Car

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 800, 600

# Create window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Window")

# Clock for FPS control
clock = pygame.time.Clock()
FPS = 60

# Create a car instance
cars = [
    Car(300, HEIGHT//2 - 30),
    Car(200, HEIGHT//2 + 10),
    ]

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Fill background
    screen.fill((30, 30, 30))  # Dark gray

    # Draw road    
    pygame.draw.rect(screen, (50, 50, 50), (0, HEIGHT//2 - 40, WIDTH, 80))
    pygame.draw.line(screen, (255, 255, 255), (0, HEIGHT//2), (WIDTH, HEIGHT//2), 2)

    # Draw and update cars
    for car in cars:
        car.update()
        car.draw(screen)

    # Update display
    pygame.display.flip()

    # Cap at 60 FPS
    clock.tick(FPS)


pygame.quit()