import math
from typing import Sequence, Tuple

import pygame

from .parts import Ray


class CarSimulation:
    """Клас фізичної симуляції руху машинки на основі кінематики Аккермана (Ackermann Steering).

    Відповідає за:
    - Кінематику заднього/переднього ходу з рульовим сервоприводом.
    - Симуляцію сенсорів відстані (Raycast).
    - Виявлення та обробку зіткнень зі стінами та іншими об'єктами.
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
        friction_coeff: float = 0.1,
        speed_factor: float = 0.02,
        ray_angles: Sequence[float] = (-60.0, 0.0, 60.0),
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

        # Ініціалізація променів-сенсорів машинки (збережено 3 сенсори)
        self.rays: list[Ray] = [
            Ray((self.x, self.y), ray_angle, max_length=ray_length)
            for ray_angle in ray_angles
        ]

    def get_center(self) -> Tuple[float, float]:
        """Обчислює координати геометричного центру машинки на основі її
        положення та кута."""
        rad = math.radians(self.angle)
        return (
            self.x + (self.length / 2.0) * math.cos(rad),
            self.y + (self.length / 2.0) * math.sin(rad),
        )

    def get_bounding_box(self) -> pygame.Rect:
        """Повертає вирівняний по осях обмежувальний прямокутник (AABB) для
        виявлення колізій."""
        cx, cy = self.get_center()
        return pygame.Rect(
            cx - self.length / 2.0,
            cy - self.width / 2.0,
            self.length,
            self.width,
        )

    def check_collisions(
        self,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> bool:
        """Перевіряє перетин машинки з будь-якою зі стін або іншими машинками.

        :return: True, якщо є колізія, інакше False.
        """
        my_box = self.get_bounding_box()

        for wall in walls:
            if my_box.colliderect(wall):
                return True

        for obs in obstacle_boxes:
            if my_box.colliderect(obs):
                return True

        return False

    def update_sensors(
        self,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> list[float]:
        """Оновлює стан усіх сенсорів-променів з урахуванням поточного положення
        авто та повертає список відстаней до найближчих об'єктів."""
        targets: list[pygame.Rect] = list(walls) + list(obstacle_boxes)
        center = self.get_center()

        for ray in self.rays:
            ray.update(center, self.angle, targets)

        return [ray.distance for ray in self.rays]

    def apply_kinematics(
        self, drive_signal: int, steering_signal: int
    ) -> Tuple[float, float]:
        """Кінематика Аккермана:

        - drive_signal: керує швидкості тягового мотора (поступальний рух вперед/назад).
        - steering_signal: керує кутом повороту сервоприводу.
        """
        # Лінійна швидкість від тягового двигуна
        v_linear = drive_signal * self.speed_factor

        # Нормалізація сигналу кермування в кут повороту колес (в радіанах)
        steering_clamped = max(-100, min(100, steering_signal))
        steering_angle_deg = (steering_clamped / 100.0) * self.max_steering_angle
        delta_rad = math.radians(steering_angle_deg)

        # Кінематика Аккермана для оновлення кута орієнтації (heading)
        if abs(delta_rad) > 0.0001 and abs(v_linear) > 0.0001:
            turning_radius = self.wheel_base / math.tan(delta_rad)
            omega_rad = v_linear / turning_radius
            omega_deg = math.degrees(omega_rad)
            self.angle += omega_deg

        # Проекція швидкості на осі X та Y
        rad = math.radians(self.angle)
        dx = v_linear * math.cos(rad)
        dy = v_linear * math.sin(rad)

        return dx, dy

    def resolve_collisions(
        self,
        dx: float,
        dy: float,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        """Обробка колізій: відкат назад при зіткненні зі спробою ковзання по

        осях із врахуванням тертя.
        """
        if self.check_collisions(walls, obstacle_boxes):
            self.is_colliding = True

            self.x -= dx
            self.y -= dy

            self.x += dx * self.friction_coeff
            if self.check_collisions(walls, obstacle_boxes):
                self.x -= dx * self.friction_coeff

                self.y += dy * self.friction_coeff
                if self.check_collisions(walls, obstacle_boxes):
                    self.y -= dy * self.friction_coeff
        else:
            self.is_colliding = False

    def step(
        self,
        drive_signal: int,
        steering_signal: int,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        """Виконує один дискретний крок фізичного оновлення."""
        dx, dy = self.apply_kinematics(drive_signal, steering_signal)
        self.x += dx
        self.y += dy
        self.resolve_collisions(dx, dy, walls, obstacle_boxes)