#!/usr/bin/env python3
"""
Mock MCU Bus Daemon
"""

import grpc
import time
import random
import threading
import queue
import uuid
from concurrent import futures
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from generated.mcubus.v1 import mcu_bus_pb2_grpc
from generated.mcubus.v1 import messages_pb2
from generated.mcubus.v1 import events_pb2
from google.protobuf.timestamp_pb2 import Timestamp


@dataclass
class MockSensorConfig:
    base_temperature: float = 25.0
    base_humidity: float = 65.0
    base_soil_moisture: float = 50.0
    base_light_level: float = 800.0
    base_water_level: float = 80.0
    base_ph: float = 6.5

    temp_variance: float = 3.0
    humidity_variance: float = 10.0
    soil_variance: float = 15.0
    light_variance: float = 200.0
    water_variance: float = 5.0
    ph_variance: float = 0.5


@dataclass
class Subscriber:
    queue: queue.Queue
    module_ids: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class MockMCUBusServicer(mcu_bus_pb2_grpc.MCUBusServiceServicer):

    def __init__(self, config: Optional[MockSensorConfig] = None):
        self.config = config or MockSensorConfig()
        self.registered_modules: Dict[str, dict] = {}
        self.subscribers: List[Subscriber] = []
        self.lock = threading.RLock()
        self._event_counter = 0

        # 模擬狀態
        self._cooling_active = False
        self._pump_active = False

    def Register(self, request, context):
        module_id = request.module_id or f"module_{uuid.uuid4().hex[:8]}"

        with self.lock:
            self.registered_modules[module_id] = {
                "type": request.module_type,
                "metadata": dict(request.metadata),
                "registered_at": datetime.now().isoformat(),
                "peer": context.peer()
            }

        print(f"[Register] ✓ Module '{module_id}' ({request.module_type}) from {context.peer()}")

        return messages_pb2.RegisterReply(
            success=True,
            assigned_id=module_id,
            message=f"Registered successfully at {datetime.now().isoformat()}"
        )

    def UnRegister(self, request, context):
        with self.lock:
            if request.module_id in self.registered_modules:
                del self.registered_modules[request.module_id]
                print(f"[UnRegister] ✓ Module '{request.module_id}' removed")
                return messages_pb2.UnSubscribeReplay(
                    success=True,
                    message="Unregistered successfully"
                )

        print(f"[UnRegister] ✗ Module '{request.module_id}' not found")
        return messages_pb2.UnSubscribeReplay(
            success=False,
            message="Module not found"
        )

    def SubscribeEvents(self, request, context):
        subscriber = Subscriber(
            queue=queue.Queue(),
            module_ids=list(request.module_ids),
            event_types=list(request.event_types)
        )

        with self.lock:
            self.subscribers.append(subscriber)

        filter_info = f"modules={request.module_ids or 'ALL'}, types={request.event_types or 'ALL'}"
        print(f"[Subscribe] ✓ New subscriber from {context.peer()} ({filter_info})")
        print(f"[Subscribe]   Active subscribers: {len(self.subscribers)}")

        try:
            while context.is_active():
                try:
                    event = subscriber.queue.get(timeout=0.5)
                    yield event
                except queue.Empty:
                    continue
        except Exception as e:
            print(f"[Subscribe] ✗ Error: {e}")
        finally:
            with self.lock:
                if subscriber in self.subscribers:
                    self.subscribers.remove(subscriber)
            print(f"[Subscribe] ✗ Subscriber disconnected. Remaining: {len(self.subscribers)}")

    def _generate_event_id(self) -> str:
        self._event_counter += 1
        return f"evt_{int(time.time())}_{self._event_counter:06d}"

    def _create_timestamp(self) -> Timestamp:
        ts = Timestamp()
        ts.GetCurrentTime()
        return ts

    def generate_sensor_event(self, module_id: str = "mcu_main") -> events_pb2.BusEvent:
        cfg = self.config

        # 加入一些隨機波動，模擬真實感測器
        sensor_data = events_pb2.SensorData(
            temperature=cfg.base_temperature + random.uniform(-cfg.temp_variance, cfg.temp_variance),
            humidity=cfg.base_humidity + random.uniform(-cfg.humidity_variance, cfg.humidity_variance),
            soil_moisture=max(0,
                              min(100, cfg.base_soil_moisture + random.uniform(-cfg.soil_variance, cfg.soil_variance))),
            light_level=max(0, cfg.base_light_level + random.uniform(-cfg.light_variance, cfg.light_variance)),
            water_level=max(0,
                            min(100, cfg.base_water_level + random.uniform(-cfg.water_variance, cfg.water_variance))),
            ph_value=cfg.base_ph + random.uniform(-cfg.ph_variance, cfg.ph_variance)
        )

        return events_pb2.BusEvent(
            event_id=self._generate_event_id(),
            module_id=module_id,
            timestamp=self._create_timestamp(),
            sensor_data=sensor_data
        )

    def generate_control_event(self, device: str, is_active: bool,
                               power: float = 100.0, reason: str = "") -> events_pb2.BusEvent:
        return events_pb2.BusEvent(
            event_id=self._generate_event_id(),
            module_id="mcu_control",
            timestamp=self._create_timestamp(),
            control_status=events_pb2.ControlStatus(
                device=device,
                is_active=is_active,
                power_level=power,
                reason=reason
            )
        )

    def generate_alert_event(self, severity: str, code: str, message: str) -> events_pb2.BusEvent:
        return events_pb2.BusEvent(
            event_id=self._generate_event_id(),
            module_id="mcu_alert",
            timestamp=self._create_timestamp(),
            alert=events_pb2.AlertEvent(
                severity=severity,
                code=code,
                message=message
            )
        )

    def broadcast_event(self, event: events_pb2.BusEvent):
        with self.lock:
            for subscriber in self.subscribers:
                # 檢查 module_id 過濾
                if subscriber.module_ids and event.module_id not in subscriber.module_ids:
                    continue

                # 檢查 event_type 過濾
                event_type = event.WhichOneof("payload")
                if subscriber.event_types and event_type not in subscriber.event_types:
                    continue

                try:
                    subscriber.queue.put_nowait(event)
                except queue.Full:
                    print(f"[Broadcast] ⚠ Queue full, dropping event")


