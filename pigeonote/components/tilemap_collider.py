from pygame import Rect

from pigeonote.components import TilemapRenderer
from pigeonote.core import Collider


class TilemapCollider(Collider):
    def init(self):
        super().init()

        self._tilemap = self.entity.get_component_by_type(TilemapRenderer)

        if self._tilemap is None:
            self.log(f"No {TilemapRenderer.__name__} was assigned to {self.entity.name}.")

    def update(self):
        # TODO: Weird stuff happens in the super() update.
        # I can't think of the correct architecture to generally find a collision between
        # 2 colliders. So meanwhile objects that have this component won't receive collision events.
        # but who the hell is gonna place this on a player or something that moves lol.
        pass

    def check_rect_overlap(self, rect: Rect):
        if self._tilemap is None:
            return

        tilesize = self._tilemap.tile_size
        camera = self.camera

        visible_world_area = camera.area
        topleft, bottomright = (
            visible_world_area.topleft,
            visible_world_area.bottomright,
        )

        topleft_tile_x, topleft_tile_y = (
            topleft[0] // tilesize,
            topleft[1] // tilesize,
        )
        bottomright_tile_x, bottomright_tile_y = (
            bottomright[0] // tilesize,
            bottomright[1] // tilesize,
        )

        for y in range(topleft_tile_y, bottomright_tile_y):
            for x in range(topleft_tile_x, bottomright_tile_x):
                if self._tilemap.has_tile_at((x, y)):
                    tile_rect = Rect(
                        self._tilemap.world_coords_of_tile((x, y)),
                        (tilesize, tilesize),
                    )

                    if tile_rect.colliderect(rect):
                        return True

        return False
