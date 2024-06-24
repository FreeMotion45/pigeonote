import uuid
from typing import Optional, TypeVar

import pygame as pg

from piegonote import Camera2D, Entity, MouseButton, Service

from .types import Coordinate

ServiceType = TypeVar("ServiceType", bound=Service)


class Game:
    instance: Optional["Game"] = None

    @staticmethod
    def get_instance():
        if not Game.instance:
            raise RuntimeError("Can't access game instance before it was created.")

        return Game.instance

    def __init__(
        self, display: Optional[pg.Surface] = None, target_fps: int = 60
    ) -> None:
        if not display:
            pg.init()
            display = pg.display.set_mode((600, 600), flags=pg.RESIZABLE)
            pg.display.set_caption("Your my_fw game")

        self._running = False

        self._display = display

        self._camera2d = Camera2D(area=pg.Rect((0, 0), self._display.get_size()))
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
        return pg.Vector2(pg.mouse.get_pos())

    def is_mouse_btn_down(self, button: MouseButton):
        return button in self._mouse_btns_down

    def is_mouse_btn_up(self, button: MouseButton):
        return button in self._mouse_btns_up

    def is_mouse_btn_pressed(self, button: MouseButton):
        return button in self._mouse_btns_pressed

    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        candidates = [e for e in self._entities if e.name == name]
        if candidates:
            return candidates[0]

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

        if self.find_entity_by_name(name):
            raise KeyError(
                f"Can't create entity with name: `{name}`, because an entity with this name already exists."
            )

        new_entity = Entity(name=name, position=position, game=self)
        self._entities.append(new_entity)
        return new_entity

    def create_service(
        self, service_type: type[ServiceType], name: Optional[str] = None
    ) -> ServiceType:
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
                        return

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

            self._dt = self._clock.tick(self._target_fps) / 1000
            self.update()

            current_frame_surface = self._camera2d.get_rendered_surface()
            scaled_frame_surface = pg.transform.scale(
                current_frame_surface, self._display.get_size()
            )

            self._display.blit(scaled_frame_surface, (0, 0))

            pg.display.flip()

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
