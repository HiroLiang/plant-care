import logging
import sys

import grpc

from concurrent import futures
from pathlib import Path

GENERATED_ROOT = Path(__file__).resolve().parents[2] / "plant-core" / "src" / "generated"
generated_root_str = str(GENERATED_ROOT)
if generated_root_str not in sys.path:
    sys.path.insert(0, generated_root_str)

from infrastructure.bus.can_daemon import CanBusDaemon
from infrastructure.bus.rpc_subscription_handler import RpcSubscriptionHandler
from infrastructure.shared.logger import setup_logging

from infrastructure.servicer.mcu_bus_servicer import MCUBusServer
from mcubus.v1 import mcu_bus_pb2_grpc


def main(
        port: int = 50051,
        channel: str = "can0",
        bitrate: int = 500000,
):
    setup_logging(json_output=False)
    logger = logging.getLogger(__name__)

    # Build servicer
    handler = RpcSubscriptionHandler()
    servicer = MCUBusServer(handler)
    can_daemon = CanBusDaemon(handler, channel=channel, bitrate=bitrate)

    # Build gRPC service
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ("grpc.max_send_message_length", 10 * 1024 * 1024),
            ("grpc.max_receive_message_length", 10 * 1024 * 1024),
        ]
    )
    mcu_bus_pb2_grpc.add_MCUBusServiceServicer_to_server(servicer, server)
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