class MockEventGenerator:

    def __init__(self, servicer: MockMCUBusServicer):
        self.servicer = servicer
        self.running = False
        self._threads: List[threading.Thread] = []

    def start(self, sensor_interval: float = 2.0,
              control_interval: float = 10.0,
              alert_interval: float = 30.0):
        self.running = True

        t1 = threading.Thread(
            target=self._sensor_loop,
            args=(sensor_interval,),
            daemon=True,
            name="SensorLoop"
        )
        t1.start()
        self._threads.append(t1)

        t2 = threading.Thread(
            target=self._control_loop,
            args=(control_interval,),
            daemon=True,
            name="ControlLoop"
        )
        t2.start()
        self._threads.append(t2)

        t3 = threading.Thread(
            target=self._alert_loop,
            args=(alert_interval,),
            daemon=True,
            name="AlertLoop"
        )
        t3.start()
        self._threads.append(t3)

        print(f"[Generator] Started with intervals: sensor={sensor_interval}s, "
              f"control={control_interval}s, alert={alert_interval}s")

    def stop(self):
        self.running = False

    def _sensor_loop(self, interval: float):
        while self.running:
            event = self.servicer.generate_sensor_event("mcu_sensor_1")
            self.servicer.broadcast_event(event)

            data = event.sensor_data
            print(f"[Sensor] T:{data.temperature:.1f}°C H:{data.humidity:.1f}% "
                  f"Soil:{data.soil_moisture:.1f}% Water:{data.water_level:.1f}% "
                  f"pH:{data.ph_value:.2f}")

            time.sleep(interval)

    def _control_loop(self, interval: float):
        devices = ["cooling_fan", "water_pump", "grow_light", "heater"]

        while self.running:
            device = random.choice(devices)
            is_active = random.choice([True, False])
            power = random.uniform(50, 100) if is_active else 0
            reason = "auto_regulation" if is_active else "threshold_reached"

            event = self.servicer.generate_control_event(device, is_active, power, reason)
            self.servicer.broadcast_event(event)

            status = "ON" if is_active else "OFF"
            print(f"[Control] {device}: {status} ({power:.0f}%) - {reason}")

            time.sleep(interval)

    def _alert_loop(self, interval: float):
        alerts = [
            ("info", "SENSOR_OK", "All sensors operating normally"),
            ("info", "PUMP_CYCLE", "Water pump completed cycle"),
            ("warning", "LOW_WATER", "Water level below 30%"),
            ("warning", "HIGH_TEMP", "Temperature exceeds 30°C"),
            ("warning", "LOW_HUMIDITY", "Humidity below 40%"),
            ("critical", "SENSOR_FAIL", "Soil moisture sensor not responding"),
            ("critical", "PUMP_ERROR", "Water pump malfunction detected"),
        ]

        while self.running:
            weights = [0.4, 0.3, 0.1, 0.08, 0.07, 0.03, 0.02]
            severity, code, message = random.choices(alerts, weights=weights)[0]

            event = self.servicer.generate_alert_event(severity, code, message)
            self.servicer.broadcast_event(event)

            icon = {"info": "ℹ", "warning": "⚠", "critical": "🚨"}.get(severity, "?")
            print(f"[Alert] {icon} [{severity.upper()}] {code}: {message}")

            time.sleep(interval)


def serve(port: int = 50051,
          sensor_interval: float = 2.0,
          control_interval: float = 10.0,
          alert_interval: float = 30.0):
    # build service
    config = MockSensorConfig(
        base_temperature=26.0,
        base_humidity=60.0,
        base_soil_moisture=55.0,
        base_water_level=75.0
    )
    servicer = MockMCUBusServicer(config)

    # build event generator
    generator = MockEventGenerator(servicer)
    generator.start(
        sensor_interval=sensor_interval,
        control_interval=control_interval,
        alert_interval=alert_interval
    )

    # activate gRPC Server
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    mcu_bus_pb2_grpc.add_MCUBusServiceServicer_to_server(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()

    print("=" * 60)
    print(f"🌱 Mock MCU Bus Daemon running on port {port}")
    print("=" * 60)
    print(f"  Sensor interval:  {sensor_interval}s")
    print(f"  Control interval: {control_interval}s")
    print(f"  Alert interval:   {alert_interval}s")
    print("=" * 60)
    print("Waiting for subscribers...")
    print()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping server...")
        generator.stop()
        server.stop(grace=5)
        print("[Shutdown] Server stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mock MCU Bus Daemon")
    parser.add_argument("-p", "--port", type=int, default=50051, help="gRPC port (default: 50051)")
    parser.add_argument("-s", "--sensor-interval", type=float, default=2.0, help="Sensor event interval in seconds")
    parser.add_argument("-c", "--control-interval", type=float, default=10.0, help="Control event interval in seconds")
    parser.add_argument("-a", "--alert-interval", type=float, default=30.0, help="Alert event interval in seconds")

    args = parser.parse_args()

    serve(
        port=args.port,
        sensor_interval=args.sensor_interval,
        control_interval=args.control_interval,
        alert_interval=args.alert_interval
    )
