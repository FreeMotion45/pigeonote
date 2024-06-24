from io import BytesIO
import struct
from typing import BinaryIO, Iterator
from piegonote.network.messages.datagram_type import *

DEFAULT_ENDIANITY = "<"
INT8 = "b"
UINT8 = "B"
INT32 = "i"
UINT32 = "I"
INT16 = "h"
UINT16 = "H"
BOOL = "B"
DOUBLE = "d"


def _format_for(*value_types: str) -> str:
    return DEFAULT_ENDIANITY + "".join(value_types)


class DatagramFormatter:
    def __init__(self) -> None:
        self._out_buffer = BytesIO()
        self._in_buffer = BytesIO()

    def serialize_into(
        self,
        datagram: Datagram,
        buffer: bytearray | BinaryIO,
    ):
        serialized_data = self.serialize(datagram)

        if isinstance(buffer, bytearray):
            buffer.extend(serialized_data)
        elif isinstance(buffer, BytesIO):
            buffer.write(serialized_data)
        else:
            raise Exception("Bruh")

    def serialize(self, datagram: Datagram):
        self._out_buffer = BytesIO()

        self._write_int16(datagram.datagram_type.value)
        self._serialize_inner(datagram)

        self._out_buffer.seek(0)
        return self._out_buffer.read()

    def _serialize_inner(self, datagram: Datagram):
        match datagram.datagram_type:
            case DatagramType.ClientIDExchange:
                assert isinstance(datagram, ClientIDExchangeDatagram)
                self._write_client_id(datagram.client_id)

            case DatagramType.ClientIDExchangeAck:
                pass

            case DatagramType.SpawnNetworkEntity:
                assert isinstance(datagram, SpawnNetworkEntityDatagram)
                self._write_string(datagram.prefab_name)
                self._write_owner(datagram.owner)
                self._write_net_entity_id(datagram.network_entity_id)
                self._write_vec2(datagram.position)
                self._write_int16(datagram.rotation)

            case DatagramType.DestroyNetworkEntity:
                assert isinstance(datagram, DestroyNetworkEntityDatagram)
                self._write_net_entity_id(datagram.net_entity_id)

            case DatagramType.ToServerExecuteRPC:
                assert isinstance(datagram, ToServerExecuteRPCDatagram)
                self._write_uint8(datagram.rpc_recipient)
                self._write_net_entity_id(datagram.net_entity_id)
                self._write_uint8(datagram.component_id)
                self._write_string(datagram.method_name, encoding="ascii")
                self._write_bytes(datagram.params)

            case DatagramType.ToClientExecuteRPC:
                assert isinstance(datagram, ToClientExecuteRPCDatagram)
                self._write_net_entity_id(datagram.net_entity_id)
                self._write_uint8(datagram.component_id)
                self._write_string(datagram.method_name)
                self._write_bytes(datagram.params)

            case _:
                raise NotImplementedError(
                    f"Serialization not implemented for message type: {datagram.datagram_type}."
                )

    def iter_deserialize(self, data: bytes) -> Iterator[Datagram]:
        self._in_buffer = BytesIO(data)

        while self._in_buffer.tell() < len(data):
            yield self._deserialize_next()

    def _deserialize_next(self):
        datagram_type = DatagramType(self._read_int16())
        return self._deserialize_inner(datagram_type)

    def _deserialize_inner(self, datagram_type: DatagramType):
        match datagram_type:
            case DatagramType.ClientIDExchange:
                return ClientIDExchangeDatagram(client_id=self._read_client_id())

            case DatagramType.ClientIDExchangeAck:
                return ClientIDExchangeAckDatagram()

            case DatagramType.SpawnNetworkEntity:
                return SpawnNetworkEntityDatagram(
                    prefab_name=self._read_string(),
                    owner=self._read_owner(),
                    network_entity_id=self._read_net_entity_id(),
                    position=self._read_vec2(),
                    rotation=self._read_int16(),
                )

            case DatagramType.DestroyNetworkEntity:
                return DestroyNetworkEntityDatagram(
                    network_entity_id=self._read_net_entity_id()
                )

            case DatagramType.ToServerExecuteRPC:
                return ToServerExecuteRPCDatagram(
                    rpc_recipient=self._read_uint8(),
                    net_entity_id=self._read_net_entity_id(),
                    component_id=self._read_uint8(),
                    method_name=self._read_string(encoding="ascii"),
                    params=self._read_bytes(),
                )

            case DatagramType.ToClientExecuteRPC:
                return ToClientExecuteRPCDatagram(
                    net_entity_id=self._read_net_entity_id(),
                    component_id=self._read_uint8(),
                    method_name=self._read_string(),
                    params=self._read_bytes(),
                )

            case _:
                raise NotImplementedError(
                    f"Serialization not implemented for message type: {datagram_type}."
                )

    def _write_uint8(self, value: int):
        self._out_buffer.write(struct.pack(_format_for(UINT8), value))

    def _read_uint8(self):
        return struct.unpack(_format_for(UINT8), self._in_buffer.read(1))[0]

    def _write_int16(self, value: int):
        self._out_buffer.write(struct.pack(_format_for(INT16), value))

    def _read_int16(self) -> int:
        return struct.unpack(_format_for(INT16), self._in_buffer.read(2))[0]

    _write_client_id = _write_int16
    _read_client_id = _read_int16
    _write_owner = _write_int16
    _read_owner = _read_int16

    def _write_int32(self, value: int):
        self._out_buffer.write(struct.pack(_format_for(INT32), value))

    def _read_int32(self) -> int:
        return struct.unpack(_format_for(INT32), self._in_buffer.read(4))[0]

    _write_net_entity_id = _write_int32
    _read_net_entity_id = _read_int32

    def _write_float(self, value: float):
        self._out_buffer.write(struct.pack(_format_for(DOUBLE), value))

    def _read_float(self) -> float:
        return struct.unpack(_format_for(DOUBLE), self._in_buffer.read(4))[0]

    def _write_string(self, value: str, encoding: str = "utf-8"):
        encoded_string = value.encode(encoding=encoding)
        self._write_int16(len(encoded_string))
        self._out_buffer.write(encoded_string)

    def _read_string(self, encoding: str = "utf-8") -> str:
        encoded_string_length = self._read_int16()
        return self._in_buffer.read(encoded_string_length).decode(encoding=encoding)

    def _write_bytes(self, value: bytes):
        self._write_int16(len(value))
        self._out_buffer.write(value)

    def _read_bytes(self):
        length = self._read_int16()
        return self._in_buffer.read(length)

    def _write_vec2(self, value: Vector2):
        self._out_buffer.write(
            struct.pack(_format_for(DOUBLE, DOUBLE), value.x, value.y)
        )

    def _read_vec2(self) -> Vector2:
        return Vector2(
            struct.unpack(_format_for(DOUBLE, DOUBLE), self._in_buffer.read(16))
        )
