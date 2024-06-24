from piegonote import Component
import pygame as pg


class SquareRenderer(Component):
    size: int = 32
    color: str = "red"

    def init(self):
        self._surface = pg.Surface((self.size, self.size))
        self._surface.fill(self.color)

    def render(self):
        # print(self.active_camera.world_position_to_screen_position(self.topleft_position))

        if self.rotation == 0:
            self.game.camera.blit(self._surface, self.pixel_position)
        else:
            rotated = pg.transform.rotate(self._surface, self.rotation)
            self.game.camera.blit(rotated, self.pixel_position)
