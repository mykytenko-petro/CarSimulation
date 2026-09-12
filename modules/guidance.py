from random import randint
from typing import Sequence, Tuple


class GuidanceAlgorithm:
    def __init__(
        self,
        base_pwm: float = 180.0,
        max_angle: float = 15.0,
        turn_sensitivity: float = 4.0,
        obstacle_threshold: float = 80.0,
    ) -> None:
        self.base_pwm = base_pwm
        self.max_angle = max_angle
        self.turn_sensitivity = turn_sensitivity
        self.obstacle_threshold = obstacle_threshold

        self.left_motor_signal: int = 0
        self.right_motor_signal: int = 0

    def find_min_max(self, distances: Sequence[float]) -> Tuple[int, int]:
        """Find indices of minimum and maximum sensor distances."""
        if not distances:
            return 0, 0

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
        """
        Calculate the steering delta angle based on which sector has the most clearance.
        - Index 0: Left sensor
        - Index 1: Center sensor
        - Index 2: Right sensor
        """
        max_ang = int(self.max_angle)
        if max_idx == 0:
            # Turn left (negative angle)
            return float(randint(-max_ang, 0))
        elif max_idx == 1:
            # Center is clear, pick side with greater clearance
            left_dist = distances[0] if len(distances) > 0 else 0
            right_dist = distances[2] if len(distances) > 2 else 0
            if left_dist > right_dist:
                return float(randint(-max_ang, 0))
            else:
                return float(randint(0, max_ang))
        else:
            # Turn right (positive angle)
            return float(randint(0, max_ang))

    def calculate_motor_signals(self, delta_angle: float) -> Tuple[int, int]:
        """Convert a steering delta angle into clamped [0, 255] PWM motor signals."""
        left_val = self.base_pwm - (delta_angle * self.turn_sensitivity)
        right_val = self.base_pwm + (delta_angle * self.turn_sensitivity)

        left_signal = int(max(0, min(255, left_val)))
        right_signal = int(max(0, min(255, right_val)))

        return left_signal, right_signal

    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        """
        Run one guidance cycle given sensor distance readings.
        Returns: (left_motor_signal, right_motor_signal)
        """
        if not distances:
            self.left_motor_signal = int(self.base_pwm)
            self.right_motor_signal = int(self.base_pwm)
            return self.left_motor_signal, self.right_motor_signal

        min_idx, max_idx = self.find_min_max(distances)

        if distances[min_idx] < self.obstacle_threshold:
            delta_angle = self.calculate_evasive_delta(max_idx, distances)
            self.left_motor_signal, self.right_motor_signal = (
                self.calculate_motor_signals(delta_angle)
            )
        else:
            self.left_motor_signal = int(self.base_pwm)
            self.right_motor_signal = int(self.base_pwm)

        return self.left_motor_signal, self.right_motor_signal
