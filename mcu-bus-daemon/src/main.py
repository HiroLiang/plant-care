import logging

import grpc

from concurrent import futures

from infrastructure.bus.can_daemon import CanBusDaemon
from infrastructure.bus.rpc_subscription_handler import RpcSubscriptionHandler
from infrastructure.shared.logger import setup_logging

from infrastructure.servicer.mcu_bus_servicer import MCUBusCommandServer, MCUBusEventServer
from plant_core.generated.mcubus.v1 import command_service_pb2_grpc, event_service_pb2_grpc


def main(
        port: int = 50051,
        channel: str = "can0",
        bitrate: int = 500000,
):
    setup_logging(json_output=False)
    logger = logging.getLogger(__name__)

    # Build servicer
    handler = RpcSubscriptionHandler()
    command_servicer = MCUBusCommandServer()
    event_servicer = MCUBusEventServer(handler)
    can_daemon = CanBusDaemon(handler, channel=channel, bitrate=bitrate)

    # Build gRPC service
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ]
    )
    command_service_pb2_grpc.add_MCUBusCommandServiceServicer_to_server(command_servicer, server)
    event_service_pb2_grpc.add_MCUBusEventServiceServicer_to_server(event_servicer, server)
    server.add_insecure_port(f"[::]:{port}")

    # Start gRPC server
    server.start()
    logger.info("[Started] gRPC server running on: %s", port)

    try:
        if not can_daemon.start():
            raise RuntimeError(f"Failed to start CAN daemon on {channel} @ {bitrate}")
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("[Shutdown] Ctrl-C received")
    finally:
        logger.info("[Shutdown] Stopping server...")
        can_daemon.stop()
        server.stop(grace=5)
        logger.info("[Shutdown] Server stopped.")


def build_arg_parser():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=50051, help="gRPC server port")
    parser.add_argument("--channel", type=str, default="can0", help="SocketCAN channel")
    parser.add_argument("--bitrate", type=int, default=500000, help="SocketCAN bitrate")
    return parser


def main_cli(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    main(port=args.port, channel=args.channel, bitrate=args.bitrate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main_cli())
