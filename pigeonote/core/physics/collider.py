from abc import ABCMeta, abstractmethod

from pygame import Rect, Vector2

from pigeonote.core import Component


class Collider(Component, metaclass=ABCMeta):
    offset: Vector2 = Vector2(0, 0)

    @property
    def collider_position(self):
        return self.position + self.offset

    def _get_components_with_enter_trigger(self):
        return [c for c in self.entity.get_components() if c is not self and hasattr(c, "on_collision_enter")]

    def _get_components_with_exit_trigger(self):
        return [c for c in self.entity.get_components() if c is not self and hasattr(c, "on_collision_exit")]

    def _fire_on_collision_enter(self, components: list[Component], others: list["Collider"]):
        for c in components:
            for o in others:
                getattr(c, "on_collision_enter")(o)

    def _fire_on_collision_exit(self, components: list[Component], others: list["Collider"]):
        for c in components:
            for o in others:
                getattr(c, "on_collision_exit")(o)

    def init(self):
        from pigeonote.core.physics import Physics

        self._PHYSICS = Physics.get_instance()
        self._PHYSICS.internal_add_collider(self)

        self._current_collisions = set[Collider]()

    def update(self):
        components_registered_for_enter = self._get_components_with_enter_trigger()
        components_registered_for_exit = self._get_components_with_exit_trigger()

        if not components_registered_for_enter and not components_registered_for_exit:
            return

        frame_collisions = set(self._PHYSICS.internal_check_collisions(self))

        exited_colliders = list[Collider]()

        for other in self._current_collisions:
            if other not in frame_collisions:
                exited_colliders.append(other)

        self._fire_on_collision_exit(components=components_registered_for_exit, others=exited_colliders)

        for removed_collider in exited_colliders:
            self._current_collisions.remove(removed_collider)

        entered_colliders = list[Collider]()

        for other in frame_collisions:
            if other not in self._current_collisions:
                self._current_collisions.add(other)
                entered_colliders.append(other)

        self._fire_on_collision_enter(components_registered_for_enter, others=entered_colliders)

    def on_destroy(self):
        self._PHYSICS.internal_remove_collider(self)

    @abstractmethod
    def check_rect_overlap(self, rect: Rect):
        pass

    # @abstractmethod
    # def check_circle_overlap(self):
    #     pass
