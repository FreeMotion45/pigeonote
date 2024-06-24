from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar
import abc
import pygame as pg

if TYPE_CHECKING:
    from piegonote import Entity
    from piegonote.core.entity import ComponentType


class Component(abc.ABC):
    def __init__(self, component_id: int, parent: "Entity") -> None:
        self._entity = parent
        self._component_id = component_id

        self._scheduled_callbacks = list[tuple[Callable, float]]()
        self._is_init = False
        self._destroyed = False

        self.is_key_down = self.game.is_key_down
        self.is_key_pressed = self.game.is_key_pressed
        self.is_key_up = self.game.is_key_up

        self.is_mouse_btn_down = self.game.is_mouse_btn_down
        self.is_mouse_btn_pressed = self.game.is_mouse_btn_pressed
        self.is_mouse_btn_up = self.game.is_mouse_btn_up

        self.find_entity_by_name = self.game.find_entity_by_name

    @property
    def is_destroyed(self):
        return self._destroyed

    @property
    def component_id(self):
        return self._component_id

    @property
    def game(self):
        return self._entity.game

    @property
    def entity(self):
        return self._entity

    @property
    def topleft_position(self):
        return self._entity.topleft_position

    @topleft_position.setter
    def topleft_position(self, new_topleft: pg.Vector2):
        self._entity.topleft_position = new_topleft

    @property
    def rotation(self):
        return self._entity.rotation

    @rotation.setter
    def rotation(self, new_rotation: float):
        self._entity.rotation = new_rotation

    @property
    def pixel_position(self):
        return self._entity.pixel_position

    @property
    def active_camera(self):
        """
        The currently active camera.
        """
        return self.game.camera

    @property
    def dt(self):
        """
        Return the delta time in seconds between the last frame and this one.
        """
        return self.game.dt

    def find_component_by_type(self, component_type: type["ComponentType"]):
        """
        Return a component of the given type available on the parent entity of this component.
        """
        return self.entity.get_component_by_type(component_type)

    def destroy(self, obj: Optional["Component | Entity"] = None):
        # This is here because we can't import Entity at top level due to circular dependency.
        from piegonote.core.entity import Entity

        if obj is None:
            obj = self

        if isinstance(obj, Component):
            if obj.is_destroyed:
                raise RuntimeError(
                    f"Cant destroy component {type(obj).__name__} of {obj.entity.name} because is already destroyed."
                )

            if obj is self:
                self._destroyed = True
                self.on_destroy()

            # Remove self from parent object.
            obj.entity.destroy_component(obj)

        elif isinstance(obj, Entity):
            self._entity.destroy()

    def schedule(self, callback: Callable[[], Any], seconds: float = 0):
        self._scheduled_callbacks.append((callback, seconds))

    def component_update(self):
        if not self._is_init:
            self.init()
            self._is_init = True

        for callback, time_left in self._scheduled_callbacks:
            if time_left <= 0:
                callback()

        self._scheduled_callbacks = [
            (cb, time_left - self.dt)
            for cb, time_left in self._scheduled_callbacks
            if time_left > 0
        ]

        self.update()

    def log(self, obj: str):
        print(f"[{type(self).__name__}] {obj}")

    def init(self):
        pass

    def setup(self):
        pass

    def update(self):
        pass

    def render(self):
        pass

    def on_destroy(self):
        pass
