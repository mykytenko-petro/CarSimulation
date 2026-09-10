import math
from random import randint
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


class Car:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.angle = 0.0  # Direction angle in degrees
        self.speed = 3.0
        self.max_angle = 15.0  # Max random turn step angle
        self.decision_counter = 0

        self.length = 18.0
        self.width = 10.0

        self.is_colliding = False
        self.friction_coeff = 0.4  # Speed reduction factor when sliding along walls/cars

        # 3-Ray configuration (-60, 0, +60 degrees relative to direction)
        self.rays: list[Ray] = [
            Ray((self.x, self.y), angle, max_length=180.0)
            for angle in range(-60, 70, 60)
        ]

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

    def update(
        self,
        walls: list[pygame.Rect],
        all_cars: list["Car"],
        target: Tuple[float, float] | None = None,
    ) -> None:
        """Updates rays, guidance, and handles movement with friction vector sliding on collisions."""
        # 1. Gather collision targets
        targets: list[pygame.Rect] = list(walls)
        for car in all_cars:
            if car is not self:
                targets.append(car.get_bounding_box())

        # 2. Update raycasting distance readings
        for ray in self.rays:
            ray.update((self.x, self.y), self.angle, targets)

        # 3. Decision & Steering Logic
        self.update_guidance(target)

        # 4. Movement execution with friction sliding mechanics
        rad = math.radians(self.angle)
        dx = self.speed * math.cos(rad)
        dy = self.speed * math.sin(rad)

        # Try standard full move
        self.x += dx
        self.y += dy

        if self.check_collisions(walls, all_cars):
            self.is_colliding = True
            # Revert full step
            self.x -= dx
            self.y -= dy

            # Sliding check 1: Try horizontal movement with friction penalty
            self.x += dx * self.friction_coeff
            if self.check_collisions(walls, all_cars):
                # Revert horizontal slide if blocked
                self.x -= dx * self.friction_coeff

                # Sliding check 2: Try vertical movement with friction penalty
                self.y += dy * self.friction_coeff
                if self.check_collisions(walls, all_cars):
                    # Fully stuck in corner: revert vertical slide
                    self.y -= dy * self.friction_coeff
        else:
            self.is_colliding = False

    def update_guidance(self, target: Tuple[float, float] | None) -> None:
        min_ray, max_ray = self.find_min_max_rays()
        if self.rays[min_ray].distance < 80.0:
            self.evasive_action(max_ray)
        else:
            self.decision_counter_check(target)

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

    def decision_counter_check(self, target: Tuple[float, float] | None) -> None:
        if self.decision_counter >= 10:
            if target:
                self.turn_towards_target(target)
            else:
                self.angle += randint(-int(self.max_angle), int(self.max_angle))
            self.decision_counter = 0
        else:
            self.decision_counter += 1

    def turn_towards_target(self, target: Tuple[float, float]) -> None:
        angle = self.get_angle_to_target(target)
        target_distance = math.dist((self.x, self.y), target)

        left = math.dist(self.get_projected_pos(self.angle - angle, target_distance), target)
        right = math.dist(self.get_projected_pos(self.angle + angle, target_distance), target)

        if right < left:
            self.angle += randint(0, int(self.max_angle))
        else:
            self.angle += randint(-int(self.max_angle), 0)

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
        # Draw 3 Rays
        for ray in self.rays:
            pygame.draw.line(surface, (255, 0, 0), (self.x, self.y), ray.terminus, 1)
            pygame.draw.circle(surface, (255, 255, 0), (int(ray.terminus[0]), int(ray.terminus[1])), 3)

        # Draw Rotated Car Body (Turns red while actively experiencing wall friction)
        body_color = (255, 50, 50) if self.is_colliding else (0, 150, 255)
        rect_surface = pygame.Surface((self.length, self.width), pygame.SRCALPHA)
        rect_surface.fill(body_color)
        rotated_surface = pygame.transform.rotate(rect_surface, -self.angle)
        rect = rotated_surface.get_rect(center=(self.x, self.y))
        surface.blit(rotated_surface, rect.topleft)