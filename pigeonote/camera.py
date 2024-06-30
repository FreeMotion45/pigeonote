from collections import defaultdict
from typing import Optional, Callable

import pygame as pg
from pygame import Rect, FRect, Vector2, Surface

from pigeonote.draw import draw_rectangle_outline
from pigeonote.types import Color, Coordinate, get_coords_as_vector2


class Camera2D:
    def __init__(self, area: Optional[Rect | FRect] = None) -> None:
        self._area = area or Rect((0, 0), pg.display.get_surface().get_size())
        self._surface = Surface(self._area.size)

        self._layering: dict[int, list[Callable[[], None]]] = defaultdict(list)

    @property
    def area(self):
        return self._area.copy()

    @property
    def center(self):
        return Vector2(self._area.center)

    @center.setter
    def center(self, position: Coordinate):
        self._area.center = position

    def clean_surface(self):
        self._surface.fill("black")

    def get_rendered_surface(self):
        return self._surface

    def render_frame(self):
        render_order = sorted(self._layering)

        for layer_index in render_order:
            for draw_task in self._layering[layer_index]:
                draw_task()

        self._layering.clear()
        return self._surface

    def world_position_to_screen_position(self, world_pos: Coordinate) -> Vector2:
        return get_coords_as_vector2(world_pos) - Vector2(self._area.topleft)

    def world_rect_to_screen_rect(self, world_rect: Rect | FRect) -> Rect | FRect:
        screen_pos = self.world_position_to_screen_position(world_rect.topleft)
        if isinstance(world_rect, Rect):
            return Rect(screen_pos, world_rect.size)

        if isinstance(world_rect, FRect):
            return FRect(screen_pos, world_rect.size)

    def screen_position_to_world_position(self, screen_pos: Coordinate):
        return get_coords_as_vector2(screen_pos) + Vector2(self._area.topleft)

    def screen_rect_to_world_rect(self, screen_pos: Rect | FRect) -> Rect | FRect:
        if isinstance(screen_pos, Rect):
            return Rect(self.screen_position_to_world_position(screen_pos.topleft), screen_pos.size)

        if isinstance(screen_pos, FRect):
            return FRect(self.screen_position_to_world_position(screen_pos.topleft), screen_pos.size)

    def blit(self, surface: Surface, world_position: Coordinate, layer: int = 0):
        def _perform_blit():
            self._surface.blit(surface, self.world_position_to_screen_position(world_position))

        self._layering[layer].append(_perform_blit)

    def fill(self, color: Color, area: Rect | FRect):
        self._surface.fill(color, self.world_rect_to_screen_rect(area))

    def draw_line(self, point1: Coordinate, point2: Coordinate, color: Color, layer: int = 0):
        def _perform_draw_line():
            p1_screen_pos = self.world_position_to_screen_position(point1)
            p2_screen_pos = self.world_position_to_screen_position(point2)
            pg.draw.line(self._surface, color, p1_screen_pos, p2_screen_pos)

        self._layering[layer].append(_perform_draw_line)

    def draw_rect_outline(self, rect: Rect | FRect, color: Color = "green", outline_width: int = 1):
        rect = rect.copy()
        screen_rectangle = self.world_rect_to_screen_rect(rect)
        draw_rectangle_outline(self._surface, screen_rectangle, outline_width, color)

    def draw_rect(
        self, rect: Rect | FRect, color: Color = "green", width: float = 0, border_radius: float = -1, layer: int = 0
    ):
        rect = rect.copy()

        def _perform_draw_rect():
            screen_rect = self.world_rect_to_screen_rect(rect)
            pg.draw.rect(self._surface, color, screen_rect, width=round(width), border_radius=round(border_radius))

        self._layering[layer].append(_perform_draw_rect)

    def draw_circle(self, center: Coordinate, radius: float, color: Color, width: float = 0, layer: int = 0):
        def _perform_draw_circle():
            center_screen_pos = self.world_position_to_screen_position(center)
            pg.draw.circle(self._surface, color, center_screen_pos, radius, width=round(width))

        self._layering[layer].append(_perform_draw_circle)
