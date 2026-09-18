import sys
import os

import pygame

from .config import screen, clock, BACKGROUND_COLOR
from .car import Car
from .map import Map

MAP = Map(os.path.abspath(os.path.join(".", "assets", "tilemaps", "EmbeddedIntensiveTilemap.png")))
CARS: list[Car] = []

def start():
    CARS.clear()

    for spawn in MAP.spawns:
        CARS.append(Car(spawn.left + 16, spawn.top + 16))

def update():
    for car in CARS:
        car.update(MAP.image, CARS)

def draw():
    MAP.draw(screen)

    for car in CARS:
        car.draw(screen)

def handle_key_inputs(event: pygame.event.Event):
    if event.key == pygame.K_r:
        start()

def run():
    running = True

    start()

    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                handle_key_inputs(event)

        update()

        screen.fill(BACKGROUND_COLOR)

        draw()

        pygame.display.flip()

    pygame.quit()
    sys.exit()