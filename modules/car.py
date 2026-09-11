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
        self.speed = 3.0
        self.max_angle = 15.0

        self.length = 18.0
        self.width = 10.0

        self.is_colliding = False
        self.friction_coeff = 0.4

        self.rays: list[Ray] = [
            Ray((self.x, self.y), angle, max_length=180.0)
            for angle in [-60, 0, 60]
        ]

        self.left_motor_signal: int = 0
        self.right_motor_signal: int = 0
        self.base_pwm: float = 180.0
        self.turn_sensitivity: float = 4.0

    def get_bounding_box(self) -> pygame.Rect:
        return pygame.Rect(
            self.x - self.length / 2,
            self.y - self.width / 2,
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

    def calculate_motor_signals(self, delta_angle: float) -> Tuple[int, int]:
        left_val = self.base_pwm + (delta_angle * self.turn_sensitivity)
        right_val = self.base_pwm - (delta_angle * self.turn_sensitivity)

        left_signal = int(max(0, min(255, left_val)))
        right_signal = int(max(0, min(255, right_val)))

        return left_signal, right_signal

    def update(
        self,
        walls: list[pygame.Rect],
        all_cars: list["Car"],
    ) -> None:
        initial_angle = self.angle

        targets: list[pygame.Rect] = list(walls)
        for car in all_cars:
            if car is not self:
                targets.append(car.get_bounding_box())

        for ray in self.rays:
            ray.update((self.x, self.y), self.angle, targets)

        self.update_guidance()

        delta_angle = self.angle - initial_angle
        self.left_motor_signal, self.right_motor_signal = self.calculate_motor_signals(delta_angle)

        rad = math.radians(self.angle)
        dx = self.speed * math.cos(rad)
        dy = self.speed * math.sin(rad)

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
            self.evasive_action(max_ray)

    def find_min_max_rays(self) -> Tuple[int, int]:
        max_distance, max_index = self.rays[0].distance, 0
        min_distance, min_index = self.rays[0].distance, 0

        for index, ray in enumerate(self.rays):
            if ray.distance >= max_distance:
                max_distance, max_index = ray.distance, index
            if ray.distance <= min_distance:
                min_distance, min_index = ray.distance, index
                
        return min_index, max_index

    def evasive_action(self, max_ray: int) -> None:
        if max_ray == 0:
            self.angle += randint(-int(self.max_angle), 0)
        elif max_ray == 1:
            if self.rays[0].distance > self.rays[2].distance:
                self.angle += randint(-int(self.max_angle), 0)
            else:
                self.angle += randint(0, int(self.max_angle))
        else:
            self.angle += randint(0, int(self.max_angle))

    def get_angle_to_target(self, target: Tuple[float, float]) -> float:
        A = (self.x, self.y)
        B = self.get_projected_pos(self.angle, self.speed)
        C = target

        AB = (B[0] - A[0], B[1] - A[1])
        AC = (C[0] - A[0], C[1] - A[1])

        AB_m = math.hypot(AB[0], AB[1])
        AC_m = math.hypot(AC[0], AC[1])

        if AB_m * AC_m == 0:
            return 0.0

        temp = max(-1.0, min(1.0, ((AB[0] * AC[0]) + (AB[1] * AC[1])) / (AB_m * AC_m)))
        return math.degrees(math.acos(temp))

    def get_projected_pos(self, base_angle: float, length: float) -> Tuple[float, float]:
        rad = math.radians(base_angle)
        return self.x + length * math.cos(rad), self.y + length * math.sin(rad)

    def draw(self, surface: pygame.Surface) -> None:
        for ray in self.rays:
            pygame.draw.line(surface, (255, 0, 0), (self.x, self.y), ray.terminus, 1)
            pygame.draw.circle(surface, (255, 255, 0), (int(ray.terminus[0]), int(ray.terminus[1])), 3)

        body_color = (255, 50, 50) if self.is_colliding else (0, 150, 255)
        rect_surface = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        rect_surface.fill(body_color)
        rotated_surface = pygame.transform.rotate(rect_surface, -self.angle)
        rect = rotated_surface.get_rect(center=(self.x, self.y))
        surface.blit(rotated_surface, rect.topleft)

        font = pygame.font.SysFont(None, 14)
        sig_text = font.render(f"L:{self.left_motor_signal} R:{self.right_motor_signal}", True, (255, 255, 255))
        surface.blit(sig_text, (self.x - 20, self.y - self.width - 12))