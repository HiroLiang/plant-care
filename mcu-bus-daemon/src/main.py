import logging

import grpc

from concurrent import futures
from infrastructure.logger import setup_logging

from infrastructure.servicer.mcu_bus_servicer import MCUBusServer
from generated.mcubus.v1 import mcu_bus_pb2_grpc


def main(
        port: int = 50051,
):
    setup_logging(json_output=False)
    logger = logging.getLogger(__name__)

    # Build servicer
    servicer = MCUBusServer()

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
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("\n[Shutdown] Stopping server...")
        server.stop(grace=5)
        logger.info("[Shutdown] Server stopped.")


if __name__ == "__main__":
    import argparse

    # Build args
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=int, default=50051, help="gRPC server port")
    args = parser.parse_args()

    # Start
    main(port=args.port)
