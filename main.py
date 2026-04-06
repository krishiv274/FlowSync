import pygame

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

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Fill background
    screen.fill((30, 30, 30))  # Dark gray

    # Update display
    pygame.display.flip()

    # Cap at 60 FPS
    clock.tick(FPS)

pygame.quit()