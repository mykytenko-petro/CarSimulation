import pygame

from .config import SPAWN_COLOR


class Map:
    def __init__(self, image_filepath: str) -> None:
        self.image = pygame.image.load(image_filepath).convert_alpha()
        self.spawns = self._load_spawns()

    def _load_spawns(self) -> list[pygame.Rect]:
        spawns: list[pygame.Rect] = []
        width, height = self.image.get_size()
        target_rgb = (SPAWN_COLOR.r, SPAWN_COLOR.g, SPAWN_COLOR.b)

        # 1. Collect all pixels matching the target color
        target_pixels: set[tuple[int, int]] = set()
        for x in range(width):
            for y in range(height):
                pixel = self.image.get_at((x, y))
                if (pixel.r, pixel.g, pixel.b) == target_rgb:
                    target_pixels.add((x, y))

        # 2. Group adjacent pixels into single rects
        while target_pixels:
            start_x, start_y = target_pixels.pop()
            min_x, max_x = start_x, start_x
            min_y, max_y = start_y, start_y
            
            queue = [(start_x, start_y)]
            
            while queue:
                cx, cy = queue.pop(0)
                
                # Expand bounding box to encompass this pixel
                if cx < min_x: min_x = cx
                if cx > max_x: max_x = cx
                if cy < min_y: min_y = cy
                if cy > max_y: max_y = cy
                
                # Check 4 neighboring pixels (Up, Down, Left, Right)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor = (cx + dx, cy + dy)
                    if neighbor in target_pixels:
                        target_pixels.remove(neighbor)  # Mark as visited
                        queue.append(neighbor)
                        
            # Create one bounding rect for the entire color drop
            width_rect = max_x - min_x + 1
            height_rect = max_y - min_y + 1
            spawns.append(pygame.Rect(min_x, min_y, width_rect, height_rect))

        return spawns

    def draw(self, surface: pygame.Surface, position: tuple[int, int] = (0, 0)) -> None:
        surface.blit(self.image, position)