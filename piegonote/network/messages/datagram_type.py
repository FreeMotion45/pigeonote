from enum import IntEnum
from pygame import Vector2


class DatagramType(IntEnum):
    ClientIDExchange = 1
    """
    Message type for exchanging client ID between.
    """

    ClientIDExchangeAck = 2
    """
    Client sends back to server that he successfully received his ID.
    """

    SpawnNetworkEntity = 100
    """
    Create a networked entity.
    """

    DestroyNetworkEntity = 101
    """
    Destroy a networked entity.
    """

    ToServerExecuteRPC = 200
    """
    Message sent to server to issue execution of a networked entity's method on local instances.
    """

    ToClientExecuteRPC = 201
    """
    Message sent from the server to the client which issues the execution of a networked entity's method on the local client.
    """

    TransferOwnership = 300
    """
    Message sent from the server to the clients which informs about an objects new owner.
    """


class Datagram:
    def __init__(self, datagram_type: DatagramType) -> None:
        self.datagram_type = datagram_type


class ClientIDExchangeDatagram(Datagram):
    def __init__(self, client_id: int) -> None:
        super().__init__(DatagramType.ClientIDExchange)
        self.client_id = client_id


class ClientIDExchangeAckDatagram(Datagram):
    def __init__(self) -> None:
        super().__init__(DatagramType.ClientIDExchangeAck)


class SpawnNetworkEntityDatagram(Datagram):
    def __init__(
        self,
        prefab_name: str,
        owner: int,
        network_entity_id: int,
        position: Vector2,
        rotation: int,
    ) -> None:
        super().__init__(DatagramType.SpawnNetworkEntity)

        self.prefab_name = prefab_name
        self.owner = owner
        self.network_entity_id = network_entity_id
        self.position = position
        self.rotation = rotation


class DestroyNetworkEntityDatagram(Datagram):
    def __init__(self, network_entity_id: int) -> None:
        super().__init__(DatagramType.DestroyNetworkEntity)
        self.net_entity_id = network_entity_id


class ToServerExecuteRPCDatagram(Datagram):
    def __init__(
        self,
        rpc_recipient: int,
        net_entity_id: int,
        component_id: int,
        method_name: str,
        params: bytes,
    ) -> None:
        super().__init__(DatagramType.ToServerExecuteRPC)

        self.rpc_recipient = rpc_recipient
        self.net_entity_id = net_entity_id
        self.component_id = component_id
        self.method_name = method_name
        self.params = params


class ToClientExecuteRPCDatagram(Datagram):
    def __init__(
        self, net_entity_id: int, component_id: int, method_name: str, params: bytes
    ) -> None:
        super().__init__(DatagramType.ToClientExecuteRPC)
        self.net_entity_id = net_entity_id
        self.component_id = component_id
        self.method_name = method_name
        self.params = params
