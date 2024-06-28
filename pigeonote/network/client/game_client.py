import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from pigeonote import Entity, Service
from pigeonote.network import (
    DatagramFormatter,
    DatagramType,
    NetworkedComponent,
    Datagram,
    TCPClient,
)
from pigeonote.network.messages.datagram_type import *

ConnectionID = int


@dataclass
class NetworkedEntity:
    net_entity_id: ConnectionID
    entity: Entity


class GameClient(Service):
    EXECUTING_RPC = False

    def __init__(self, name, game) -> None:
        super().__init__(name, game)

        self.server_ip = "localhost"
        self.server_port = 27800
        self.formatter = DatagramFormatter()
        self.prefab_factories = dict[str, Callable[[], Entity]]()

        self._client: TCPClient = None
        self._client_id: Optional[ConnectionID] = None
        self._time_connected: datetime = datetime.now()
        self._outgoing_datagrams = list[Datagram]()

        self._networked_entities = dict[ConnectionID, NetworkedEntity]()

        self._custom_handlers = dict[str, list[Callable[..., Any]]]()

    def fire(self, event: str, *args: Any):
        if event not in self._custom_handlers:
            return

        for handler in self._custom_handlers[event]:
            handler(*args)

    def on(self, event: str, callback: Callable[..., Any]):
        if event not in self._custom_handlers:
            self._custom_handlers[event] = []

        self._custom_handlers[event].append(callback)

    def _send_datagram(self, datagram: Datagram):
        self._outgoing_datagrams.append(datagram)

    @property
    def client_id(self):
        if self._client_id is None:
            raise Exception("No client id available (not connected).")

        return self._client_id

    def reset(self):
        if self._client and not self._client.closed:
            self._client.close()

        self._client_id = None

    # def initialize(self):
    #     self._client = TCPClient((self.server_address, self.server_port))
    #     self._time_connected: datetime = datetime.now()
    #     print(
    #         f"[CLIENT] Establishing connection to {self.server_address}:{self.server_port}"
    #     )

    def connect(self):
        self._client = TCPClient((self.server_ip, self.server_port))
        self._time_connected: datetime = datetime.now()
        print(f"[CLIENT] Establishing connection to {self.server_ip}:{self.server_port}")

    def update(self):
        if not self._client:
            return

        try:
            for msg in self._client.receive_messages():
                self._handle_message(msg)

        except ConnectionError:
            self.reset()
            print(f"[CLIENT] Lost connection to {self.server_ip}:{self.server_port}")
            self.fire("disconnected")

        self._handle_outgoing_datagrams()

    def _handle_message(self, msg: bytes):
        assert self._client is not None

        for datagram in self.formatter.iter_deserialize(msg):
            if not self._client_id and datagram.datagram_type != DatagramType.ClientIDExchange:
                raise Exception(
                    f"[CLIENT] error, server sent invalid first message. Expected to receive message type, but received: {datagram.datagram_type}."
                )

            self._handle_datagram(datagram)

    def _handle_outgoing_datagrams(self):
        try:
            message = bytearray()
            for outgoing_datagram in self._outgoing_datagrams:
                self.formatter.serialize_into(outgoing_datagram, message)

            if len(message) > 0:
                self._client.send_message(bytes(message))

        except ConnectionError:
            self.reset()
            print(f"[CLIENT] Lost connection to {self.server_ip}:{self.server_port}")
            self.fire("disconnected")

        self._outgoing_datagrams.clear()

    def _handle_datagram(self, datagram: Datagram):
        assert self._client is not None
        # print("got dgram")

        match datagram.datagram_type:
            case DatagramType.ClientIDExchange:
                assert isinstance(datagram, ClientIDExchangeDatagram)

                self._client_id = datagram.client_id
                time_took = datetime.now() - self._time_connected
                print(
                    f"[CLIENT] Established connection, received ID: {self._client_id} (took: {time_took.total_seconds():.2f}s)."
                )
                self._send_datagram(ClientIDExchangeAckDatagram())
                self.fire("connected")

            case DatagramType.SpawnNetworkEntity:
                assert isinstance(datagram, SpawnNetworkEntityDatagram)

                new_entity = self.prefab_factories[datagram.prefab_name]()
                new_entity.position = datagram.position
                new_entity.rotation = datagram.rotation

                for networked_component in new_entity.get_all_components_of_type(NetworkedComponent):
                    networked_component.private_fw_set_entity_id(datagram.network_entity_id)
                    networked_component.private_fw_set_owner(datagram.owner)

                self._networked_entities[datagram.network_entity_id] = NetworkedEntity(
                    net_entity_id=datagram.network_entity_id,
                    entity=new_entity,
                )

            case DatagramType.DestroyNetworkEntity:
                assert isinstance(datagram, DestroyNetworkEntityDatagram)

                net_entity = self._networked_entities[datagram.net_entity_id]
                self.game.destroy(net_entity.entity)
                self._networked_entities.pop(net_entity.net_entity_id)

            case DatagramType.ToClientExecuteRPC:
                assert isinstance(datagram, ToClientExecuteRPCDatagram)

                deserialized_json = json.loads(datagram.params.decode("ascii"))
                args, kwargs = deserialized_json["a"], deserialized_json["k"]

                net_entity = self._networked_entities[datagram.net_entity_id]
                net_component = net_entity.entity.get_component_by_id(datagram.component_id)

                rpc_method = getattr(net_component, datagram.method_name)
                GameClient.EXECUTING_RPC = True
                rpc_method(*args, **kwargs)
                GameClient.EXECUTING_RPC = False
