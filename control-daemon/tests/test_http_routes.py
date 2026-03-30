def test_health_route(client):
    response = client.get("/daemon/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_actuator_route_returns_dispatch_payload(client, service_stub):
    response = client.post(
        "/controls/actuators",
        json={"node_id": 7, "device_type": "pump", "action": "on"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "command_id": "cmd-123",
        "accepted": False,
        "status": "unsupported",
        "message": "Not wired yet",
        "accepted_at": None,
        "target": {"node_id": 7},
    }


def test_telemetry_request_route_happy_path(client, service_stub):
    response = client.post(
        "/controls/telemetry-requests",
        json={"node_id": 7, "sensor_types": ["temperature", "humidity"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["command_id"] == "cmd-telemetry"
    assert body["status"] == "accepted"
    assert body["target"] == {"node_id": 7}


def test_reset_route_happy_path(client, service_stub):
    response = client.post("/controls/resets", json={"node_id": 7, "reason": "maintenance"})

    assert response.status_code == 200
    assert response.json()["command_id"] == "cmd-reset"


def test_threshold_route_happy_path(client, service_stub):
    response = client.post(
        "/controls/thresholds",
        json={
            "node_id": 7,
            "sensor_type": "humidity",
            "value": 60.0,
            "unit": "percent",
            "channel": "zone-a",
        },
    )

    assert response.status_code == 200
    assert response.json()["command_id"] == "cmd-threshold"


def test_actuator_route_rejects_invalid_level_payload(client):
    response = client.post(
        "/controls/actuators",
        json={"node_id": 7, "device_type": "pump", "action": "on", "level": 0.5},
    )

    assert response.status_code == 422


def test_request_validation_rejects_missing_level_for_set_level(client):
    response = client.post(
        "/controls/actuators",
        json={"node_id": 7, "device_type": "light", "action": "set_level"},
    )

    assert response.status_code == 422
