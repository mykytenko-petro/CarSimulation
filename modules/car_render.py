"""
Pygame rendering module for vehicle presentation.

Handles:
- Visual setups, color palettes, and cached fonts
- Drawing sensor rays and endpoint markers
- Drawing rotated vehicle body with collision highlight
- Rendering telemetry overlay (motor signals)
"""

from typing import Optional, Sequence, Tuple

import pygame

from .car_sim import CarSimulation
from .parts import Ray


class CarRenderer:
    """
    Handles all Pygame-specific visual presentation and drawing for a car.
    """

    COLOR_NORMAL: Tuple[int, int, int] = (0, 150, 255)
    COLOR_COLLIDING: Tuple[int, int, int] = (255, 50, 50)
    COLOR_RAY: Tuple[int, int, int] = (255, 0, 0)
    COLOR_RAY_TERMINUS: Tuple[int, int, int] = (255, 255, 0)
    COLOR_TEXT: Tuple[int, int, int] = (255, 255, 255)

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

    @property
    def font(self) -> pygame.font.Font:
        """Lazily initialize and cache pygame font."""
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
        """Draw sensor rays and terminus indicators."""
        for ray in rays:
            pygame.draw.line(surface, self.COLOR_RAY, center, ray.terminus, 1)
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
        """Draw the rotated vehicle body rectangle."""
        body_color = self.COLOR_COLLIDING if is_colliding else self.COLOR_NORMAL
        rect_surface = pygame.Surface((length, width), pygame.SRCALPHA)
        rect_surface.fill(body_color)

        rotated_surface = pygame.transform.rotate(rect_surface, -angle)
        rect = rotated_surface.get_rect(center=center)
        surface.blit(rotated_surface, rect.topleft)

    def draw_telemetry(
        self,
        surface: pygame.Surface,
        center: Tuple[float, float],
        width: float,
        left_signal: int,
        right_signal: int,
    ) -> None:
        """Render motor PWM signals above the car."""
        sig_text = self.font.render(
            f"L:{left_signal} R:{right_signal}", True, self.COLOR_TEXT
        )
        surface.blit(
            sig_text, (center[0] - 20, center[1] - width - 12)
        )

    def draw(
        self,
        surface: pygame.Surface,
        sim: CarSimulation,
        left_signal: int,
        right_signal: int,
    ) -> None:
        """Render complete car representation on given Pygame surface."""
        center = sim.get_center()

        if self.show_rays:
            self.draw_rays(surface, center, sim.rays)

        self.draw_body(
            surface,
            center,
            sim.angle,
            sim.length,
            sim.width,
            sim.is_colliding,
        )

        if self.show_telemetry:
            self.draw_telemetry(
                surface, center, sim.width, left_signal, right_signal
            )
