from pathlib import Path
from pigeonote import Component, Coordinate, get_coords_as_tuple

import pygame as pg

from pigeonote.core.entity import Entity


TilenameType = str | tuple[int, int]


def _coords_as_int_tuple(coords: Coordinate):
    coords_tup = get_coords_as_tuple(coords)
    return int(coords_tup[0]), int(coords_tup[1])


class TilemapRenderer(Component):
    tileset: dict[TilenameType, pg.Surface] = dict()
    tile_size: int = 10
    layer: int = 0
    draw_grid: bool = False

    def __init__(self, component_id: int, parent: Entity) -> None:
        super().__init__(component_id, parent)
        self._tiles = dict[tuple[int, int], TilenameType]()

    def load_tilset_from_file(self, file: Path | str, tilesize: int):
        tilset_image = pg.image.load(file).convert_alpha()

        msk = pg.Mask((tilesize, tilesize))
        msk.fill()

        for px in range(0, tilset_image.width, tilesize):
            for py in range(0, tilset_image.height, tilesize):
                tile_coords = px // tilesize, py // tilesize

                tile_rect = pg.Rect((px, py), (tilesize, tilesize))

                current_tile = pg.Surface((tilesize, tilesize), pg.SRCALPHA)
                current_tile.blit(tilset_image, (0, 0), tile_rect)

                if msk.overlap(pg.mask.from_surface(current_tile), (0, 0)):
                    self.tileset[tile_coords] = current_tile

    def set_tile(self, coords: Coordinate, tile_name: TilenameType | None = None):
        int_coords = _coords_as_int_tuple(coords)

        if tile_name is None:
            if int_coords in self._tiles:
                self._tiles.pop(int_coords)
        else:
            self._tiles[int_coords] = tile_name

    def clear_tile(self, coords: Coordinate):
        self.set_tile(coords, None)

    def has_tile_at(self, coords: Coordinate) -> bool:
        return _coords_as_int_tuple(coords) in self._tiles

    def get_tile_at(self, coords: Coordinate) -> TilenameType | None:
        coords_tup = _coords_as_int_tuple(coords)
        return self._tiles.get(coords_tup, None)

    def world_coords_of_tile(self, coords: Coordinate):
        """
        Return the world coordinates of the tile at `coords`.
        """
        int_coords = _coords_as_int_tuple(coords)
        return int_coords[0] * self.tile_size, int_coords[1] * self.tile_size

    def get_tile_coords_from_world_position(self, world_position: Coordinate) -> tuple[int, int]:
        world_position = get_coords_as_tuple(world_position)

        # Ignoring an analyzer error. Somewhy it can't figure out that `//` will always return an int.
        return world_position[0] // self.tile_size, world_position[1] // self.tile_size  # type: ignore

    def init(self):
        for tile_name in self.tileset:
            surface = self.tileset[tile_name]

            if surface.width != surface.height:
                self.log(f"size of `{tile_name}`s size isn't a square: {surface.width}x{surface.height}.")

            elif surface.width != self.tile_size:
                self.log(
                    f"size of `{tile_name}` is {surface.width}x{surface.height}, which isn't {self.tile_size}x{self.tile_size}. "
                    + "Scaling down..."
                )
                self.tileset[tile_name] = pg.transform.scale(surface, (self.tile_size, self.tile_size))

    def render(self):
        camera = self.game.camera
        visible_world_area = camera.area
        topleft, bottomright = (
            visible_world_area.topleft,
            visible_world_area.bottomright,
        )

        topleft_tile_x, topleft_tile_y = (
            int(topleft[0] // self.tile_size),
            int(topleft[1] // self.tile_size),
        )
        bottomright_tile_x, bottomright_tile_y = (
            int((bottomright[0] + self.tile_size - 1) // self.tile_size),
            int((bottomright[1] + self.tile_size - 1) // self.tile_size),
        )

        for y in range(topleft_tile_y, bottomright_tile_y):
            for x in range(topleft_tile_x, bottomright_tile_x):
                if tile_image_name := self._tiles.get((x, y), None):
                    tile_image = self.tileset[tile_image_name]

                    tile_world_pos = self.world_coords_of_tile((x, y))
                    camera.blit(tile_image, tile_world_pos, layer=self.layer)

                    if self.draw_grid:
                        tile_rect = pg.Rect(tile_world_pos, (tile_image.size))
                        camera.draw_rect(tile_rect, "black", 1, layer=self.layer)
