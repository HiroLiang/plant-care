import grpc

from generated.mcubus.v1 import mcu_bus_pb2_grpc
from generated.mcubus.v1.messages_pb2 import SubscribeRequest


class MCUBusClient:
    def __init__(self, channel: grpc.aio.Channel):
        self._stub = mcu_bus_pb2_grpc.MCUBusServiceStub(channel)

    async def subscribe_events(self):
        async for event in self._stub.SubscribeEvents(
                SubscribeRequest()
        ):
            yield event
