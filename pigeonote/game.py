import uuid
from typing import Literal, Optional, TypeVar, overload

import pygame as pg

from pigeonote import Camera2D, Entity, MouseButton, Service

from .types import Coordinate

ServiceType = TypeVar("ServiceType", bound=Service)


class Game:
    instance: Optional["Game"] = None

    @staticmethod
    def get_instance():
        if not Game.instance:
            raise RuntimeError("Can't access game instance before it was created.")

        return Game.instance

    def __init__(self, display: Optional[pg.Surface] = None, target_fps: int = 60) -> None:
        self._is_actual_display = False
        if not display:
            pg.init()
            display = pg.display.set_mode((16 * 100, 9 * 100))
            self._is_actual_display = True
            pg.display.set_caption("Your pigeonote game")

        self._running = False

        self._display = display

        camera_view_area = pg.Rect((0, 0), (16 * 25, 9 * 25))
        camera_view_area.center = (0, 0)
        self._camera2d = Camera2D(area=camera_view_area)

        self._entities = list[Entity]()
        self._services = list[Service]()

        self._clock = pg.Clock()
        self._target_fps = target_fps
        self._dt = 0.1

        self._keys_down = set[int]()
        self._keys_pressed = set[int]()
        self._keys_up = set[int]()

        self._mouse_btns_down = set[MouseButton]()
        self._mouse_btns_pressed = set[MouseButton]()
        self._mouse_btns_up = set[MouseButton]()

        assert self.instance is None
        Game.instance = self

    @property
    def camera(self):
        return self._camera2d

    @property
    def dt(self):
        return self._dt

    def is_key_down(self, key: int):
        return key in self._keys_down

    def is_key_up(self, key: int):
        return key in self._keys_up

    def is_key_pressed(self, key: int):
        return key in self._keys_pressed

    @property
    def mouse_screen_position(self):
        mouse_pos_x, mouse_pos_y = pg.mouse.get_pos()
        camera_width, camera_height = self._camera2d.area.size
        display_width, display_height = pg.display.get_surface().size
        scale_x, scale_y = (camera_width / display_width, camera_height / display_height)
        return pg.Vector2(mouse_pos_x * scale_x, mouse_pos_y * scale_y)

    @property
    def mouse_world_position(self):
        return self._camera2d.screen_position_to_world_position(self.mouse_screen_position)

    def is_mouse_btn_down(self, button: MouseButton):
        return button in self._mouse_btns_down

    def is_mouse_btn_up(self, button: MouseButton):
        return button in self._mouse_btns_up

    def is_mouse_btn_pressed(self, button: MouseButton):
        return button in self._mouse_btns_pressed

    @overload
    def find_entity_by_name(self, name: str, raise_if_not_found: Literal[False]) -> Optional[Entity]: ...
    @overload
    def find_entity_by_name(self, name: str, raise_if_not_found: Literal[True]) -> Entity: ...

    # Note: the return typehint in the overload below depends on the default value of `raise_if_not_found`.
    @overload
    def find_entity_by_name(self, name: str) -> Entity: ...
    def find_entity_by_name(self, name: str, raise_if_not_found: bool = True) -> Optional[Entity]:
        candidates = [e for e in self._entities if e.name == name]
        if candidates:
            return candidates[0]

        if raise_if_not_found:
            raise LookupError(f"Couldn't find entity with name: `{name}`.")

    def find_service_by_name(self, name: str) -> Optional[Service]:
        candidates = [s for s in self._services if s.name == name]
        if candidates:
            return candidates[0]

    def find_service_by_type(self, service_type: type[ServiceType]) -> ServiceType:
        candidates = [s for s in self._services if isinstance(s, service_type)]
        if candidates:
            return candidates[0]

        raise LookupError(f"Couldnt find service of type {service_type.__name__}.")

    def create_entity(self, position: Coordinate = (0, 0), name: Optional[str] = None):
        if name is None:
            name = f"entity_{str(uuid.uuid4())}"

        if self.find_entity_by_name(name, raise_if_not_found=False):
            raise KeyError(f"Can't create entity with name: `{name}`, because an entity with this name already exists.")

        new_entity = Entity(name=name, position=position, game=self)
        self._entities.append(new_entity)
        return new_entity

    def create_service(self, service_type: type[ServiceType], name: Optional[str] = None) -> ServiceType:
        if name is None:
            name = f"service_{service_type.__name__}_{str(uuid.uuid4())}"

        if self.find_service_by_name(name):
            raise KeyError(
                f"Can't create service with name: `{name}`, because a service with this name already exists."
            )

        new_service = service_type(name=name, game=self)
        self._services.append(new_service)
        return new_service

    def blit(self, surface: pg.Surface, topleft: Coordinate):
        return self.camera.blit(surface, topleft)

    def fill(self, color: str | int, area: pg.Rect):
        return self.camera.fill(color, area)

    def run(self):
        self.initialize()
        self.game_loop()

        pg.quit()

    def game_loop(self):
        self._running = True
        while self._running:
            self.process()

            if self._is_actual_display:
                pg.display.flip()

    def process(self):
        self._display.fill("black")

        self.camera.clean_surface()

        self._keys_down.clear()
        self._keys_up.clear()

        self._mouse_btns_down.clear()
        self._mouse_btns_up.clear()

        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    self._running = False
                    return False

                case pg.KEYDOWN:
                    self._keys_down.add(event.key)
                    self._keys_pressed.add(event.key)

                case pg.KEYUP:
                    self._keys_up.add(event.key)
                    self._keys_pressed.remove(event.key)

                case pg.MOUSEBUTTONDOWN:
                    mouse_button = MouseButton(event.button)
                    self._mouse_btns_down.add(mouse_button)
                    self._mouse_btns_pressed.add(mouse_button)

                case pg.MOUSEBUTTONUP:
                    mouse_button = MouseButton(event.button)
                    self._mouse_btns_up.add(mouse_button)
                    self._mouse_btns_pressed.remove(mouse_button)

        self.update()
        self._camera2d.render_frame()

        current_frame_surface = self._camera2d.get_rendered_surface()
        pg.transform.scale(current_frame_surface, self._display.get_size(), dest_surface=self._display)

        self._dt = self._clock.tick(self._target_fps) / 1000
        return True

    def initialize(self):
        for service in self._services:
            service.initialize()

        print(f"pygame driver: {pg.display.get_driver()}.")

    def update(self):
        """
        Steps through the life cycle of entities/components.

        1. Update every component of each entity. This is usually where any logic is being processed.
        2. Update every service.
        3. After all the game logic was updated in component/service.update(), we call another `render`
           method in which components can actually draw/render anything onto the screen.
        """
        for entity in self._entities:
            for component in entity.get_components():
                component.component_update()

        for service in self._services:
            service.service_update()

        for entity in self._entities:
            for component in entity.get_components():
                component.render()

    def destroy(self, entity: Entity):
        entity.destroy()

        # TODO: fix entity/component destroy procedure.
        if entity in self._entities:
            self._entities.remove(entity)
