import math
from typing import Sequence, Tuple

import pygame


class Ray:
    """
    Клас, що симулює сенсор відстані (далекомір / raycast по поверхні).
    Випромінює промінь від заданої позиції та обчислює дистанцію до
    найближчого пікселя стіни (WALL_COLOR) або прямокутників перешкод.
    """

    def __init__(self, position: Tuple[float, float], angle: float, max_length: float) -> None:
        self.pos = position
        self.init_angle = angle
        self.length = max_length
        self.dir: Tuple[float, float] = (0.0, 0.0)
        self.terminus: Tuple[float, float] = position
        self.distance: float = max_length

    def update_direction(self, direction: float) -> None:
        """Перераховує одиничний вектор напрямку променя в залежності від кута машинки."""
        angle = math.radians(self.init_angle + direction)
        self.dir = (math.cos(angle), math.sin(angle))

    def update_color_map(
        self,
        origin: Tuple[float, float],
        direction: float,
        map_surface: pygame.Surface,
        wall_color: pygame.Color,
        obstacle_boxes: Sequence[pygame.Rect],
        step_size: float = 1.0,
    ) -> None:
        """
        Сканує карту вздовж напрямку променя кроками step_size для виявлення 
        найближчого пікселя стіни (wall_color) або перетину з obstacle_boxes.
        """
        self.pos = origin
        self.update_direction(direction)

        map_w, map_h = map_surface.get_size()
        target_rgb = (wall_color.r, wall_color.g, wall_color.b)

        current_dist = 0.0
        hit = False
        hit_pos = (
            self.pos[0] + self.dir[0] * self.length,
            self.pos[1] + self.dir[1] * self.length,
        )

        while current_dist <= self.length:
            curr_x = self.pos[0] + self.dir[0] * current_dist
            curr_y = self.pos[1] + self.dir[1] * current_dist

            ix, iy = int(curr_x), int(curr_y)

            # 1. Перевірка за межами мапи (поза карти = стіна)
            if ix < 0 or ix >= map_w or iy < 0 or iy >= map_h:
                hit = True
                hit_pos = (curr_x, curr_y)
                break

            # 2. Перевірка кольору пікселя карти
            pixel = map_surface.get_at((ix, iy))
            if (pixel.r, pixel.g, pixel.b) == target_rgb:
                hit = True
                hit_pos = (curr_x, curr_y)
                break

            # 3. Перевірка додаткових прямокутників (інших машин)
            if obstacle_boxes:
                point_rect = pygame.Rect(ix, iy, 1, 1)
                if any(box.colliderect(point_rect) for box in obstacle_boxes):
                    hit = True
                    hit_pos = (curr_x, curr_y)
                    break

            current_dist += step_size

        self.distance = current_dist if hit else self.length
        self.terminus = hit_pos

    def draw(self, surface: pygame.Surface, color: Tuple[int, int, int] = (255, 0, 0)) -> None:
        """Візуалізація променя від початку до кінцевої точки (для дебагу)."""
        pygame.draw.line(surface, color, self.pos, self.terminus, 1)