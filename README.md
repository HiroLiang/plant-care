# Plant Care System

An IoT monorepo for plant monitoring and control on Raspberry Pi + STM32 hardware.

The system is split into small services: the STM32 publishes sensor data over CAN bus, the Raspberry Pi receives and exposes it through gRPC and HTTP, and the web UI consumes those APIs for monitoring and control.

## Architecture

```text
STM32 MCU (CAN bus)
    -> SocketCAN
mcu-bus-daemon  (gRPC :50051)
    -> gRPC event stream
monitor-daemon  (HTTP :8001)
    -> REST API
ui-web          (React / Vite)
```

`monitor-daemon` can also talk to:

- `control-daemon` for command/control flows
- local sensors on Raspberry Pi, such as SHT31

## Repository Layout

| Path | Role |
| --- | --- |
| `plant-core/` | Shared protobuf definitions, generated gRPC stubs, and core domain models |
| `mcu-bus-daemon/` | SocketCAN + gRPC bridge for MCU events |
| `monitor-daemon/` | FastAPI service that aggregates sensor readings and exposes HTTP APIs |
| `control-daemon/` | Minimal command/control service |
| `ui-web/` | React + TypeScript frontend |
| `firmware/` | STM32 firmware project |

## Python Service Structure

The Python services follow a similar clean architecture layout:

```text
domain/          # entities, protocols, value objects
application/     # use cases and orchestration
infrastructure/  # gRPC, CAN, SQLite, HTTP, sensor adapters
interface/       # FastAPI routers or gRPC servicers
bootstrap/       # dependency wiring and app context
```

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm for `ui-web`
- Raspberry Pi + SocketCAN setup if running against real hardware

## Getting Started

### 1. Install Python workspace dependencies

```bash
uv sync
```

### 2. Run backend services

Start `mcu-bus-daemon` first:

```bash
uv run --package mcu-bus-daemon mcu-bus-daemon
```

Optional flags:

```bash
uv run --package mcu-bus-daemon mcu-bus-daemon --port 50051 --channel can0 --bitrate 500000
```

Then start `monitor-daemon`:

```bash
cd monitor-daemon
python src/main.py
```

Or:

```bash
cd monitor-daemon
make dev
```

### 2a. Raspberry Pi `can0` bring-up for STM32 validation

Bring the CAN interface up on the Pi before starting `mcu-bus-daemon`:

```bash
sudo ip link set can0 down || true
sudo ip link set can0 up type can bitrate 500000
ip -details link show can0
```

Validate that the STM32 is already sending raw frames:

```bash
candump can0
```

Expected traffic from the current firmware:

- `0x083` for combined temperature/humidity payloads (`<hHB>`) every 2 seconds
- `0x0A2` for heartbeat payloads (`<BBHI>`) every 5 seconds

Once raw frames are visible, start the daemon:

```bash
uv run --package mcu-bus-daemon mcu-bus-daemon --channel can0 --bitrate 500000
```

Expected bring-up sequence:

1. `can0` comes up at `500000` bps.
2. `candump can0` shows `0x083` and `0x0A2`.
3. `mcu-bus-daemon` logs CAN connection success and incoming heartbeat / temperature-humidity events.
4. gRPC clients subscribe through `SubscribeEvents` and receive translated `BusEvent` messages.

`Register` and `UnRegister` intentionally return `UNIMPLEMENTED` during this bring-up phase.

### 3. Run frontend

```bash
cd ui-web
npm install
npm run dev
```

## monitor-daemon Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `HTTP_HOST` | `0.0.0.0` | HTTP bind address |
| `HTTP_PORT` | `8001` | HTTP port |
| `RUNTIME_ENV` | `mock` | `mock` or `rasp`; enables real hardware-specific sensor setup |
| `MCU_BUS_DAEMON_HOST` | `localhost` | gRPC host for `mcu-bus-daemon` |
| `MCU_BUS_DAEMON_PORT` | `50051` | gRPC port for `mcu-bus-daemon` |
| `CTRL_DAEMON_URL` | `http://localhost:8000` | Control daemon base URL |
| `DB_PATH` | `data/dev.sqlite3` | SQLite database path |

Example:

```bash
cd monitor-daemon
RUNTIME_ENV=mock HTTP_PORT=8001 python src/main.py
```

## Development Commands

### Run tests

From repository root:

```bash
uv run pytest
```

Run a single test file:

```bash
uv run pytest mcu-bus-daemon/tests/test_can_protocol.py
```

Run tests inside a package:

```bash
cd mcu-bus-daemon && uv run pytest
cd monitor-daemon && uv run pytest
```

### Regenerate protobuf stubs

Proto files live in `plant-core/proto/mcubus/v1/`.
Generated files are written to `plant-core/src/generated/mcubus/v1/`.

```bash
python -m grpc_tools.protoc -I plant-core/proto \
  --python_out=plant-core/src/generated \
  --grpc_python_out=plant-core/src/generated \
  plant-core/proto/mcubus/v1/*.proto
```

## Notes

- `mcu-bus-daemon` owns CAN bus ingestion and event fan-out to gRPC subscribers.
- `monitor-daemon` translates bus events into domain sensor readings and serves them over HTTP.
- `plant-core` is the shared contract layer between services.
