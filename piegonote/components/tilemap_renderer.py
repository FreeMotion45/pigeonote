from piegonote import Component, Coordinate, get_coords_as_tuple

import pygame as pg


def _coords_as_int_tuple(coords: Coordinate):
    coords_tup = get_coords_as_tuple(coords)
    return int(coords_tup[0]), int(coords_tup[1])


class TilemapRenderer(Component):
    tileset: dict[str, pg.Surface] = dict()
    tile_size: int = 10

    def set_tile(self, coords: Coordinate, tile_name: str | None = None):
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

    def render_position_of_tile(self, coords: Coordinate):
        """
        Return the world coordinates of the tile at `coords`.
        """
        int_coords = _coords_as_int_tuple(coords)
        return int_coords[0] * self.tile_size, int_coords[1] * self.tile_size

    def get_tile_coords_from_world_position(self, world_position: Coordinate):
        return world_position[0] // self.tile_size, world_position[1] // self.tile_size

    def init(self):
        self._tiles = dict[tuple[int, int], str]()

        for tile_name in self.tileset:
            surface = self.tileset[tile_name]

            if surface.width != surface.height:
                self.log(
                    f"size of `{tile_name}`s size isn't a square: {surface.width}x{surface.height}."
                )

            elif surface.width != self.tile_size:
                self.log(
                    f"size of `{tile_name}` is {surface.width}x{surface.height}, which isn't {self.tile_size}x{self.tile_size}. "
                    + "Scaling down..."
                )
                self.tileset[tile_name] = pg.transform.scale(
                    surface, (self.tile_size, self.tile_size)
                )

        self._gen_x = 0
        self._gen_y = 0

        self.schedule(self.gen, 1)

    def gen(self):
        self._tiles[(self._gen_x, self._gen_y)] = "white"
        self._gen_x += 1
        self._gen_y += 1
        self.schedule(self.gen, 1)

    def render(self):
        camera = self.game.camera
        visible_world_area = camera.area
        topleft, bottomright = (
            visible_world_area.topleft,
            visible_world_area.bottomright,
        )

        topleft_tile_x, topleft_tile_y = (
            topleft[0] // self.tile_size,
            topleft[1] // self.tile_size,
        )
        bottomright_tile_x, bottomright_tile_y = (
            (bottomright[0] + self.tile_size - 1) // self.tile_size,
            (bottomright[1] + self.tile_size - 1) // self.tile_size,
        )

        for y in range(topleft_tile_y, bottomright_tile_y):
            for x in range(topleft_tile_x, bottomright_tile_x):
                if tile_image_name := self._tiles.get((x, y), None):
                    tile_image = self.tileset[tile_image_name]
                    camera.blit(tile_image, self.render_position_of_tile((x, y)))
