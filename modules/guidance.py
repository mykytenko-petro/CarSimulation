from random import randint
from typing import Sequence, Tuple


class GuidanceAlgorithm:
    def __init__(
        self,
        base_pwm: float = 180.0,
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

    # алгоритм для визначення найменшого та найбільшого індексу сенсорів за значенням
    def find_min_max(self, distances: Sequence[float]) -> Tuple[int, int]:
        max_distance, max_index = distances[0], 0
        min_distance, min_index = distances[0], 0

        for index, dist in enumerate(distances):
            if dist >= max_distance:
                max_distance, max_index = dist, index
            if dist <= min_distance:
                min_distance, min_index = dist, index

        return min_index, max_index

    # алгоритм знаходження кута вільного місця
    def calculate_evasive_delta(
        self,
        max_idx: int,
        distances: Sequence[float]
    ) -> float:
        # переаодимо максимальний кут відхилу в int
        max_ang = int(self.max_angle)

        # якщо максимальнимальна дистанція з лівого датчика то відхиляємося на випадковий кут вліво
        if max_idx == 0:
            return float(randint(-max_ang, 0))
        # якщо максимальнимальна дистанція з центрального датчика то визначаємо де більше місця з обох сторін і повертаємо туди
        elif max_idx == 1:
            left_dist = distances[0]
            right_dist = distances[2]

            if left_dist > right_dist:
                return float(randint(-max_ang, 0))
            else:
                return float(randint(0, max_ang))
        # якщо максимальнимальна дистанція з правого датчика то відхиляємося на випадковий кут впарво
        else:
            return float(randint(0, max_ang))

    # алгоритм переведення кута та швидкості у сигнали для моторів
    def calculate_motor_signals(
        self,
        delta_angle: float,
        speed: float
    ) -> Tuple[int, int]:
        # розрахунок різниці швидкості
        left_val = speed - (delta_angle * self.turn_sensitivity)
        right_val = speed + (delta_angle * self.turn_sensitivity)

        # обмежуємо занчення до діапазону (0-255)
        left_signal = int(max(0, min(255, left_val)))
        right_signal = int(max(0, min(255, right_val)))

        return left_signal, right_signal

    # алгоритм для визначення швидкості моторів
    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        # знаходимо індекси найменшого та найбільшого за значенням сенсори
        min_idx, max_idx = self.find_min_max(distances)
        # записуємо мінімальну дистанцію
        min_dist = distances[min_idx]

        # записуємо дистанцію середнього датчика
        front_dist = distances[1]

        # алгоритм визначення швидкості
        # якщо дистанція середнього датчика менше або дорівнює дистанції зупинки то зупиняємося
        if front_dist <= self.stop_distance:
            speed = 0.0
        # якщо дистанція середнього датчика більше або дорівнює дистанції сповільнення то їдемо на базовій швидкості
        elif front_dist >= self.slow_distance:
            speed = self.base_pwm
        # в іншому випадку плавно сповільнюємо швидкість залежно від дистанції до перешкоди
        else:
            speed = self.base_pwm * (
                (front_dist - self.stop_distance)
                / (self.slow_distance - self.stop_distance)
            )

        # алгоритм маневрування
        # якщо мінімальна дистанція менше дистанції реагування на перешкоду то:
        # 1. вираховуємо кут який буде напрямляти до найвільнішого місця
        # 2. розраховуємо швидкість для моторів для повороту (одне колесо сповільнюєтся, інше прискорюєтся)
        if min_dist < self.obstacle_threshold:
            delta_angle = self.calculate_evasive_delta(max_idx, distances)
            self.left_motor_signal, self.right_motor_signal = (
                self.calculate_motor_signals(delta_angle, speed)
            )
        # в іншому випадку просто їдемо уперед
        else:
            self.left_motor_signal = int(speed)
            self.right_motor_signal = int(speed)

        return self.left_motor_signal, self.right_motor_signal
