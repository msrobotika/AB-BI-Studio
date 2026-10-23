"""Opt-in live Suite Core ingestion tests; isolated model/workspace, no PLC."""
import pytest
from fastapi.testclient import TestClient

from backend import server as api
from backend.suite_live import append_batch, parse_row, SCHEMA, TABLE
from scripts.ab_suite_telemetry import snapshot_to_row


def sample_event(sequence=1, mode="RUN"):
    return {
        "schema": "msrobotika.suite.event.v1", "source": "ab-plc-simulator",
        "topic": "plc.snapshot", "sequence": sequence,
        "received_at": "2026-10-23T09:00:00Z", "simulated_ms": sequence * 100,
        "data": {"scan": sequence, "scenario": "conveyor", "mode": mode,
                 "inputs": {"I0.0": True},
                 "outputs": {"Q0.0": True, "Q0.1": False, "Q0.2": False},
                 "analog": {"AI0": 17.5}, "counters": {"C0": 1},
                 "process": {"kind": "conveyor", "delivered": sequence},
                 "faults": {}}
    }


def sample_row(seq=1):
    value = snapshot_to_row(sample_event(seq))
    assert value is not None
    return value


def test_validate_real_bridge_row():
    parsed = parse_row(sample_row(1))
    assert parsed["mode"] == "RUN"
    assert parsed["Q0_0"] == 1
    assert parsed["sequence"] == 1


def test_append_preserves_model_and_deduplicates():
    original = api.demo()
    a, inserted, skipped = append_batch(original, [sample_row(1)], "a" * 24)
    assert (inserted, skipped) == (1, 0)
    assert TABLE not in original["tables"]
    assert a["tables"][TABLE][0]["session_id"] == "a" * 24
    b, inserted, skipped = append_batch(a, [sample_row(1), sample_row(2)], "a" * 24)
    assert (inserted, skipped) == (1, 1)
    assert len(b["tables"][TABLE]) == 2
    c, inserted, skipped = append_batch(b, [sample_row(1)], "b" * 24)
    assert (inserted, skipped) == (1, 0)
    assert c["tables"][TABLE][-1]["session_id"] == "b" * 24


def test_collision_prevents_overwriting_existing_table():
    model = api.demo()
    model["tables"][TABLE] = [{"custom": "original"}]
    with pytest.raises(Exception, match="ajena"):
        append_batch(model, [sample_row(1)], "a" * 24)
    assert model["tables"][TABLE] == [{"custom": "original"}]


def test_malformed_row_and_limit_rejected():
    model = api.demo()
    bad = sample_row()
    bad["AI0"] = float("nan")
    with pytest.raises(Exception, match="analógica"):
        append_batch(model, [bad], "a" * 24)
    with pytest.raises(Exception, match="lote"):
        append_batch(model, [sample_row()] * 51, "a" * 24)


@pytest.fixture()
def live_client(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "MODEL", api.demo())
    monkeypatch.setattr(api, "STATE", tmp_path / "workspace.json")
    monkeypatch.setenv("ABBI_SUITE_WRITE_TOKEN", "s" * 40)
    with TestClient(api.app, base_url="http://127.0.0.1:8765") as client:
        yield client


def test_api_local_ingest_auth_persist_and_replay(live_client):
    secret = {"X-ABBI-Suite-Token": "s" * 40}
    payload = {"schema": SCHEMA, "session_id": "f" * 24,
               "rows": [sample_row(1), sample_row(2)]}
    assert live_client.post("/api/suite/ingest", json=payload).status_code == 403
    assert live_client.post("/api/suite/ingest", json=payload,
                            headers={"X-ABBI-Suite-Token": "invalid"}).status_code == 403
    first = live_client.post("/api/suite/ingest", json=payload, headers=secret)
    assert first.status_code == 200, first.text
    assert first.json()["inserted"] == 2
    assert live_client.get("/api/model").json()["tables"][-1]["name"] == TABLE
    assert live_client.get("/api/suite/status", headers=secret).json()["last_sequence"] == 2
    replay = live_client.post("/api/suite/ingest", json=payload, headers=secret)
    assert replay.json()["duplicates"] == 2
    assert replay.json()["inserted"] == 0
    assert live_client.get("/api/suite/summary").json()["rows"] == 2
    assert len(api.MODEL["tables"][TABLE]) == 2
    assert api.STATE.exists()


def test_disabled_without_explicit_operator_token(live_client, monkeypatch):
    monkeypatch.delenv("ABBI_SUITE_WRITE_TOKEN")
    result = live_client.post("/api/suite/ingest",
                              json={"schema": SCHEMA, "session_id": "a" * 24,
                                    "rows": [sample_row()]})
    assert result.status_code == 503
    assert live_client.get("/api/suite/summary").json()["enabled"] is False
    assert TABLE not in api.MODEL["tables"]
