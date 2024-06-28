from abc import ABCMeta, abstractmethod

from pygame import Rect, Vector2

from pigeonote.core import Component


class Collider(Component, metaclass=ABCMeta):
    offset: Vector2 = Vector2(0, 0)

    @property
    def collider_position(self):
        return self.position + self.offset

    def _fire_on_collision_enter(self, other: "Collider"):
        for component in self.entity.get_components():
            if component is not self and hasattr(component, "on_collision_enter"):
                getattr(component, "on_collision_enter")(other)

    def _fire_on_collision_exit(self, other: "Collider"):
        for component in self.entity.get_components():
            if component is not self and hasattr(component, "on_collision_exit"):
                getattr(component, "on_collision_exit")(other)

    def init(self):
        from pigeonote.core.physics import Physics

        self._PHYSICS = Physics.get_instance()
        self._PHYSICS.internal_add_collider(self)

        self._current_collisions = set[Collider]()

    def update(self):
        frame_collisions = set(self._PHYSICS.internal_check_collisions(self))

        to_remove = list[Collider]()

        for other in self._current_collisions:
            if other not in frame_collisions:
                to_remove.append(other)
                self._fire_on_collision_exit(other)

        for removed_collider in to_remove:
            self._current_collisions.remove(removed_collider)

        for other in frame_collisions:
            if other not in self._current_collisions:
                self._current_collisions.add(other)
                self._fire_on_collision_enter(other)

    def on_destroy(self):
        self._PHYSICS.internal_remove_collider(self)

    @abstractmethod
    def check_rect_overlap(self, rect: Rect):
        pass

    # @abstractmethod
    # def check_circle_overlap(self):
    #     pass
