import math
from random import randint
from typing import Tuple

import pygame

from .ray import Ray


class Car:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.angle = 0.0
        self.max_angle = 15.0

        self.length = 18.0
        self.width = 10.0
        self.wheel_base = 10.0

        self.is_colliding = False
        self.friction_coeff = 0.4

        self.rays: list[Ray] = [
            Ray((self.x, self.y), angle, max_length=180.0)
            for angle in [-60, 0, 60]
        ]

        self.left_motor_signal: int = 180
        self.right_motor_signal: int = 180
        self.base_pwm: float = 180.0

        self.speed_factor: float = 0.02

    def get_center(self) -> Tuple[float, float]:
        rad = math.radians(self.angle)
        return (
            self.x + (self.length / 2) * math.cos(rad),
            self.y + (self.length / 2) * math.sin(rad),
        )

    def get_bounding_box(self) -> pygame.Rect:
        cx, cy = self.get_center()
        return pygame.Rect(
            cx - self.length / 2,
            cy - self.width / 2,
            self.length,
            self.width,
        )

    def check_collisions(self, walls: list[pygame.Rect], all_cars: list["Car"]) -> bool:
        my_box = self.get_bounding_box()

        for wall in walls:
            if my_box.colliderect(wall):
                return True

        for car in all_cars:
            if car is not self:
                if my_box.colliderect(car.get_bounding_box()):
                    return True

        return False

    def update(
        self,
        walls: list[pygame.Rect],
        all_cars: list["Car"],
    ) -> None:
        targets: list[pygame.Rect] = list(walls)
        for car in all_cars:
            if car is not self:
                targets.append(car.get_bounding_box())

        for ray in self.rays:
            ray.update(self.get_center(), self.angle, targets)

        self.update_guidance()

        v_left = self.left_motor_signal * self.speed_factor
        v_right = self.right_motor_signal * self.speed_factor

        v_linear = (v_left + v_right) / 2.0

        omega_rad = (v_right - v_left) / self.wheel_base
        omega_deg = math.degrees(omega_rad)

        self.angle += omega_deg

        rad = math.radians(self.angle)
        dx = v_linear * math.cos(rad)
        dy = v_linear * math.sin(rad)

        self.x += dx
        self.y += dy

        if self.check_collisions(walls, all_cars):
            self.is_colliding = True

            self.x -= dx
            self.y -= dy

            self.x += dx * self.friction_coeff
            if self.check_collisions(walls, all_cars):
                self.x -= dx * self.friction_coeff

                self.y += dy * self.friction_coeff
                if self.check_collisions(walls, all_cars):
                    self.y -= dy * self.friction_coeff
        else:
            self.is_colliding = False

    def update_guidance(self) -> None:
        min_ray, max_ray = self.find_min_max_rays()

        if self.rays[min_ray].distance < 80.0:
            delta_angle = self.calculate_evasive_delta(max_ray)
            self.left_motor_signal, self.right_motor_signal = self.calculate_motor_signals(delta_angle)
        else:
            self.left_motor_signal = int(self.base_pwm)
            self.right_motor_signal = int(self.base_pwm)

    def calculate_evasive_delta(self, max_ray: int) -> float:
        if max_ray == 0:
            return float(randint(-int(self.max_angle), 0))
        elif max_ray == 1:
            if self.rays[0].distance > self.rays[2].distance:
                return float(randint(-int(self.max_angle), 0))
            else:
                return float(randint(0, int(self.max_angle)))
        else:
            return float(randint(0, int(self.max_angle)))

    def calculate_motor_signals(self, delta_angle: float) -> Tuple[int, int]:
        turn_sensitivity = 4.0
        left_val = self.base_pwm - (delta_angle * turn_sensitivity)
        right_val = self.base_pwm + (delta_angle * turn_sensitivity)

        left_signal = int(max(0, min(255, left_val)))
        right_signal = int(max(0, min(255, right_val)))

        return left_signal, right_signal

    def find_min_max_rays(self) -> Tuple[int, int]:
        max_distance, max_index = self.rays[0].distance, 0
        min_distance, min_index = self.rays[0].distance, 0
        for index, ray in enumerate(self.rays):
            if ray.distance >= max_distance:
                max_distance, max_index = ray.distance, index
            if ray.distance <= min_distance:
                min_distance, min_index = ray.distance, index
        return min_index, max_index

    def draw(self, surface: pygame.Surface) -> None:
        center = self.get_center()

        for ray in self.rays:
            pygame.draw.line(surface, (255, 0, 0), center, ray.terminus, 1)
            pygame.draw.circle(surface, (255, 255, 0), (int(ray.terminus[0]), int(ray.terminus[1])), 3)

        body_color = (255, 50, 50) if self.is_colliding else (0, 150, 255)
        rect_surface = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        rect_surface.fill(body_color)
        rotated_surface = pygame.transform.rotate(rect_surface, -self.angle)
        rect = rotated_surface.get_rect(center=center)
        surface.blit(rotated_surface, rect.topleft)

        font = pygame.font.SysFont(None, 14)
        sig_text = font.render(f"L:{self.left_motor_signal} R:{self.right_motor_signal}", True, (255, 255, 255))
        surface.blit(sig_text, (center[0] - 20, center[1] - self.width - 12))