from pigeonote import Component, Color, Surface, Rect
import pygame as pg


class CircleRenderer(Component):
    radius: float = 10
    color: Color = "white"
    width: float = 0

    layer: int = 0

    def render(self):
        self.width = self.width if self.width >= 0 else 0
        self.camera.draw_circle(self.position, self.radius, self.color, width=self.width, layer=self.layer)
