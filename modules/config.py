import pygame


WIDTH = 1280
HEIGHT = 720

BACKGROUND_COLOR = pygame.Color("#1e1e23")
WALL_COLOR = pygame.Color("#8f3dd4")
SPAWN_COLOR = pygame.Color("#37946e")

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()