from typing import Optional, Sequence, Tuple

import pygame

from .car_sim import CarSimulation
from .parts.ray import Ray


class CarRenderer:
    COLOR_NORMAL: Tuple[int, int, int] = (0, 150, 255)
    COLOR_COLLIDING: Tuple[int, int, int] = (255, 50, 50)
    COLOR_RAY: Tuple[int, int, int] = (255, 0, 0)
    COLOR_RAY_TERMINUS: Tuple[int, int, int] = (255, 255, 0)
    COLOR_TEXT: Tuple[int, int, int] = (255, 255, 255)

    # Кольорова палітра для елементів
    COLOR_NORMAL: Tuple[int, int, int] = (0, 150, 255)       # Синій колір машинки за нормального руху
    COLOR_COLLIDING: Tuple[int, int, int] = (255, 50, 50)    # Червоний колір машинки під час зіткнення
    COLOR_RAY: Tuple[int, int, int] = (255, 0, 0)            # Червоний колір променів сенсорів
    COLOR_RAY_TERMINUS: Tuple[int, int, int] = (255, 255, 0) # Жовтий колір точки зіткнення променя з перешкодою
    COLOR_TEXT: Tuple[int, int, int] = (255, 255, 255)       # Білий колір тексту телеметрії

    def __init__(
        self,
        font_size: int = 14,
        show_rays: bool = True,
        show_telemetry: bool = True,
    ) -> None:
        self.show_rays = show_rays
        self.show_telemetry = show_telemetry
        self._font_size = font_size
        self._font: Optional[pygame.font.Font] = None

    def get_font(self) -> pygame.font.Font:
        if self._font is None:
            if not pygame.font.get_init():
                pygame.font.init()
            self._font = pygame.font.SysFont(None, self._font_size)
        return self._font

    def draw_rays(
        self,
        surface: pygame.Surface,
        center: Tuple[float, float],
        rays: Sequence[Ray],
    ) -> None:
        """
        Малює промені сенсорів машинки:
        лінію від центру авто до точки контакту та кружок на кінці променя.
        """
        for ray in rays:
            # Лінія променя від центру машинки до точки зустрічі з перешкодою
            pygame.draw.line(surface, self.COLOR_RAY, center, ray.terminus, 1)
            # Точка контакту на кінці променя
            pygame.draw.circle(
                surface,
                self.COLOR_RAY_TERMINUS,
                (int(ray.terminus[0]), int(ray.terminus[1])),
                3,
            )

    def draw_body(
        self,
        surface: pygame.Surface,
        center: Tuple[float, float],
        angle: float,
        length: float,
        width: float,
        is_colliding: bool,
    ) -> None:
        """
        Малює корпус машинки з урахуванням її повороту та стану зіткнення.
        """
        # Вибираємо колір залежно від того, чи є зіткнення зі стіною або іншою машиною
        body_color = self.COLOR_COLLIDING if is_colliding else self.COLOR_NORMAL

        # Створюємо тимчасову прозору поверхню для корпусу прямокутної форми
        rect_surface = pygame.Surface((length, width), pygame.SRCALPHA)
        rect_surface.fill(body_color)

        # Повертаємо поверхню на кут машинки (знак мінус через систему координат екрана)
        rotated_surface = pygame.transform.rotate(rect_surface, -angle)
        rect = rotated_surface.get_rect(center=center)

        # Відображаємо повернутий корпус на основну поверхню
        surface.blit(rotated_surface, rect.topleft)

    def draw_telemetry(
        self,
        surface: pygame.Surface,
        center: Tuple[float, float],
        width: float,
        left_signal: int,
        right_signal: int,
    ) -> None:
        """
        Виводить над машинкою текстові дані телеметрії (ШІМ лівого та правого моторів).
        """
        font = self.get_font()
        sig_text = font.render(
            f"L:{left_signal} R:{right_signal}", True, self.COLOR_TEXT
        )
        # Зміщуємо напис трохи вище корпусу машинки
        surface.blit(sig_text, (center[0] - 20, center[1] - width - 12))

    def draw(
        self,
        surface: pygame.Surface,
        sim: CarSimulation,
        left_signal: int,
        right_signal: int,
    ) -> None:
        center = sim.get_center()

        # 1. Малювання променів сенсорів
        if self.show_rays:
            self.draw_rays(surface, center, sim.rays)

        # 2. Малювання прямокутного корпусу авто
        self.draw_body(
            surface,
            center,
            sim.angle,
            sim.length,
            sim.width,
            sim.is_colliding,
        )

        # 3. Малювання телеметрії моторів
        if self.show_telemetry:
            self.draw_telemetry(
                surface, center, sim.width, left_signal, right_signal
            )
