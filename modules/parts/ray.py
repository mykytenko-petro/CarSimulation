import math
from typing import Tuple

import pygame


class Ray:
    def __init__(self, position: Tuple[float, float], angle: float, max_length: float) -> None:
        self.pos = position
        self.init_angle = angle
        self.length = max_length
        self.dir = (0.0, 0.0)
        self.terminus: Tuple[float, float] = position
        self.distance = max_length

    def update(self, point: Tuple[float, float], direction: float, walls: list[pygame.Rect]) -> None:
        self.pos = point
        self.update_direction(direction)
        self.update_terminus(walls)

    def update_direction(self, direction: float) -> None:
        angle = math.radians(self.init_angle + direction)
        self.dir = (math.cos(angle), math.sin(angle))

    def update_terminus(self, walls: list[pygame.Rect]) -> None:
        min_distance = self.length
        min_terminus = (
            self.pos[0] + self.dir[0] * self.length,
            self.pos[1] + self.dir[1] * self.length,
        )

        x3, y3 = self.pos
        x4, y4 = self.pos[0] + self.dir[0], self.pos[1] + self.dir[1]

        for rect in walls:
            segments = [
                (rect.topleft, rect.topright),
                (rect.topright, rect.bottomright),
                (rect.bottomright, rect.bottomleft),
                (rect.bottomleft, rect.topleft),
            ]

            for (x1, y1), (x2, y2) in segments:
                divisor = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                if divisor == 0:
                    continue

                t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / divisor
                u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / divisor

                if 0 <= t <= 1 and u > 0:
                    x_point = x1 + t * (x2 - x1)
                    y_point = y1 + t * (y2 - y1)
                    dist_check = math.dist(self.pos, (x_point, y_point))

                    if dist_check < min_distance:
                        min_distance = dist_check
                        min_terminus = (x_point, y_point)

        self.distance = min_distance
        self.terminus = min_terminus
