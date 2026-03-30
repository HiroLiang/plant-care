from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.control import ActuatorAction, CommandStatus, DeviceType, SensorType, ValueUnit


class ActuatorControlRequest(BaseModel):
    node_id: int = Field(gt=0)
    device_type: DeviceType
    action: ActuatorAction
    level: float | None = None

    @model_validator(mode="after")
    def validate_level_rules(self) -> "ActuatorControlRequest":
        if self.action == ActuatorAction.SET_LEVEL and self.level is None:
            raise ValueError("level is required when action is set_level")
        if self.action != ActuatorAction.SET_LEVEL and self.level is not None:
            raise ValueError("level is only allowed when action is set_level")
        return self


class TelemetryRequestCommandRequest(BaseModel):
    node_id: int = Field(gt=0)
    sensor_types: list[SensorType] = Field(default_factory=list)


class ResetNodeRequest(BaseModel):
    node_id: int = Field(gt=0)
    reason: str | None = None


class SetThresholdRequest(BaseModel):
    node_id: int = Field(gt=0)
    sensor_type: SensorType
    value: float
    unit: ValueUnit
    channel: str | None = None


class CommandTargetResponse(BaseModel):
    node_id: int


class CommandDispatchResponse(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    command_id: str
    accepted: bool
    status: CommandStatus
    message: str
    accepted_at: datetime | None
    target: CommandTargetResponse
