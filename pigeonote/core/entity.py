from typing import TYPE_CHECKING, Iterator, Optional, TypeVar
from pigeonote.core import Component
from pigeonote.types import Coordinate, get_coords_as_vector2

if TYPE_CHECKING:
    from pigeonote import Game

ComponentType = TypeVar("ComponentType", bound=Component)


class _EmptyClass(object):
    pass


class Entity:
    def __init__(self, name: str, position: Coordinate, game: "Game") -> None:
        self._name = name

        self._position = get_coords_as_vector2(position)
        self._rotation = 0

        self._components = list[Component]()
        self._components_destroyed = list[Component]()
        self._next_component_id = 0

        self._game = game
        self._is_destroyed = False

    @property
    def is_destroyed(self):
        return self._is_destroyed

    @property
    def game(self):
        return self._game

    @property
    def name(self):
        return self._name

    @property
    def position(self):
        return self._position

    @property
    def pixel_position(self):
        return int(self._position.x), int(self._position.y)

    @position.setter
    def position(self, new_topleft: Coordinate):
        self._position = get_coords_as_vector2(new_topleft)

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, new_rotation: float):
        # Note: this also works for negative rotation as expected.
        # e.g if rotation is -13 degrees, then it will become 347.
        self._rotation = new_rotation % 360

    def update(self):
        for component in self.get_components():
            component.component_update()

        for component in self._components_destroyed:
            self._components.remove(component)

        self._components_destroyed.clear()

    def create_component(self, component_type: type[ComponentType]) -> ComponentType:
        created_component_insance = component_type(component_id=self._next_component_id, parent=self)

        for var_name, annotation in component_type.__annotations__.items():
            if hasattr(component_type, var_name):
                var_value = getattr(component_type, var_name)

                if hasattr(var_value, "copy"):
                    instance_value = var_value.copy()
                else:
                    instance_value = var_value

                setattr(created_component_insance, var_name, instance_value)

            else:
                setattr(created_component_insance, var_name, annotation())

        self._next_component_id += 1

        self._components.append(created_component_insance)
        return created_component_insance

    def destroy_component(self, component: Component):
        self._components_destroyed.append(component)

    def get_components(self) -> Iterator[Component]:
        """
        Returns all the non-destroyed components of this entity.

        Note
        ----
        This doesn't returned components which were destroyed.

        Yields:
            Component: component of the entity.
        """
        for component in self._components:
            if component.is_destroyed:
                continue

            yield component

    def get_component_by_type(self, component_type: type[ComponentType]) -> ComponentType | None:
        for component in self.get_components():
            if isinstance(component, component_type):
                return component

    def get_all_components_of_type(self, component_type: type[ComponentType]) -> list[ComponentType]:
        return [c for c in self.get_components() if isinstance(c, component_type)]

    def get_component_by_id(self, component_id: int):
        component = [c for c in self.get_components() if c.component_id == component_id]
        if not component:
            raise KeyError(f"Component with ID `{component_id}` doesn't exist on `{self.name}`.")

        return component[0]

    def destroy(self):
        if self.is_destroyed:
            return

        # TODO: right here we should destroy children objects.

        # Perform destruction of attached components
        for component in self.get_components():
            component.destroy()

        # Clear possibly lingering references and set destroyed flag to True.
        self._components.clear()
        self._components_destroyed.clear()
        self._is_destroyed = True

        self._game.destroy(self)
