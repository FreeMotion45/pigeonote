from pigeonote import Component, Color


class CircleRenderer(Component):
    radius: float = 10
    color: Color = "white"
    width: float = 0

    def render(self):
        self.width = self.width if self.width >= 0 else 0
        self.camera.draw_circle(self.position, self.radius, self.color, width=self.width)
