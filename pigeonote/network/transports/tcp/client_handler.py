import select
import struct
from queue import Empty, Queue
from socket import socket
from threading import Thread

from .socket_stream_wrapper import SocketStreamWrapper


class ClientHandler:
    def __init__(self, client: socket) -> None:
        self._client = client
        self._client_io = SocketStreamWrapper(self._client)

        self._closed = False

        self._out_msg_queue = Queue[bytes]()

        self._socket_send_thread = Thread(target=self._write_message_loop)
        self._socket_send_thread.daemon = True
        self._socket_send_thread.start()

    def _read_message(self):
        msg_length_bytes = self._client_io.read(4)
        if not msg_length_bytes:
            return b""

        length = struct.unpack("<i", msg_length_bytes)[0]
        return self._client_io.read(length)

    def _write_message(self, data: bytes):
        msg_length_bytes = struct.pack("<i", len(data))
        self._client_io.write(msg_length_bytes + data)

    def _write_message_loop(self):
        while not self._closed:
            try:
                while data := self._out_msg_queue.get(timeout=0.1):
                    self._write_message(data)
            except Empty:
                pass

    def receive_messages(self):
        received_messages = list[bytes]()

        readable, _, _ = select.select([self._client], [], [], 0)
        while readable and (message := self._read_message()):
            received_messages.append(message)
            readable, _, _ = select.select([self._client], [], [], 0)

        return received_messages

    def send_message(self, data: bytes):
        self._out_msg_queue.put(data)

    def close(self):
        self._closed = True
        self._socket_send_thread.join()

        self._client.close()
