from queue import Empty, Queue
import select
from socket import create_connection
import struct
from threading import Thread
from typing import Optional

from piegonote.network.transports.tcp.socket_stream_wrapper import SocketStreamWrapper


class TCPClient:
    def __init__(self, server_address: tuple[str, int] = ("localhost", 27800)) -> None:
        self._server_address = server_address
        self._sock = create_connection(self._server_address)
        self._sock_io = SocketStreamWrapper(self._sock)

        self._out_msg_queue = Queue[bytes]()

        self._closed = False
        self._can_receive_data = True
        self._errored = False

        self._sending_thread = Thread(target=self._send_message_loop)
        self._sending_thread.daemon = True
        self._sending_thread.start()
        
    @property
    def closed(self):
        return self._closed

    def _send_message_loop(self):
        while not self._closed:
            try:
                data = self._out_msg_queue.get(timeout=0.1)
                self._sock_io.write(data)
            except Empty:
                pass

    def receive_messages(self, max_messages: Optional[int] = None):
        received_messages = list[bytes]()

        if self._can_receive_data:
            data_available, _, _ = select.select([self._sock], [], [], 0)
            while data_available:
                try:
                    msg_length_bytes = self._sock_io.read(4)
                    length = struct.unpack("<i", msg_length_bytes)[0]
                    received_messages.append(self._sock_io.read(length))
                except ConnectionResetError:
                    self._can_receive_data = False
                    raise

                if max_messages is not None and len(received_messages) >= max_messages:
                    break

                data_available, _, _ = select.select([self._sock], [], [], 0)

        return received_messages

    def send_message(self, data: bytes):
        if self._closed:
            raise RuntimeError(f"The client has been closed.")

        msg_length_bytes = struct.pack("<i", len(data))
        self._out_msg_queue.put(msg_length_bytes + data)

    def close(self):
        self._closed = True
        self._can_receive_data = False
        self._sending_thread.join()
        self._sock.close()
