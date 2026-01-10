import grpc

from concurrent import futures


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server running on :50051")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down gRPC server...")
        server.stop(grace=2)


if __name__ == "__main__":
    serve()
