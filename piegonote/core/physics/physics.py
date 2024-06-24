from piegonote.core.physics import Collider
from pygame import Rect


class Physics:
    _instance: "Physics" = None

    @staticmethod
    def get_instance() -> "Physics":
        if Physics._instance is None:
            Physics._instance = Physics()

        return Physics._instance

    def __init__(self) -> None:
        self._colliders = set[Collider]()

    def internal_add_collider(self, collider: Collider):
        self._colliders.add(collider)

    def internal_remove_collider(self, collider: Collider):
        self._colliders.remove(collider)

    def internal_check_collisions(self, collider: Collider) -> list[Collider]:
        collisions = []
        rect = Rect(collider.collider_position, collider.size)

        for other in self._colliders:
            if other is not collider and other.check_rect_overlap(rect):
                collisions.append(other)

        return collisions

    def check_rect_overlap(self, rect: Rect) -> list[Collider]:
        return [c for c in self._colliders if c.check_rect_overlap(rect)]
