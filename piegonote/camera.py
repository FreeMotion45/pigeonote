from typing import Optional

import pygame as pg

from piegonote.draw import draw_rectangle_outline
from piegonote.types import Color, Coordinate, get_coords_as_vector2


class Camera2D:
    """
    I think the best way, is that the camera doesn't actually do any rendering when the
    draw/blit/whatever function that renders is called. Instead, the camera should remember
    what it needs to render this frame, but only actually do the rendering using a final: `render_frame` method.

    This way we no will longer need the separation of render/update method in the component class
    because the separation will occur within the framework.
    """

    def __init__(self, area: Optional[pg.Rect] = None) -> None:
        self._area = area or pg.Rect((0, 0), pg.display.get_surface().get_size())
        self._surface = pg.Surface(self._area.size)

    @property
    def area(self):
        return self._area.copy()

    @property
    def center(self):
        return pg.Vector2(self._area.center)

    @center.setter
    def center(self, position: Coordinate):
        self._area.center = position

    def clean_surface(self):
        self._surface.fill("black")

    def get_rendered_surface(self):
        return self._surface

    def world_position_to_screen_position(self, world_pos: Coordinate):
        return get_coords_as_vector2(world_pos) - pg.Vector2(self._area.topleft)

    def world_rect_to_screen_rect(self, world_rect: pg.Rect):
        return pg.Rect(self.world_position_to_screen_position(world_rect.topleft), world_rect.size)

    def screen_position_to_world_position(self, screen_pos: Coordinate):
        return get_coords_as_vector2(screen_pos) + pg.Vector2(self._area.topleft)

    def screen_rect_to_world_rect(self, screen_pos: pg.Rect):
        return pg.Rect(self.screen_position_to_world_position(screen_pos.topleft), screen_pos.size)

    def blit(self, surface: pg.Surface, world_position: Coordinate):
        self._surface.blit(surface, self.world_position_to_screen_position(world_position))

    def fill(self, color: Color, area: pg.Rect):
        self._surface.fill(color, self.world_rect_to_screen_rect(area))

    def draw_line(self, point1: Coordinate, point2: Coordinate, color: Color):
        p1_screen_pos = self.world_position_to_screen_position(point1)
        p2_screen_pos = self.world_position_to_screen_position(point2)
        pg.draw.line(self._surface, color, p1_screen_pos, p2_screen_pos)

    def draw_rect_outline(self, rect: pg.Rect, color: Color = "green", outline_width: int = 1):
        position = self.world_position_to_screen_position(rect.topleft)
        screen_rectangle = pg.Rect(position, rect.size)
        draw_rectangle_outline(self._surface, screen_rectangle, outline_width, color)

    def draw_circle(self, center: Coordinate, radius: float, color: Color, width: float = 0):
        center_screen_pos = self.world_position_to_screen_position(center)
        pg.draw.circle(self._surface, color, center_screen_pos, radius, width=round(width))
