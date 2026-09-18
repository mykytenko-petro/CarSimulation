from typing import Sequence

import pygame

from .car_render import CarRenderer
from .car_sim import CarSimulation
from .guidance import GuidanceAlgorithm


class Car:
    """
    Основний контролер машинки, який містить алгоритм відображення,
    фізичну симуляцію (на основі колірних стін) та алгоритм навігації.
    """
    def __init__(self, x: float, y: float) -> None:
        self.sim = CarSimulation(x, y)
        self.controller = GuidanceAlgorithm()
        self.renderer = CarRenderer()

    def get_bounding_box(self) -> pygame.Rect:
        return self.sim.get_bounding_box()

    def check_collisions(
        self, map_surface: pygame.Surface, all_cars: Sequence["Car"]
    ) -> bool:
        """Перевіряє зіткнення машинки з колірними стінами карти та іншими авто."""
        obstacle_boxes = [c.get_bounding_box() for c in all_cars if c is not self]
        return self.sim.check_collisions(map_surface, obstacle_boxes)

    def update(
        self,
        map_surface: pygame.Surface,
        all_cars: Sequence["Car"],
    ) -> None:
        """
        Оновлює стан машинки:
        1. Зчитує показники сенсорів із поверхні карти.
        2. Обчислює керуючі сигнали (drive_signal, steering_signal).
        3. Виконує фізичний крок переміщення та розв'язання колізій.
        """
        obstacle_boxes = [c.get_bounding_box() for c in all_cars if c is not self]
        
        # 1. Зчитування сенсорів через map_surface
        distances = self.sim.update_sensors(map_surface, obstacle_boxes)
        
        # 2. Обчислення керуючих сигналів
        drive_signal, steering_signal = self.controller.update(distances)
        
        # 3. Фізичний крок руху
        self.sim.step(drive_signal, steering_signal, map_surface, obstacle_boxes)

    def draw(self, surface: pygame.Surface) -> None:
        self.renderer.draw(
            surface,
            self.sim,
        )