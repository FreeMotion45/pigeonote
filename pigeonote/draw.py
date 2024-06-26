import pygame as pg

from pigeonote.types import Color


def draw_rectangle_outline(surface: pg.Surface, rect: pg.Rect, width: int, color: Color):
    # Draw horizontal lines (top and bottom)
    pg.draw.rect(surface, color, pg.Rect(rect.topleft, (rect.width, width)))
    pg.draw.rect(surface, color, pg.Rect((rect.left, rect.bottom - width), (rect.width, width)))

    # Draw vertical lines (left and right)
    pg.draw.rect(surface, color, pg.Rect(rect.topleft, (width, rect.height)))
    pg.draw.rect(surface, color, pg.Rect((rect.right - width, rect.top), (width, rect.height)))
