from pigeonote import Component, Rect, Surface
import pygame as pg


class SquareRenderer(Component):
    size: int = 32
    color: str = "red"
    layer: int = 0

    def init(self):
        self._surface = Surface((self.size, self.size))
        self._surface.fill(self.color)

    def render(self):
        if not self._is_init:
            self.init()
            self._is_init = True

        # Using the Rect below because it can easily calculate for us what the "topleft"
        # coordinate should be for `pixel_position` as the center.

        if self.rotation == 0:
            rect = Rect((0, 0), self._surface.size)
            rect.center = self.pixel_position
            self.camera.blit(self._surface, rect.topleft, layer=self.layer)

        else:
            rotated = pg.transform.rotate(self._surface, self.rotation)
            rect = Rect((0, 0), rotated.size)
            rect.center = self.pixel_position
            self.camera.blit(rotated, rect.topleft, layer=self.layer)
