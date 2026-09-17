from typing import Sequence

import pygame

from .car_render import CarRenderer
from .car_sim import CarSimulation
from .guidance import GuidanceAlgorithm


class Car:
    '''
    Основний контролер машинки який містить алгоритм відображення та фізичну симуляцію
    '''
    def __init__(self, x: float, y: float) -> None:
        self.sim = CarSimulation(x, y)
        self.controller = GuidanceAlgorithm()
        self.renderer = CarRenderer()

    def get_bounding_box(self) -> pygame.Rect:
        return self.sim.get_bounding_box()

    def check_collisions(
        self, walls: Sequence[pygame.Rect], all_cars: Sequence["Car"]
    ) -> bool:
        obstacle_boxes = [c.get_bounding_box() for c in all_cars if c is not self]
        return self.sim.check_collisions(walls, obstacle_boxes)

    def update(
        self,
        walls: Sequence[pygame.Rect],
        all_cars: Sequence["Car"],
    ) -> None:
        obstacle_boxes = [c.get_bounding_box() for c in all_cars if c is not self]
        distances = self.sim.update_sensors(walls, obstacle_boxes)
        left_signal, right_signal = self.controller.update(distances)
        self.sim.step(left_signal, right_signal, walls, obstacle_boxes)

    def draw(self, surface: pygame.Surface) -> None:
        self.renderer.draw(
            surface,
            self.sim,
        )