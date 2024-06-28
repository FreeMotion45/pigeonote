import json
from typing import TYPE_CHECKING, Callable

from pygame import Vector2

from pigeonote.network.messages.datagram_type import (
    ToServerExecuteRPCDatagram,
    ToClientExecuteRPCDatagram,
)
from pigeonote.network.rpc.rpc_recipient import RPCRecipient

if TYPE_CHECKING:
    from pigeonote.network import NetworkedComponent


def _serialize_method_params(func: Callable, args, kwargs):
    for i in range(len(args)):
        if isinstance(args[i], Vector2):
            args[i] = tuple(args[i])

    return json.dumps({"a": args, "k": kwargs}, separators=(",", ":")).encode("ascii")


def _deserialize_method_params(func: Callable, params: bytes):
    deserialized_json = json.loads(params.decode("ascii"))
    return deserialized_json["a"], deserialized_json["k"]


def rpc(recipient: RPCRecipient = RPCRecipient.Everyone):
    from pigeonote.network import GameServer, GameClient

    def decorator(func):
        def wrapper(self: "NetworkedComponent", *args, **kwargs):

            ret = func(self, *args, **kwargs)

            # In case this function was called due to an RPC request, then don't proceed further.
            if GameClient.EXECUTING_RPC or GameServer.EXECUTING_RPC:
                return ret

            if self._client:
                datagram = ToServerExecuteRPCDatagram(
                    rpc_recipient=recipient.value,
                    net_entity_id=self.net_entity_id,
                    component_id=self.component_id,
                    method_name=func.__name__,
                    params=_serialize_method_params(func, list(args), kwargs),
                )
                self._client._send_datagram(datagram)
            elif self._server:
                datagram = ToClientExecuteRPCDatagram(
                    net_entity_id=self.net_entity_id,
                    component_id=self.component_id,
                    method_name=func.__name__,
                    params=_serialize_method_params(func, list(args), kwargs),
                )
                self._server._send_datagram(datagram)

            return ret

        return wrapper

    deco = decorator
    return deco
