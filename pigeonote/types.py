from pygame import Vector2, Rect, FRect, Color as PyGameColor

Coordinate = tuple[int | float, int | float] | Vector2
Color = int | str | tuple[int, int, int] | tuple[int, int, int, int] | PyGameColor
AnyRect = Rect | FRect


def get_coords_as_vector2(coord: Coordinate):
    if isinstance(coord, (tuple, list)):
        return Vector2(coord)

    assert isinstance(coord, Vector2)
    return coord.copy()


def get_coords_as_tuple(coord: Coordinate) -> tuple[int | float, int | float]:
    if isinstance(coord, Vector2):
        return (coord.x, coord.y)

    elif isinstance(coord, list):
        return (coord[0], coord[1])

    assert isinstance(coord, tuple)
    return coord
