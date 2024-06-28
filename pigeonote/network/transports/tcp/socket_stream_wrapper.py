from socket import socket


class SocketStreamWrapper:
    def __init__(self, sock: socket) -> None:
        self._sock = sock
        
    def read(self, count: int):
        data = b""
        while len(data) < count:
            data += self._sock.recv(count - len(data))

        return data
    
    def write(self, data: bytes):
        self._sock.sendall(data)