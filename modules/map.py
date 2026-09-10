import pygame
from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer, TiledObjectGroup


class Map:
    def __init__(self, tmx_filepath: str) -> None:
        self.tmx_data = load_pygame(tmx_filepath)
        
        self.walls = self._load_walls()
        self.spawns = self._load_spawns()

    def _load_walls(self) -> list[pygame.Rect]:
        walls: list[pygame.Rect] = []
        layer = self.tmx_data.get_layer_by_name("Walls")

        if isinstance(layer, TiledTileLayer):
            for x, y, gid in layer: # type: ignore
                if gid != 0:
                    rect = pygame.Rect(
                        x * self.tmx_data.tilewidth,
                        y * self.tmx_data.tileheight,
                        self.tmx_data.tilewidth,
                        self.tmx_data.tileheight,
                    )
                    walls.append(rect)

        return walls

    def _load_spawns(self) -> list[pygame.Rect]:
        spawns: list[pygame.Rect] = []
        layer = self.tmx_data.get_layer_by_name("Spawns")

        if isinstance(layer, TiledTileLayer):
            for x, y, gid in layer: # type: ignore
                if gid != 0:
                    spawns.append(
                        pygame.Rect(
                            x * self.tmx_data.tilewidth,
                            y * self.tmx_data.tileheight,
                            self.tmx_data.tilewidth,
                            self.tmx_data.tileheight,
                        )
                    )
        elif isinstance(layer, TiledObjectGroup):
            for obj in layer:
                spawns.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        return spawns

    def draw(self, surface: pygame.Surface) -> None:
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, TiledTileLayer):
                for x, y, gid in layer: # type: ignore
                    tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        surface.blit(
                            tile_image,
                            (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight),
                        )