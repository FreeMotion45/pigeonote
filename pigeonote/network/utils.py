from pigeonote.network import GameServer
from pigeonote import Vector2, Entity


def net_spawn(
    prefab: str,
    owner: int = -1,
    position: Vector2 | tuple[int, int] = (0, 0),
    rotation: int = 0,
):

    from pigeonote import Game

    try:
        server = Game.get_instance().find_service_by_type(GameServer)
    except LookupError:
        raise RuntimeError("Only a server may spawn network entities.")

    server.spawn_entity(
        prefab=prefab, owner=owner, position=position, rotation=rotation
    )


def net_destroy(entity: int | Entity):
    from pigeonote import Game

    try:
        server = Game.get_instance().find_service_by_type(GameServer)
    except LookupError:
        raise RuntimeError("Only a server may destroy network entities.")

    server.destroy_entity(entity=entity)
