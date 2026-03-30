# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An IoT monorepo for plant monitoring and control, targeting Raspberry Pi + STM32 MCU hardware. The Python backend is managed as a UV workspace.

## Commands

### Package Management (UV workspace)

```bash
# Install all workspace deps
uv sync

# Run tests (from workspace root)
uv run pytest

# Run a single test file
uv run pytest mcu-bus-daemon/tests/test_foo.py

# Run tests within a specific package
cd mcu-bus-daemon && uv run pytest
cd monitor-daemon && uv run pytest
```

### Running Services

```bash
# mcu-bus-daemon (gRPC server, port 50051)
cd mcu-bus-daemon && PYTHONPATH=src python src/main.py
cd mcu-bus-daemon && PYTHONPATH=src python src/main.py --port 50051

# monitor-daemon (FastAPI/uvicorn, port 8001)
cd monitor-daemon && python src/main.py
# or
cd monitor-daemon && make dev

# control-daemon (FastAPI/uvicorn, port 8000)
cd control-daemon && python src/main.py
```

### Regenerating Protobuf Stubs

Protos live in `plant-core/proto/mcubus/v1/`. Generated stubs are in `plant-core/src/plant_core/generated/mcubus/v1/`. Regenerate with:

```bash
python -m grpc_tools.protoc -I plant-core/proto \
  --python_out=plant-core/src/plant_core/generated \
  --grpc_python_out=plant-core/src/plant_core/generated \
  plant-core/proto/mcubus/v1/*.proto
```

## Architecture

### Service Topology

```
STM32 MCU (CAN bus)
    ↓ SocketCAN
mcu-bus-daemon  (gRPC :50051)
    ↓ gRPC event stream
monitor-daemon  (HTTP :8001)
    ↓ REST
ui-web          (React/Vite)
```

`monitor-daemon` also talks to `control-daemon` (HTTP :8000) and local I²C sensors (SHT31 via RS485/direct).

### Packages

| Package | Role |
|---|---|
| `plant-core` | Shared protobuf stubs, domain models, SQLite infrastructure (`plant_core` namespace) |
| `mcu-bus-daemon` | gRPC server; owns CAN bus I/O and fan-out to subscribers |
| `monitor-daemon` | FastAPI HTTP server; aggregates sensor readings, talks to mcu-bus-daemon |
| `control-daemon` | FastAPI HTTP server; forwards commands from monitor-daemon to mcu-bus-daemon via gRPC |
| `ui-web` | React + TypeScript frontend |
| `firmware/` | STM32 C firmware (STM32CubeIDE) |

### Clean Architecture Layers (Python services)

Each daemon follows the same layered structure:

```
domain/          # Entities, protocols, value objects — no I/O
application/     # Use-case services, orchestration
infrastructure/  # Concrete I/O: CAN bus, gRPC clients, SQLite, HTTP clients
interface/       # HTTP routers (FastAPI) or gRPC servicers
bootstrap/       # Wiring: builds AppContext, injects dependencies
```

### Key Domain Concepts

**mcu-bus-daemon**
- `Subscriber` (dataclass): UUID + `queue.Queue` for event delivery; created by `SubscriptionHandler`
- `SubscriptionHandler` (ABC): manages subscriber lifecycle with RLock; `RpcSubscriptionHandler` streams events over gRPC
- `CANDaemon`: wraps SocketCAN socket; runs RX loop in a thread; routes parsed frames to `SubscriptionHandler`
- CAN ID encoding: 4-bit node ID + 6-bit data type packed into 11-bit CAN ID (see `can_protocol.py`)

**monitor-daemon**
- `SensorModule` (Protocol): collection of `Sensor` objects; types are LOCAL (direct I²C) or MCU_SERIAL (via gRPC)
- `SensorReading` (dataclass): `sensor_id`, `type`, `value`, `unit`, `timestamp`
- `McuBusClient` (application layer): subscribes to mcu-bus-daemon, translates gRPC events to domain `SensorReading`s
- `AppContext` (bootstrap): holds db, clients, services; initialized in FastAPI lifespan

**control-daemon**
- Minimal FastAPI service (HTTP :8000); receives commands from `monitor-daemon` and forwards them over gRPC to `mcu-bus-daemon`
- `AppContext` (bootstrap): holds clients and services; no database

**plant-core**
- Python package name is `plant_core` (import as `from plant_core.generated.mcubus.v1 import ...`)
- Proto definitions: `common.proto`, `events.proto`, `event_service.proto`, `commands.proto`, `command_service.proto`
- `EventService` gRPC: `Register`, `UnRegister`, `SubscribeEvents` (server-streaming); `CommandService` gRPC: sends commands to MCU
- Shared SQLite infrastructure: `plant_core.infrastructure.persistence.sqlite` — `DataSource`, repositories, schema, and mappers used by both `monitor-daemon` and `control-daemon`
- Shared domain models in `plant_core.domain`: `Sensor`, `Device`, `Node`, `Command`, `Event`; ports/interfaces in `plant_core.ports`

### Environment Variables (monitor-daemon)

| Variable | Default | Description |
|---|---|---|
| `HTTP_HOST` | `0.0.0.0` | Bind address |
| `HTTP_PORT` | `8001` | HTTP port |
| `RUNTIME_ENV` | `mock` | `mock` or `rasp` (enables real SHT31 sensor) |
| `MCU_BUS_DAEMON_HOST` | `localhost` | gRPC host |
| `MCU_BUS_DAEMON_PORT` | `50051` | gRPC port |
| `CTRL_DAEMON_URL` | `http://localhost:8000` | Control daemon URL |
| `DB_PATH` | `data/dev.sqlite3` | SQLite path |

### Testing Patterns

- `mcu-bus-daemon` tests use `FakeSubscriptionHandler` (in `tests/fake/`) to avoid real CAN bus
- `monitor-daemon` uses `FakeEventStub` to mock gRPC streaming without a real server
- Each package has a `test_import_smoke.py` that verifies top-level imports work (catches missing deps early)
- `PYTHONPATH=src` is set via `pytest.ini_options` in `monitor-daemon`'s `pyproject.toml`; `mcu-bus-daemon` requires it set manually
- Tests that import from `plant-core` add `plant-core/src` to `sys.path` via `conftest.py` (not via the workspace install) — keep this pattern when adding new cross-package tests
