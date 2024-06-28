from pigeonote import Component, Entity


class NetworkedComponent(Component):
    def __init__(self, component_id: int, parent: Entity) -> None:
        super().__init__(component_id, parent)

        from pigeonote.network import GameClient, GameServer

        try:
            self._client = self.game.find_service_by_type(GameClient)
        except:
            self._client = None

        try:
            self._server = self.game.find_service_by_type(GameServer)
        except:
            self._server = None

        self._owner = -1
        self._net_entity_id = -1

    def private_fw_set_owner(self, owner: int):
        self._owner = owner

    def private_fw_set_entity_id(self, net_entity_id: int):
        self._net_entity_id = net_entity_id

    @property
    def owner(self):
        return self._owner

    @property
    def is_owner(self):
        if self._client:
            return self.owner == self._client.client_id

        return self.owner == 0

    @property
    def net_entity_id(self):
        assert self._net_entity_id != -1
        return self._net_entity_id
