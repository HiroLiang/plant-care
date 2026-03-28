from datetime import timezone

from domain.mcu_bus_event import MCUBusEvent, BusPayload, AlertEvent, SensorDataEvent, ControlStatusEvent
import sys
from pathlib import Path

GENERATED_ROOT = Path(__file__).resolve().parents[3] / "plant-core" / "src" / "generated"
generated_root_str = str(GENERATED_ROOT)
if generated_root_str not in sys.path:
    sys.path.insert(0, generated_root_str)

from mcubus.v1 import events_pb2


def to_domain(event: events_pb2.BusEvent) -> MCUBusEvent:
    return MCUBusEvent(
        event_id=event.event_id,
        module_id=event.module_id,
        timestamp=event.timestamp.ToDatetime().replace(tzinfo=timezone.utc),
        payload=to_payload(event),
    )


def to_payload(event: events_pb2.BusEvent) -> BusPayload:
    payload_type = event.WhichOneof("payload")

    if payload_type == "sensor_data":
        sd = event.sensor_data
        return SensorDataEvent(
            temperature=sd.temperature,
            humidity=sd.humidity,
            soil_moisture=sd.soil_moisture,
            light_level=sd.light_level,
            water_level=sd.water_level,
            ph_value=sd.ph_value,
        )

    if payload_type == "control_status":
        cs = event.control_status
        return ControlStatusEvent(
            device=cs.device,
            is_active=cs.is_active,
            power_level=cs.power_level,
            reason=cs.reason,
        )

    if payload_type == "alert":
        al = event.alert
        return AlertEvent(
            severity=al.severity,
            code=al.code,
            message=al.message,
        )

    raise ValueError(f"Unknown payload type: {payload_type}")
