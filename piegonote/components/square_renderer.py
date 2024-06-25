from piegonote import Component
import pygame as pg


class SquareRenderer(Component):
    size: int = 32
    color: str = "red"

    def init(self):
        self._surface = pg.Surface((self.size, self.size))
        self._surface.fill(self.color)

    def render(self):        
        # Using the Rect below because it can easily calculate for us what the "topleft"
        # coordinate should be for `pixel_position` as the center.

        if self.rotation == 0:
            rect = pg.Rect((0, 0), self._surface.size)
            rect.center = self.pixel_position
            self.game.camera.blit(self._surface, rect.topleft)

        else:
            rotated = pg.transform.rotate(self._surface, self.rotation)
            rect = pg.Rect((0, 0), rotated.size)
            rect.center = self.pixel_position
            self.game.camera.blit(rotated, rect.topleft)
