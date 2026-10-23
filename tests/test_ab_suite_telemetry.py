"""Offline unit tests for Suite Core CSV ingestion; no network required."""
from pathlib import Path
import tempfile
import unittest

from scripts.ab_suite_telemetry import (
    snapshot_to_row, previous_sequence, sanitize_url, COLUMNS
)
from csv import DictWriter


def sample(seq: int = 5, kind: str = "conveyor") -> dict:
    return {
        "schema": "msrobotika.suite.event.v1",
        "source": "ab-plc-simulator",
        "topic": "plc.snapshot",
        "sequence": seq,
        "received_at": "2026-10-23T00:00:00.000Z",
        "simulated_ms": 500,
        "data": {
            "scan": seq, "scenario": kind, "mode": "RUN",
            "inputs": {"I0.0": True},
            "outputs": {"Q0.0": True, "Q0.1": False},
            "analog": {"AI0": 55.5},
            "counters": {"C0": 5},
            "process": {"kind": kind, "delivered": 3, "level": 88},
            "faults": {"jam": False}
        }
    }


class AB_SuiteTelemetryTests(unittest.TestCase):
    def test_conveyor_snapshot(self):
        row = snapshot_to_row(sample())
        self.assertEqual(row["Q0_0"], 1)
        self.assertEqual(row["process_value"], 3)
        self.assertEqual(row["process_unit"], "packages")
        self.assertEqual(row["AI0"], 55.5)

    def test_tank_snapshot(self):
        row = snapshot_to_row(sample(kind="tank"))
        self.assertEqual(row["process_value"], 88)
        self.assertEqual(row["process_unit"], "percent")

    def test_ignores_other_topics(self):
        message = sample()
        message["topic"] = "vision.inspection.result"
        self.assertIsNone(snapshot_to_row(message))

    def test_rejects_other_hosts(self):
        with self.assertRaises(ValueError):
            sanitize_url("http://192.168.1.22:4175")
        with self.assertRaises(ValueError):
            sanitize_url("https://example.org")
        self.assertEqual(sanitize_url("http://127.0.0.1:4175"),
                         "http://127.0.0.1:4175")

    def test_cursor_scans_actual_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "samples.csv"
            self.assertEqual(previous_sequence(output), 0)
            with output.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerow(snapshot_to_row(sample(5)))
                writer.writerow(snapshot_to_row(sample(6)))
            self.assertEqual(previous_sequence(output), 6)

    def test_corrupt_duplicate_cursor_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "samples.csv"
            with output.open("w", newline="", encoding="utf-8") as handle:
                writer = DictWriter(handle, fieldnames=COLUMNS)
                writer.writeheader()
                writer.writerow(snapshot_to_row(sample(5)))
                writer.writerow(snapshot_to_row(sample(5)))
            with self.assertRaises(ValueError):
                previous_sequence(output)


if __name__ == "__main__":
    unittest.main()
