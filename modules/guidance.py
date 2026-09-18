from typing import Sequence, Tuple


class GuidanceAlgorithm:
    """Алгоритм навігації та оминання перешкод для механізму Аккермана на

    основі 5 ToF-сенсорів.
    """

    def __init__(
        self,
        base_pwm: float = 180.0,
        min_pwm: float = 80.0,
        max_steering_signal: float = 100.0,
        turn_sensitivity: float = 1.2,
        obstacle_threshold: float = 100.0,
        stop_distance: float = 0.0,
        slow_distance: float = 90.0,
        # Вагові коефіцієнти: бічні сенсори відповідають за вирівнювання/виявлення бічних стін,
        # а діагональні — за напрямок повороту від перешкоди.
        w_diagonal: float = 1.0,
        w_side: float = 1,
    ) -> None:
        self.base_pwm = base_pwm
        self.min_pwm = min_pwm
        self.max_steering_signal = max_steering_signal
        self.turn_sensitivity = turn_sensitivity
        self.obstacle_threshold = obstacle_threshold
        self.stop_distance = stop_distance
        self.slow_distance = slow_distance

        self.w_diagonal = w_diagonal
        self.w_side = w_side

        self.drive_signal: int = 0
        self.steering_signal: int = 0

    def calculate_steering_signal(self, distances: Sequence[float]) -> int:
        """Обчислює кут кермування за 5 сенсорами:

        distances: [Far-Left (0), Mid-Left (1), Center (2), Mid-Right (3), Far-Right (4)]
        """
        d_far_left = distances[0]
        d_mid_left = distances[1]
        d_mid_right = distances[3]
        d_far_right = distances[4]

        # 1. Обчислюємо зважену різницю між лівою та правою сторонами (Virtual Field Vector)
        # Якщо праворуч вільніше (d_right > d_left) -> diff > 0 -> поворот праворуч
        # Якщо ліворуч вільніше (d_left > d_right) -> diff < 0 -> поворот ліворуч
        left_score = (d_mid_left * self.w_diagonal) + (d_far_left * self.w_side)
        right_score = (d_mid_right * self.w_diagonal) + (d_far_right * self.w_side)

        diff = right_score - left_score
        raw_steering = diff * self.turn_sensitivity

        # 2. Обмежуємо значення сигналу [-100, 100]
        clamped_steering = max(
            -self.max_steering_signal,
            min(self.max_steering_signal, raw_steering),
        )
        return int(clamped_steering)

    def calculate_drive_signal(
        self, front_dist: float, steering_abs: float
    ) -> int:
        """Обчислює поступальну швидкість тягового мотора."""
        # 1. Гальмування/сповільнення за даними центрального та діагональних сенсорів
        if front_dist <= self.stop_distance:
            speed = 0.0
        elif front_dist >= self.slow_distance:
            speed = self.base_pwm
        else:
            speed = self.base_pwm * (
                (front_dist - self.stop_distance)
                / (self.slow_distance - self.stop_distance)
            )

        # 2. Динамічне скидання швидкості під час маневрування (Dynamic Cornering)
        # У крутому повороті машинка уповільнюється, щоб не зрізати кути боковими стінами
        turn_ratio = steering_abs / self.max_steering_signal
        speed *= (1.0 - turn_ratio * 0.45)

        if speed > 0 and speed < self.min_pwm:
            speed = self.min_pwm

        return int(max(0, min(255, speed)))

    def update(self, distances: Sequence[float]) -> Tuple[int, int]:
        """Приймає масив з 5 відстаней: [Far-Left, Mid-Left, Center, Mid-Right,

        Far-Right] Повертає: (drive_signal, steering_signal)
        """
        center_dist = distances[2]
        
        # Для сповільнення переднім сектором використовуємо найменшу відстань серед 3 центральних
        front_sector_dist = min(distances[1], distances[2], distances[3])
        min_dist = min(distances)

        # 1. Розрахунок кута керма
        if min_dist < self.obstacle_threshold:
            self.steering_signal = self.calculate_steering_signal(distances)
        else:
            self.steering_signal = 0

        # 2. Розрахунок швидкості мотора
        self.drive_signal = self.calculate_drive_signal(
            front_sector_dist, abs(self.steering_signal)
        )

        return self.drive_signal, self.steering_signal