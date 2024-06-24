from typing import TYPE_CHECKING, Optional

import pygame as pg

from piegonote import Component, Entity, Game

if TYPE_CHECKING:
    from piegonote import Entity


class SpriteRenderer(Component):
    def __init__(self, component_id: int, parent: Entity) -> None:
        super().__init__(component_id, parent)
        self.sprite_surface: Optional[pg.Surface] = None

    def set_sprite(self, sprite: Optional[pg.Surface]):
        self.sprite_surface = sprite

    def render(self):
        if self.sprite_surface:
            if self.rotation == 0:
                self.game.camera.blit(self.sprite_surface, self.pixel_position)
            else:
                rotated = pg.transform.rotate(self.sprite_surface, self.rotation)
                self.game.camera.blit(rotated, self.pixel_position)
