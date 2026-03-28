import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = PROJECT_ROOT / "plant-core" / "src" / "generated"

generated_root_str = str(GENERATED_ROOT)
if generated_root_str not in sys.path:
    sys.path.insert(0, generated_root_str)

from mcubus.v1 import commands_pb2, common_pb2, events_pb2


def test_actuator_command_round_trip():
    request = commands_pb2.DispatchCommandRequest(
        command=commands_pb2.McuCommand(
            command_id="cmd-1",
            correlation_id="http-req-1",
            issued_by="control-daemon",
            type=common_pb2.COMMAND_TYPE_ACTUATOR,
            actuator_command=commands_pb2.ActuatorCommand(
                device_type=common_pb2.DEVICE_TYPE_PUMP,
                operation=common_pb2.ACTUATOR_OPERATION_SET_LEVEL,
                level=0.75,
            ),
        )
    )

    parsed = commands_pb2.DispatchCommandRequest()
    parsed.ParseFromString(request.SerializeToString())

    assert parsed.command.command_id == "cmd-1"
    assert parsed.command.actuator_command.device_type == common_pb2.DEVICE_TYPE_PUMP
    assert parsed.command.actuator_command.level == 0.75


def test_telemetry_event_round_trip():
    event = events_pb2.BusEvent(
        event_id="evt-1",
        source_node_id=1,
        event_type=common_pb2.EVENT_TYPE_TELEMETRY,
        telemetry=events_pb2.TelemetryEvent(
            readings=[
                events_pb2.SensorReading(
                    sensor_type=common_pb2.SENSOR_TYPE_TEMPERATURE,
                    value=25.5,
                    unit=common_pb2.VALUE_UNIT_CELSIUS,
                    status=common_pb2.READING_STATUS_OK,
                )
            ]
        ),
    )

    parsed = events_pb2.BusEvent()
    parsed.ParseFromString(event.SerializeToString())

    assert parsed.event_id == "evt-1"
    assert parsed.telemetry.readings[0].sensor_type == common_pb2.SENSOR_TYPE_TEMPERATURE
    assert parsed.telemetry.readings[0].value == 25.5


def test_command_result_event_keeps_command_id():
    event = events_pb2.BusEvent(
        event_id="evt-2",
        source_node_id=1,
        command_id="cmd-42",
        event_type=common_pb2.EVENT_TYPE_COMMAND_RESULT,
        command_result=events_pb2.CommandResultEvent(
            command_id="cmd-42",
            status=common_pb2.COMMAND_STATUS_FAILED,
            message="pump controller timeout",
            device_type=common_pb2.DEVICE_TYPE_PUMP,
        ),
    )

    parsed = events_pb2.BusEvent()
    parsed.ParseFromString(event.SerializeToString())

    assert parsed.command_id == "cmd-42"
    assert parsed.command_result.command_id == "cmd-42"
    assert parsed.command_result.status == common_pb2.COMMAND_STATUS_FAILED
