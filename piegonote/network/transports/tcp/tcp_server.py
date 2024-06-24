import select
from queue import Queue
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP, TCP_NODELAY
from typing import Optional

from .client_handler import ClientHandler
from .raw_message import RawMessage


class Client:
    def __init__(self, client_id: int, handler: ClientHandler) -> None:
        self.client_id = client_id
        self.handler = handler


class TCPServer:
    def __init__(self, address: tuple[str, int] = ("localhost", 27800)) -> None:
        self._address = address

        self._server = socket(AF_INET, SOCK_STREAM)
        self._server.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        self._server.bind(address)
        self._server.listen()

        self._in_msg_queue = Queue[RawMessage]()
        self._out_msg_queue = Queue[bytes]()

        self._clients = dict[int, Client]()

        self._next_client_id = 1

    def remove_client(self, client_id: int):
        if not self._clients[client_id].handler._closed:
            self._clients[client_id].handler.close()

        self._clients.pop(client_id)

    def get_connected_client_ids(self):
        return list(self._clients.keys())

    def send_message(
        self, data: bytes, recipients: Optional[list[int] | tuple[int]] = None
    ):
        recipients = recipients or self.get_connected_client_ids()

        for recipient_id in recipients:
            self._clients[recipient_id].handler.send_message(data)

    def accept_connections(self):
        changed, _, _ = select.select([self._server], [], [], 0)
        new_clients = list[int]()

        if changed:
            client_socket, _ = self._server.accept()

            handler = ClientHandler(client_socket)
            client_id = self._next_client_id
            self._clients[client_id] = Client(client_id, handler)
            new_clients.append(client_id)

            self._next_client_id += 1

        return new_clients

    def receive_messages_from(self, client_id: int):
        client = self._clients[client_id]

        try:
            for message in client.handler.receive_messages():
                yield message

        except ConnectionError:
            self.remove_client(client_id)
            raise

        except ValueError:
            self.remove_client(client_id)
            raise ConnectionResetError()

    def close(self):
        self._server.close()
