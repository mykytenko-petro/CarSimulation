from enum import IntEnum
from typing import Sequence, Tuple


class SensorIndex(IntEnum):
    FAR_LEFT = 0
    MID_LEFT = 1
    CENTER = 2
    MID_RIGHT = 3
    FAR_RIGHT = 4


class GuidanceAlgorithm:
    def __init__(
        self,
        base_pwm: float = 230.0,
        max_steering_signal: float = 100.0,

        obstacle_threshold: float = 100.0,
        stop_distance: float = 0.0,
        slow_distance: float = 10.0,
    ) -> None:
        self.base_pwm = base_pwm
        self.max_steering_signal = max_steering_signal
        self.obstacle_threshold = obstacle_threshold
        self.stop_distance = stop_distance
        self.slow_distance = slow_distance

    def calculate_steering_signal(self, distances: Sequence[float]) -> int:
        # Різниця між правою та лівою стороною із урахуванням вагових коефіцієнтів
        diff = (
            (distances[SensorIndex.MID_RIGHT] - distances[SensorIndex.MID_LEFT]) +
            (distances[SensorIndex.FAR_RIGHT] - distances[SensorIndex.FAR_LEFT])
        )
        raw_steering = diff 
        
        # Обмеження діапазону
        clamped = max(-self.max_steering_signal, min(self.max_steering_signal, raw_steering))
        return int(clamped)

    def calculate_drive_signal(self, front_dist: float, steering_abs: float) -> int:
        # 1. Линійне уповільнення при наближенні до перешкоди
        if front_dist <= self.stop_distance:
            speed = 0.0
        elif front_dist >= self.slow_distance:
            speed = self.base_pwm
        else:
            ratio = (front_dist - self.stop_distance) / (self.slow_distance - self.stop_distance)
            speed = self.base_pwm * ratio

        # 2. Динамічне скидання швидкості під час маневрування (Dynamic Cornering)
        turn_ratio = steering_abs / self.max_steering_signal
        speed *= (1.0 - turn_ratio * 0.45)

        return int(max(0, min(255, speed)))

    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        # Визначаємо мінімальну відстань у передньому секторі
        front_dist = min(
            distances[SensorIndex.MID_LEFT],
            distances[SensorIndex.CENTER],
            distances[SensorIndex.MID_RIGHT],
        )

        # Кермо повертає, тільки якщо в полі зору є перешкода
        if min(distances) < self.obstacle_threshold:
            steering_signal = self.calculate_steering_signal(distances)
        else:
            steering_signal = 0

        drive_signal = self.calculate_drive_signal(front_dist, abs(steering_signal))

        return drive_signal, steering_signal