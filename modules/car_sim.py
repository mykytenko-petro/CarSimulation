import math
from typing import Sequence, Tuple

import pygame

from .parts.ray import Ray


class CarSimulation:
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

        self.rays: list[Ray] = [
            Ray((self.x, self.y), ray_angle, max_length=ray_length)
            for ray_angle in ray_angles
        ]

    def get_center(self) -> Tuple[float, float]:
        rad = math.radians(self.angle)
        return (
            self.x + (self.length / 2.0) * math.cos(rad),
            self.y + (self.length / 2.0) * math.sin(rad),
        )

    def get_bounding_box(self) -> pygame.Rect:
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
        targets: list[pygame.Rect] = list(walls) + list(obstacle_boxes)
        center = self.get_center()

        for ray in self.rays:
            ray.update(center, self.angle, targets)

        return [ray.distance for ray in self.rays]

    def apply_kinematics(
        self, left_signal: int, right_signal: int
    ) -> Tuple[float, float]:
        v_left = left_signal * self.speed_factor
        v_right = right_signal * self.speed_factor

        v_linear = (v_left + v_right) / 2.0

        omega_rad = (v_right - v_left) / self.wheel_base
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
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
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
        left_signal: int,
        right_signal: int,
        walls: Sequence[pygame.Rect],
        obstacle_boxes: Sequence[pygame.Rect],
    ) -> None:
        dx, dy = self.apply_kinematics(left_signal, right_signal)
        self.x += dx
        self.y += dy
        self.resolve_collisions(dx, dy, walls, obstacle_boxes)
