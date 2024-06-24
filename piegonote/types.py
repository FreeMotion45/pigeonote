from pygame import Vector2

Coordinate = tuple[int, int] | Vector2


def get_coords_as_vector2(coord: Coordinate):
    if isinstance(coord, (tuple, list)):
        return Vector2(coord)

    assert isinstance(coord, Vector2)
    return coord


def get_coords_as_tuple(coord: Coordinate) -> tuple[float, float] | tuple[int, int]:
    if isinstance(coord, Vector2):
        return (coord.x, coord.y)

    elif isinstance(coord, list):
        return (coord[0], coord[1])

    assert isinstance(coord, tuple)
    return coord
