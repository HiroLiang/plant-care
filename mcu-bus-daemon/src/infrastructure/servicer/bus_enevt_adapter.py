from datetime import timezone
from domain.mcu_bus import BusEvent, SensorDataEvent, ControlStatusEvent, AlertEvent
from google.protobuf.timestamp_pb2 import Timestamp
from generated.mcubus.v1 import events_pb2


def to_proto(event: BusEvent) -> events_pb2.BusEvent:
    proto = events_pb2.BusEvent(
        event_id=event.event_id,
        module_id=event.module_id,
    )

    # timestamp
    ts = Timestamp()
    ts.FromDatetime(event.timestamp.replace(tzinfo=timezone.utc))
    proto.timestamp.CopyFrom(ts)

    # payload
    match event.payload:
        case SensorDataEvent():
            proto.sensor_data.CopyFrom(
                events_pb2.SensorData(
                    temperature=event.payload.temperature,
                    humidity=event.payload.humidity,
                    soil_moisture=event.payload.soil_moisture,
                    light_level=event.payload.light_level,
                    water_level=event.payload.water_level,
                    ph_value=event.payload.ph_value,
                )
            )

        case ControlStatusEvent():
            proto.control_status.CopyFrom(
                events_pb2.ControlStatus(
                    device=event.payload.device,
                    is_active=event.payload.is_active,
                    power_level=event.payload.power_level,
                    reason=event.payload.reason,
                )
            )

        case AlertEvent():
            proto.alert.CopyFrom(
                events_pb2.AlertEvent(
                    severity=event.payload.severity,
                    code=event.payload.code,
                    message=event.payload.message,
                )
            )

        case _:
            raise ValueError(f"Unsupported payload type: {type(event.payload)}")

    return proto
