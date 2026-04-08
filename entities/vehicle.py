class CarUpdate:
    #singleton implemented
    def update(self):
        return self

class Car:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 20
        self.velocity = 2

    def update(self):
        self.x = CarUpdate.update(self.x)

    def draw(self, screen):
        import pygame
        pygame.draw.rect(screen, (220, 90, 90), (self.x, self.y, self.width, self.height))
