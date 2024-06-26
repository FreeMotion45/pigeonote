from typing import Optional
from pygame import Vector2, Surface, Rect

from .types import Coordinate, Color, get_coords_as_vector2, get_coords_as_tuple
from .input import *
from .core import *
from .camera import Camera2D
from .game import Game


def create_entity(position: Vector2 | tuple[float, float] = (0, 0), name: Optional[str] = None):
    return Game.get_instance().create_entity(position=position, name=name)
