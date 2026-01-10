#!/usr/bin/env python3
"""
Test Monitor Client
"""

import grpc
import signal
import sys
from datetime import datetime

from generated.mcubus.v1 import mcu_bus_pb2_grpc
from generated.mcubus.v1 import messages_pb2
from generated.mcubus.v1 import events_pb2


class MonitorClient:
    """Monitor Daemon"""

    def __init__(self, server_address: str = "localhost:50051"):
        self.server_address = server_address
        self.channel = None
        self.stub = None
        self._running = True

    def connect(self):
        print(f"[Monitor] Connecting to {self.server_address}...")

        self.channel = grpc.insecure_channel(
            self.server_address,
            options=[
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
            ]
        )
        self.stub = mcu_bus_pb2_grpc.MCUBusServiceStub(self.channel)
        print("[Monitor] ✓ Connected")

    def register(self, module_id: str = "monitor_daemon", module_type: str = "monitor"):
        request = messages_pb2.RegisterRequest(
            module_id=module_id,
            module_type=module_type,
            metadata={"version": "1.0.0", "platform": "raspberry_pi"}
        )

        try:
            response = self.stub.Register(request)
            if response.success:
                print(f"[Monitor] ✓ Registered as '{response.assigned_id}'")
                return response.assigned_id
            else:
                print(f"[Monitor] ✗ Registration failed: {response.message}")
                return None
        except grpc.RpcError as e:
            print(f"[Monitor] ✗ RPC Error: {e.code()} - {e.details()}")
            return None

    def subscribe(self, module_ids: list = None, event_types: list = None):
        request = messages_pb2.SubscribeRequest(
            module_ids=module_ids or [],
            event_types=event_types or []
        )

        filter_desc = []
        if module_ids:
            filter_desc.append(f"modules={module_ids}")
        if event_types:
            filter_desc.append(f"types={event_types}")
        filter_str = ", ".join(filter_desc) if filter_desc else "ALL"

        print(f"[Monitor] Subscribing to events ({filter_str})...")
        print("-" * 60)

        try:
            event_stream = self.stub.SubscribeEvents(request)

            for event in event_stream:
                if not self._running:
                    break
                self._handle_event(event)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.CANCELLED:
                print("\n[Monitor] Subscription cancelled")
            else:
                print(f"\n[Monitor] ✗ RPC Error: {e.code()} - {e.details()}")

    def _handle_event(self, event: events_pb2.BusEvent):
        ts = datetime.fromtimestamp(event.timestamp.seconds).strftime("%H:%M:%S")
        payload_type = event.WhichOneof("payload")

        if payload_type == "sensor_data":
            self._handle_sensor(event, ts)
        elif payload_type == "control_status":
            self._handle_control(event, ts)
        elif payload_type == "alert":
            self._handle_alert(event, ts)
        else:
            print(f"[{ts}] Unknown event type: {payload_type}")

    def _handle_sensor(self, event: events_pb2.BusEvent, ts: str):
        d = event.sensor_data
        print(f"[{ts}] 📊 SENSOR | T:{d.temperature:5.1f}°C | H:{d.humidity:5.1f}% | "
              f"Soil:{d.soil_moisture:5.1f}% | Water:{d.water_level:5.1f}% | pH:{d.ph_value:.2f}")

    def _handle_control(self, event: events_pb2.BusEvent, ts: str):
        c = event.control_status
        status = "🟢 ON " if c.is_active else "🔴 OFF"
        print(f"[{ts}] 🎛  CONTROL | {c.device:15} | {status} | "
              f"Power:{c.power_level:5.1f}% | {c.reason}")

    def _handle_alert(self, event: events_pb2.BusEvent, ts: str):
        a = event.alert
        icons = {"info": "ℹ️ ", "warning": "⚠️ ", "critical": "🚨"}
        icon = icons.get(a.severity, "❓")
        print(f"[{ts}] {icon} ALERT  | [{a.severity.upper():8}] {a.code}: {a.message}")

    def shutdown(self):
        self._running = False
        if self.channel:
            self.channel.close()
        print("[Monitor] Disconnected")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor Client for MCU Bus")
    parser.add_argument("-s", "--server", default="localhost:50051", help="Server address")
    parser.add_argument("-m", "--modules", nargs="*", help="Filter by module IDs")
    parser.add_argument("-t", "--types", nargs="*",
                        choices=["sensor_data", "control_status", "alert"],
                        help="Filter by event types")
    args = parser.parse_args()

    client = MonitorClient(args.server)

    # deal with Ctrl+C
    def signal_handler(sig, frame):
        print("\n[Monitor] Shutting down...")
        client.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        client.connect()
        client.register()
        client.subscribe(module_ids=args.modules, event_types=args.types)
    except Exception as e:
        print(f"[Monitor] Error: {e}")
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()
