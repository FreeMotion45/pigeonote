from pygame import Rect
from pigeonote.core.physics import Collider


class RectCollider(Collider):
    auto_detect: bool = False
    size: tuple[int, int] = (32, 32)

    _draw_debug_outline: bool = False

    @property
    def width(self):
        return self.size[0]

    @width.setter
    def width(self, w: int):
        self.size = (w, self.size[1])

    @property
    def height(self):
        return self.size[1]

    @height.setter
    def height(self, h: int):
        self.size = (self.size[0], h)

    def init(self):
        super().init()

        if self.auto_detect:
            try:
                from pigeonote.components import SpriteRenderer

                renderer = self.entity.get_component_by_type(SpriteRenderer)
            except:
                return

            if renderer is not None and renderer.sprite_surface is not None:
                self.size = renderer.sprite_surface.size

    def update(self):
        super().update()

        if self._draw_debug_outline:
            this_rect = Rect((0,0), self.size)
            this_rect.center = self.position + self.offset
            
            self.camera.draw_rect(this_rect, width=2, layer=999)

    def check_rect_overlap(self, rect: Rect):
        this_rect = Rect((0,0), self.size)
        this_rect.center = self.position + self.offset
        
        return this_rect.colliderect(rect)
