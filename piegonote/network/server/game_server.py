import json
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Callable, Optional

from piegonote import Entity, Service
from piegonote.network import (
    DatagramFormatter,
    DatagramType,
    NetworkedComponent,
    Datagram,
    TCPServer,
)
from piegonote.network.messages.datagram_type import *
from piegonote.types import Coordinate, get_coords_as_vector2

ConnectionID = int


@dataclass
class OutgoingDatagram:
    datagram: Datagram
    recipients: Optional[list[ConnectionID]]


@dataclass
class NetworkedEntity:
    prefab: str  # The prefab factory used to create the entity.
    net_entity_id: ConnectionID
    entity: Entity


class GameServer(Service):
    EXECUTING_RPC = False

    def __init__(self, name, game) -> None:
        super().__init__(name, game)

        self.host_ip = "localhost"
        self.port = 27800
        self.formatter = DatagramFormatter()
        self.prefab_factories = dict[str, Callable[[], Entity]]()

        self._server: TCPServer = None
        self._outgoing_datagrams = list[OutgoingDatagram]()

        self._unacked_clients = list[ConnectionID]()
        self._connected_clients = list[int]()

        self._event_handlers = dict[str, list[Callable[..., Any]]]()

        self._networked_entities = dict[int, NetworkedEntity]()
        self._next_networked_entity_id = 0

    def fire(self, event: str, *args: Any):
        if event not in self._event_handlers:
            return

        for handler in self._event_handlers[event]:
            handler(*args)

    def on(self, event: str, callback: Callable[..., Any]):
        if event not in self._event_handlers:
            self._event_handlers[event] = []

        self._event_handlers[event].append(callback)

    def _send_datagram(self, datagram: Datagram, recipients: Optional[list[int]] = None):
        if recipients is not None and len(recipients) == 0:
            return

        self._outgoing_datagrams.append(OutgoingDatagram(datagram=datagram, recipients=recipients))

    def _generate_networked_entity_id(self):
        new = self._next_networked_entity_id
        self._next_networked_entity_id += 1
        return new

    def _remove_client(self, client_id: int):
        if client_id in self._connected_clients:
            self._connected_clients.remove(client_id)

        if client_id in self._unacked_clients:
            self._unacked_clients.remove(client_id)

    def connect(self):
        self._server = TCPServer((self.host_ip, self.port))
        print(f"[SERVER] hosting server on address {self.host_ip}:{self.port}")

    def update(self):
        if not self._server:
            return

        new_clients = self._server.accept_connections()
        for new_client_id in new_clients:
            self._server.send_message(
                self.formatter.serialize(ClientIDExchangeDatagram(client_id=new_client_id)),
                recipients=[new_client_id],
            )
            self._unacked_clients.append(new_client_id)

        for client_id in self._connected_clients + self._unacked_clients:
            try:
                for message in self._server.receive_messages_from(client_id):
                    self._handle_message(client_id, message)

            except ConnectionError:
                self._remove_client(client_id)
                print(f"[SERVER] Lost connection to {client_id}.")
                self.fire("disconnected", client_id)

        self._handle_outgoing_datagrams()

    def _handle_message(self, client_id: ConnectionID, message: bytes):
        for datagram in self.formatter.iter_deserialize(message):
            if client_id in self._connected_clients:
                self._handle_datagram(client_id, datagram)

            elif client_id in self._unacked_clients:
                if datagram.datagram_type != DatagramType.ClientIDExchangeAck:
                    # TODO: instead, don't raise exception. Disconnect client and resume to normal flow.
                    raise Exception("Client didn't respond with an appropriate ACK message.")

                print(f"[SERVER] New client connected: {client_id}.")
                self._connected_clients.append(client_id)
                self._unacked_clients.remove(client_id)
                self._sync_client(client_id)
                self.fire("connected", client_id)

    def _handle_datagram(self, client_id: ConnectionID, datagram: Datagram):
        match datagram.datagram_type:
            case DatagramType.ToServerExecuteRPC:
                assert isinstance(datagram, ToServerExecuteRPCDatagram)

                # If it doesn't exist on the server anymore, escape.
                # (this might happen, e.g if a datagram was received after an entity had been destroyed)
                if datagram.net_entity_id not in self._networked_entities:
                    return

                deserialized_json = json.loads(datagram.params.decode("ascii"))
                args, kwargs = deserialized_json["a"], deserialized_json["k"]

                net_entity = self._networked_entities[datagram.net_entity_id]
                net_component = net_entity.entity.get_component_by_id(datagram.component_id)

                rpc_method = getattr(net_component, datagram.method_name)
                GameServer.EXECUTING_RPC = True
                rpc_method(*args, **kwargs)
                GameServer.EXECUTING_RPC = False

                # If it's for everyone, send to everyone.
                if datagram.rpc_recipient == 1:
                    everyone_except_sender = [other for other in self._connected_clients if other != client_id]
                    forwaded_dgram = ToClientExecuteRPCDatagram(
                        net_entity_id=datagram.net_entity_id,
                        component_id=datagram.component_id,
                        method_name=datagram.method_name,
                        params=datagram.params,
                    )
                    self._send_datagram(forwaded_dgram, recipients=everyone_except_sender)

    def _handle_outgoing_datagrams(self):
        messages = dict[ConnectionID, BytesIO]()

        for outgoing_datagram in self._outgoing_datagrams:
            serialized_data = self.formatter.serialize(outgoing_datagram.datagram)

            recipients = outgoing_datagram.recipients
            if recipients is None:
                recipients = self._connected_clients

            for recipient in recipients:
                if recipient not in self._connected_clients:
                    continue

                if recipient not in messages:
                    messages[recipient] = BytesIO()

                messages[recipient].write(serialized_data)

            # print(
            #     f"[SERVER] will send datagram of type {outgoing_datagram.datagram.datagram_type} to {recipients}"
            # )

        for client_id, message in messages.items():
            message.seek(0)
            self._server.send_message(message.read(), [client_id])

        self._outgoing_datagrams.clear()

    def _sync_client(self, client_id: ConnectionID):
        for net_entity_id, net_entity_data in self._networked_entities.items():
            if net_entity_data.entity.get_component_by_type(NetworkedComponent).owner == client_id:
                continue

            # TODO: this is obviously wrong, since ownership is per component, and not object.
            # Get arbitrary owner of some network component.
            owner = net_entity_data.entity.get_component_by_type(NetworkedComponent).owner

            dgram = SpawnNetworkEntityDatagram(
                prefab_name=net_entity_data.prefab,
                owner=owner,
                network_entity_id=net_entity_id,
                position=net_entity_data.entity.position,
                rotation=int(net_entity_data.entity.rotation),
            )

            # self._send_datagram(
            #     dgram,
            #     recipients=[client_id],
            # )
            self._server.send_message(self.formatter.serialize(dgram), recipients=[client_id])

    def spawn_entity(
        self,
        prefab: str,
        owner: int = -1,
        position: Coordinate = (0, 0),
        rotation: int = 0,
    ):
        net_entity_id = self._generate_networked_entity_id()

        new_entity = self.prefab_factories[prefab]()
        new_entity.position = position
        new_entity.rotation = rotation

        for networked_component in new_entity.get_all_components_of_type(NetworkedComponent):
            networked_component.private_fw_set_entity_id(net_entity_id)
            networked_component.private_fw_set_owner(owner)

        self._networked_entities[net_entity_id] = NetworkedEntity(
            prefab=prefab, net_entity_id=net_entity_id, entity=new_entity
        )

        spawn_datagram = SpawnNetworkEntityDatagram(
            prefab_name=prefab,
            owner=owner,
            network_entity_id=net_entity_id,
            position=get_coords_as_vector2(position),
            rotation=rotation,
        )
        self._send_datagram(spawn_datagram)
        return new_entity

    def destroy_entity(self, entity: int | Entity):
        if isinstance(entity, Entity):
            net_entity_id = None

            for net_id, net_data in self._networked_entities.items():
                if net_data.entity == entity:
                    net_entity_id = net_id
                    break

            if net_entity_id is None:
                raise RuntimeError(f"{entity.name} isn't a network entity!")

        elif isinstance(entity, int):
            net_entity_id = entity

        else:
            raise TypeError("Entity can either be the ID of the entity, or an Entity.")

        net_entity = self._networked_entities[net_entity_id]

        self._networked_entities.pop(net_entity.net_entity_id)
        self.game.destroy(net_entity.entity)

        destroy_datagram = DestroyNetworkEntityDatagram(network_entity_id=net_entity_id)
        self._send_datagram(destroy_datagram)
