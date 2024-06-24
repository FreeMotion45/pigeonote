from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from piegonote import Game


class Service:
    def __init__(self, name: str, game: "Game") -> None:
        self._name = name
        self._game = game
        self._is_init = False

    @property
    def name(self):
        return self._name

    @property
    def game(self):
        return self._game

    def initialize(self):
        pass
    
    def init(self):
        pass
    
    def service_update(self):
        if not self._is_init:
            self.init()
            self._is_init = True
            
        self.update()

    def update(self):
        pass
