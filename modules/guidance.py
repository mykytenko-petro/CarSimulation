from random import randint
from typing import Sequence, Tuple


class GuidanceAlgorithm:
    def __init__(
        self,
        base_pwm: float = 255.0,
        max_angle: float = 15.0,
        turn_sensitivity: float = 4.0,
        obstacle_threshold: float = 80.0,
        stop_distance: float = 25.0,
        slow_distance: float = 80.0,
    ) -> None:
        self.base_pwm = base_pwm
        self.max_angle = max_angle
        self.turn_sensitivity = turn_sensitivity
        self.obstacle_threshold = obstacle_threshold
        self.stop_distance = stop_distance
        self.slow_distance = slow_distance

        self.left_motor_signal: int = 0
        self.right_motor_signal: int = 0

    def find_min_max(self, distances: Sequence[float]) -> Tuple[int, int]:
        max_distance, max_index = distances[0], 0
        min_distance, min_index = distances[0], 0

        for index, dist in enumerate(distances):
            if dist >= max_distance:
                max_distance, max_index = dist, index
            if dist <= min_distance:
                min_distance, min_index = dist, index

        return min_index, max_index

    def calculate_evasive_delta(
        self, max_idx: int, distances: Sequence[float]
    ) -> float:
        max_ang = int(self.max_angle)
        if max_idx == 0:
            return float(randint(-max_ang, 0))
        elif max_idx == 1:
            left_dist = distances[0] if len(distances) > 0 else 0
            right_dist = distances[2] if len(distances) > 2 else 0
            if left_dist > right_dist:
                return float(randint(-max_ang, 0))
            else:
                return float(randint(0, max_ang))
        else:
            return float(randint(0, max_ang))

    def calculate_motor_signals(
        self, delta_angle: float, speed: float
    ) -> Tuple[int, int]:
        left_val = speed - (delta_angle * self.turn_sensitivity)
        right_val = speed + (delta_angle * self.turn_sensitivity)

        left_signal = int(max(0, min(255, left_val)))
        right_signal = int(max(0, min(255, right_val)))

        return left_signal, right_signal

    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        if not distances:
            self.left_motor_signal = int(self.base_pwm)
            self.right_motor_signal = int(self.base_pwm)
            return self.left_motor_signal, self.right_motor_signal

        min_idx, max_idx = self.find_min_max(distances)
        min_dist = distances[min_idx]
        front_dist = distances[1] if len(distances) > 1 else min_dist

        if front_dist <= self.stop_distance:
            speed = 0.0
        elif front_dist >= self.slow_distance:
            speed = self.base_pwm
        else:
            speed = self.base_pwm * (
                (front_dist - self.stop_distance)
                / (self.slow_distance - self.stop_distance)
            )

        if min_dist < self.obstacle_threshold:
            delta_angle = self.calculate_evasive_delta(max_idx, distances)
            self.left_motor_signal, self.right_motor_signal = (
                self.calculate_motor_signals(delta_angle, speed)
            )
        else:
            self.left_motor_signal = int(speed)
            self.right_motor_signal = int(speed)

        return self.left_motor_signal, self.right_motor_signal
