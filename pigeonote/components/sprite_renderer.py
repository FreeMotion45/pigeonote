from typing import Optional

import pygame as pg

from pigeonote import Component


class SpriteRenderer(Component):
    sprite_surface: Optional[pg.Surface] = None
    layer: int = 0

    def init(self):
        self._mutated_surface: pg.Surface | None = None
        self._previous_mutated_rotation: int = 0

    def render(self):
        if not self._is_init:
            self.init()
            self._is_init = True
        
        if self.sprite_surface:
            if round(self.rotation) == 0:
                surface_to_blit = self.sprite_surface

            elif round(self.rotation) == self._previous_mutated_rotation and self._mutated_surface is not None:
                surface_to_blit = self._mutated_surface

            else:
                # PyGame rotates COUNTER CLOCKWISE. We need to provide negative value for clockwise rotation.
                pygame_dumb_rotation = self.rotation * (-1)
                rotated = pg.transform.rotate(self.sprite_surface, pygame_dumb_rotation)
                surface_to_blit = rotated

                self._mutated_surface = rotated
                self._previous_mutated_rotation = round(self.rotation)

            # Using the Rect below because it can easily calculate for us what the "topleft"
            # coordinate should be for `pixel_position` as the center.
            rect = pg.Rect((0, 0), surface_to_blit.size)
            rect.center = self.pixel_position

            self.game.camera.blit(surface_to_blit, rect.topleft, layer=self.layer)
