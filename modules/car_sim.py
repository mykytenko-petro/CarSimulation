import math
from typing import Sequence, Tuple

import pygame

from .config import WALL_COLOR
from .parts import Ray


class CarSimulation:
    """Клас фізичної симуляції руху машинки на основі кінематики Аккермана (Ackermann Steering).

    Відповідає за:
    - Кінематику заднього/переднього ходу з рульовим сервоприводом.
    - Симуляцію сенсорів відстані (Raycast по поверхні PNG карти).
    - Виявлення та обробку зіткнень із кольоровими стінами на PNG карти.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float = 0.0,
        length: float = 18.0,
        width: float = 10.0,
        wheel_base: float = 10.0,
        max_steering_angle: float = 30.0,
        friction_coeff: float = 1.0,
        speed_factor: float = 0.02,
        ray_angles: Sequence[float] = (-75.0, -10.0, 0.0, 10.0, 75.0),
        ray_length: float = 180.0,
    ) -> None:
        self.x = x
        self.y = y
        self.angle = angle

        self.length = length
        self.width = width
        self.wheel_base = wheel_base
        self.max_steering_angle = max_steering_angle

        self.friction_coeff = friction_coeff
        self.speed_factor = speed_factor
        self.is_colliding = False

        self.rays: list[Ray] = [
            Ray((self.x, self.y), ray_angle, max_length=ray_length)
            for ray_angle in ray_angles
        ]

    def get_center(self) -> Tuple[float, float]:
        """Обчислює координати геометричного центру машинки."""
        rad = math.radians(self.angle)
        return (
            self.x + (self.length / 2.0) * math.cos(rad),
            self.y + (self.length / 2.0) * math.sin(rad),
        )

    def get_bounding_box(self) -> pygame.Rect:
        """Повертає обмежувальний прямокутник (AABB) машинки."""
        cx, cy = self.get_center()
        return pygame.Rect(
            cx - self.length / 2.0,
            cy - self.width / 2.0,
            self.length,
            self.width,
        )

    def _is_wall_pixel(self, map_surface: pygame.Surface, x: int, y: int) -> bool:
        """Перевіряє, чи належить піксель на карті до стіни (за WALL_COLOR)."""
        width, height = map_surface.get_size()
        if 0 <= x < width and 0 <= y < height:
            pixel = map_surface.get_at((x, y))
            return (pixel.r, pixel.g, pixel.b) == (WALL_COLOR.r, WALL_COLOR.g, WALL_COLOR.b)
        return True  # Вважати все за межами карти стіною

    def check_collisions(
        self,
        map_surface: pygame.Surface,
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> bool:
        """Перевіряє зіткнення прямокутника машинки з колірними пікселями стін на карті

        та прямокутниками інших машинок.
        """
        my_box = self.get_bounding_box()

        # 1. Перевірка зіткнення зі стінами карти (за коліром пікселів у межах AABB машинки)
        for x in range(int(my_box.left), int(my_box.right)):
            for y in range(int(my_box.top), int(my_box.bottom)):
                if self._is_wall_pixel(map_surface, x, y):
                    return True

        # 2. Перевірка зіткнення з прямокутниками інших машин/перешкод
        for obs in obstacle_boxes:
            if my_box.colliderect(obs):
                return True

        return False

    def update_sensors(
        self,
        map_surface: pygame.Surface,
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> list[float]:
        """Оновлює промені-сенсори з урахуванням пікселів стін карти та об'єктів."""
        center = self.get_center()

        for ray in self.rays:
            # Оновлюємо рейкастинг за мапою та прямокутниками перешкод
            ray.update_color_map(center, self.angle, map_surface, WALL_COLOR, obstacle_boxes)

        return [ray.distance for ray in self.rays]

    def apply_kinematics(
        self, drive_signal: int, steering_signal: int
    ) -> Tuple[float, float]:
        """Кінематика Аккермана."""
        v_linear = drive_signal * self.speed_factor

        steering_clamped = max(-100, min(100, steering_signal))
        steering_angle_deg = (steering_clamped / 100.0) * self.max_steering_angle
        delta_rad = math.radians(steering_angle_deg)

        if abs(delta_rad) > 0.0001 and abs(v_linear) > 0.0001:
            turning_radius = self.wheel_base / math.tan(delta_rad)
            omega_rad = v_linear / turning_radius
            omega_deg = math.degrees(omega_rad)
            self.angle += omega_deg

        rad = math.radians(self.angle)
        dx = v_linear * math.cos(rad)
        dy = v_linear * math.sin(rad)

        return dx, dy

    def resolve_collisions(
        self,
        dx: float,
        dy: float,
        map_surface: pygame.Surface,
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        """Обробка колізій із ковзанням при зіткненні з кольоровими стінами."""
        if self.check_collisions(map_surface, obstacle_boxes):
            self.is_colliding = True

            self.x -= dx
            self.y -= dy

            self.x += dx * self.friction_coeff
            if self.check_collisions(map_surface, obstacle_boxes):
                self.x -= dx * self.friction_coeff

                self.y += dy * self.friction_coeff
                if self.check_collisions(map_surface, obstacle_boxes):
                    self.y -= dy * self.friction_coeff
        else:
            self.is_colliding = False

    def step(
        self,
        drive_signal: int,
        steering_signal: int,
        map_surface: pygame.Surface,
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        """Виконує один дискретний крок фізичного оновлення."""
        dx, dy = self.apply_kinematics(drive_signal, steering_signal)
        self.x += dx
        self.y += dy
        self.resolve_collisions(dx, dy, map_surface, obstacle_boxes)