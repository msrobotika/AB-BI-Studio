"""AB-Suite Core → AB-BI Studio CSV importer bridge (read-only, stdlib).

Connects to the localhost-only SSE bus, records virtual PLC snapshots as a
flat CSV for explicit import into AB-BI Studio. No PLC writes and no tokens
saved to files. Python 3.11+; standalone script.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

COLUMNS = (
    "sequence", "received_at", "simulated_ms", "scenario", "mode", "scan",
    "Q0_0", "Q0_1", "Q0_2", "AI0", "counter_C0", "process_value",
    "process_unit", "active_faults"
)
CONTRACT = "msrobotika.suite.event.v1"
ALLOWED_URL = re.compile(r"^http://127\.0\.0\.1:[0-9]{1,5}$")
TOKEN_FORMAT = re.compile(r"^[a-f0-9]{64}$")

class RejectRedirect(HTTPRedirectHandler):
    """A bus redirect must not forward an application Bearer token."""
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


OPENER = build_opener(RejectRedirect)



def sanitize_url(url: str) -> str:
    if not ALLOWED_URL.fullmatch(url):
        raise ValueError("AB-Suite Core debe estar en 127.0.0.1 y un puerto TCP")
    port = int(url.rsplit(":", 1)[1])
    if not 1 <= port <= 65535:
        raise ValueError("Puerto incorrecto")
    return url


def snapshot_to_row(event: dict) -> dict | None:
    """Convert a validated PLC event to a small flat table; ignore others."""
    if not isinstance(event, dict) or event.get("schema") != CONTRACT:
        return None
    if event.get("source") != "ab-plc-simulator" or event.get("topic") != "plc.snapshot":
        return None
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    sequence = event.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        return None
    if data.get("mode") not in {"RUN", "PAUSE", "STOP"}:
        return None
    inputs = data.get("inputs", {})
    outputs = data.get("outputs", {})
    analog = data.get("analog", {})
    counters = data.get("counters", {})
    process = data.get("process", {})
    faults = data.get("faults", {})
    if not all(isinstance(d, dict) for d in (inputs, outputs, analog, counters, process, faults)):
        return None
    kind = process.get("kind")
    if kind == "tank":
        value, unit = process.get("level", 0), "percent"
    elif kind == "conveyor":
        value, unit = process.get("delivered", 0), "packages"
    else:
        value, unit = 0, "none"
    def signal(tag: str) -> int:
        return int(outputs.get(tag) is True)
    return {
        "sequence": sequence,
        "received_at": str(event.get("received_at", "")),
        "simulated_ms": event.get("simulated_ms", ""),
        "scenario": str(data.get("scenario", "")),
        "mode": data["mode"],
        "scan": data.get("scan", 0),
        "Q0_0": signal("Q0.0"),
        "Q0_1": signal("Q0.1"),
        "Q0_2": signal("Q0.2"),
        "AI0": analog.get("AI0", 0),
        "counter_C0": counters.get("C0", 0),
        "process_value": value,
        "process_unit": unit,
        "active_faults": "|".join(k for k, v in sorted(faults.items()) if v is True)
    }


def previous_sequence(path: Path) -> int:
    """Use actual CSV content for replay: avoids data loss after interruption."""
    if not path.is_file() or path.stat().st_size == 0:
        return 0
    last = 0
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(COLUMNS):
            raise ValueError("Cabecera CSV incompatible; usa otro archivo")
        for row in reader:
            try:
                sequence = int(row["sequence"])
            except (ValueError, KeyError, TypeError):
                raise ValueError("CSV existente contiene una fila inválida") from None
            if sequence <= last:
                raise ValueError("CSV contiene secuencias desordenadas")
            last = sequence
    return last


def events_from_sse(url: str, token: str, after: int):
    """Yield JSON events from authenticated SSE. No auto-retry or hidden skip."""
    url = sanitize_url(url)
    if not TOKEN_FORMAT.fullmatch(token):
        raise ValueError("AB_SUITE_TOKEN debe ser un token de sesión hexadecimal de 64 caracteres")
    request = Request(
        f"{url}/v1/events?after={after}",
        headers={"Authorization": f"Bearer {token}", "Accept": "text/event-stream"},
        method="GET",
    )
    with OPENER.open(request, timeout=60) as response:
        lines: list[str] = []
        for raw in response:
            line = raw.decode("utf-8").rstrip("\r\n")
            if not line:
                payload = next((part[6:] for part in lines if part.startswith("data: ")), None)
                lines.clear()
                if payload is not None:
                    yield json.loads(payload)
            elif not line.startswith(":"):
                lines.append(line)
                if sum(len(value) for value in lines) > 100_000:
                    raise ValueError("Evento SSE excesivamente grande")


def record(url: str, token: str, output: Path, max_rows: int) -> int:
    """Append and flush each PLC snapshot, preserving replay cursor on disk."""
    if not 1 <= max_rows <= 40_000:
        raise ValueError("max_rows debe estar entre 1 y 40000")
    output.parent.mkdir(parents=True, exist_ok=True)
    last = previous_sequence(output)
    is_new = not output.exists() or output.stat().st_size == 0
    rows = 0
    with output.open("a", newline="", encoding="utf-8-sig" if is_new else "utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
            handle.flush()
            os.fsync(handle.fileno())
        print(f"AB-Suite → AB-BI: {url}, CSV={output}, después de seq={last}")
        for event in events_from_sse(url, token, last):
            row = snapshot_to_row(event)
            if row is None or row["sequence"] <= last:
                continue
            writer.writerow(row)
            handle.flush()
            os.fsync(handle.fileno())
            last = row["sequence"]
            rows += 1
            if rows >= max_rows:
                break
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description="Telemetría virtual AB-Suite Core a CSV AB-BI Studio")
    p.add_argument("--url", default="http://127.0.0.1:4175")
    p.add_argument("--out", type=Path, default=Path("ab_suite_plc_telemetry.csv"))
    p.add_argument("--max-rows", type=int, default=40_000)
    args = p.parse_args()
    try:
        token = os.environ.get("AB_SUITE_TOKEN", "")
        count = record(args.url, token, args.out, args.max_rows)
        print(f"Filas añadidas: {count}. Importa el CSV desde AB-BI Studio.")
        return 0
    except (ValueError, HTTPError, URLError, OSError) as exc:
        print(f"Error de conexión/CSV: {exc}", file=sys.stderr)
        print("Si el bus responde 409, se perdió histórico: no avances el cursor a ciegas.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nGrabación finalizada por el usuario.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
