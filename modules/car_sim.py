import math
from typing import Sequence, Tuple

import pygame

from .parts.ray import Ray


class CarSimulation:
    """
    Клас фізичної симуляції руху машинки.
    Відповідає за:
    - Кінематику двоколісного диференційного приводу (швидкість, кут повороту, переміщення).
    - Симуляцію сенсорів відстані (Raycast).
    - Виявлення та обробку зіткнень зі стінами та іншими машинками.
    """

    def __init__(
        self,
        x: float,
        y: float,
        angle: float = 0.0,
        length: float = 18.0,
        width: float = 10.0,
        wheel_base: float = 10.0,
        friction_coeff: float = 0.2,
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

        self.friction_coeff = friction_coeff
        self.speed_factor = speed_factor
        self.is_colliding = False

        # Ініціалізація променів-сенсорів машинки
        self.rays: list[Ray] = [
            Ray((self.x, self.y), ray_angle, max_length=ray_length)
            for ray_angle in ray_angles
        ]

    def get_center(self) -> Tuple[float, float]:
        """
        Обчислює координати геометричного центру машинки на основі її положення та кута.
        """
        rad = math.radians(self.angle)
        return (
            self.x + (self.length / 2.0) * math.cos(rad),
            self.y + (self.length / 2.0) * math.sin(rad),
        )

    def get_bounding_box(self) -> pygame.Rect:
        """
        Повертає вирівняний по осях обмежувальний прямокутник (AABB) для виявлення колізій.
        """
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
        """
        Перевіряє перетин машинки з будь-якою зі стін або іншими машинками.
        :return: True, якщо є колізія, інакше False.
        """
        my_box = self.get_bounding_box()

        # Перевірка зіткнення зі стінами карти
        for wall in walls:
            if my_box.colliderect(wall):
                return True

        # Перевірка зіткнення з іншими машинками
        for obs in obstacle_boxes:
            if my_box.colliderect(obs):
                return True

        return False

    def update_sensors(
        self,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> list[float]:
        """
        Оновлює стан усіх сенсорів-променів з урахуванням поточного положення авто
        та повертає список відстаней до найближчих об'єктів.
        """
        # Об'єднуємо стіни та інші машинки в єдиний список перешкод
        targets: list[pygame.Rect] = list(walls) + list(obstacle_boxes)
        center = self.get_center()

        for ray in self.rays:
            ray.update(center, self.angle, targets)

        return [ray.distance for ray in self.rays]

    def apply_kinematics(
        self, left_signal: int, right_signal: int
    ) -> Tuple[float, float]:
        """
        Кінематика диференційного приводу:
        перетворює сигнали ШІМ лівого і правого мотора на зміщення (dx, dy) та поворот кута машинки.
        """
        # Лінійні швидкості лівого та правого колеса
        v_left = left_signal * self.speed_factor
        v_right = right_signal * self.speed_factor

        # Загальна поступальна швидкість центру мас машинки
        v_linear = (v_left + v_right) / 2.0

        # Кутова швидкість повороту (радіани/кадр) на основі різниці швидкостей коліс
        omega_rad = (v_right - v_left) / self.wheel_base
        omega_deg = math.degrees(omega_rad)

        # Оновлення орієнтації машинки
        self.angle += omega_deg

        # Проекція швидкості на координатні осі X та Y
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
        """
        Обробка колізій: відкат назад при зіткненні зі спробою ковзання по осях із врахуванням тертя.
        """
        if self.check_collisions(walls, obstacle_boxes):
            self.is_colliding = True

            # Відкочуємо машинку назад на попередню позицію до зіткнення
            self.x -= dx
            self.y -= dy

            # Пробуємо виконати частковий рух вздовж осі X (ковзання по стіні)
            self.x += dx * self.friction_coeff
            if self.check_collisions(walls, obstacle_boxes):
                self.x -= dx * self.friction_coeff

                # Якщо по X не вдалося, пробуємо рух вздовж осі Y
                self.y += dy * self.friction_coeff
                if self.check_collisions(walls, obstacle_boxes):
                    self.y -= dy * self.friction_coeff
        else:
            self.is_colliding = False

    def step(
        self,
        left_signal: int,
        right_signal: int,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        """
        Виконує один дискретний крок фізичного оновлення:
        1. Розрахунок переміщення на основі сигналів моторів.
        2. Оновлення координат машинки.
        3. Перевірка та усунення колізій.
        """
        dx, dy = self.apply_kinematics(left_signal, right_signal)
        self.x += dx
        self.y += dy
        self.resolve_collisions(dx, dy, walls, obstacle_boxes)
