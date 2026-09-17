from typing import Sequence, Tuple


class GuidanceAlgorithm:
    """Алгоритм навігації та оминання перешкод для машинки з кермуванням на

    основі Аккермана (3 сенсори).
    """

    def __init__(
        self,
        base_pwm: float = 180.0,
        max_steering_signal: float = 100.0,
        turn_sensitivity: float = 1.2,
        obstacle_threshold: float = 80.0,
        stop_distance: float = 0.0,
        slow_distance: float = 80.0,
    ) -> None:
        self.base_pwm = base_pwm
        self.max_steering_signal = max_steering_signal
        self.turn_sensitivity = turn_sensitivity
        self.obstacle_threshold = obstacle_threshold
        self.stop_distance = stop_distance
        self.slow_distance = slow_distance

        self.drive_signal: int = 0
        self.steering_signal: int = 0

    def calculate_steering_signal(
        self,
        distances: Sequence[float]
    ) -> int:
        """Обчислює сигнал для керування сервоприводом.

        - Негативний сигнал (< 0): поворот ліворуч - Позитивний сигнал (>
        0): поворот праворуч
        """
        left_dist = distances[0]
        right_dist = distances[2]

        # Обчислюємо різницю між даними лівого та правого сенсорів
        # Якщо зліва перешкода ближче (left < right), різниця > 0 -> повертаємо праворуч
        # Якщо справа перешкода ближче (right < left), різниця < 0 -> повертаємо ліворуч
        diff = right_dist - left_dist
        raw_steering = diff * self.turn_sensitivity

        # Обмежуємо значення сигналу в межах [-max_steering_signal, max_steering_signal]
        clamped_steering = max(
            -self.max_steering_signal,
            min(self.max_steering_signal, raw_steering)
        )

        return int(clamped_steering)

    def calculate_drive_signal(self, front_dist: float) -> int:
        """Розраховує швидкість для тягового мотора (поступальний рух) залежно

        від відстані до перешкоди спереду.
        """
        if front_dist <= self.stop_distance:
            speed = 0.0
        elif front_dist >= self.slow_distance:
            speed = self.base_pwm
        else:
            speed = self.base_pwm * (
                (front_dist - self.stop_distance)
                / (self.slow_distance - self.stop_distance)
            )

        return int(max(0, min(255, speed)))

    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        """Оновлює керуючі сигнали та повертає параметри:

        :return: (drive_signal, steering_signal)
        """
        front_dist = distances[1]
        min_dist = min(distances)

        # 1. Розрахунок швидкості руху
        self.drive_signal = self.calculate_drive_signal(front_dist)

        # 2. Розрахунок кута кермування
        if min_dist < self.obstacle_threshold:
            self.steering_signal = self.calculate_steering_signal(distances)
        else:
            # Якщо перешкод немає — колеса стоять прямо
            self.steering_signal = 0

        return self.drive_signal, self.steering_signal