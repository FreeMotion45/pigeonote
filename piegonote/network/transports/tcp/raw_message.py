from dataclasses import dataclass


@dataclass
class RawMessage:
    client_id: int
    data: bytes
