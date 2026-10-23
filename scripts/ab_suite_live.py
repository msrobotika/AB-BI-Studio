"""Opt-in AB-Suite Core SSE → AB-BI Studio live semantic table connector.

No CSV reimport, browser credentials, camera feeds or PLC writes. The BI API
must be launched with ABBI_SUITE_WRITE_TOKEN set to enable mutations.
Python 3.11+; uses only standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, HTTPRedirectHandler, Request

if __package__:
    from .ab_suite_telemetry import events_from_sse, snapshot_to_row
else:
    from ab_suite_telemetry import events_from_sse, snapshot_to_row

SCHEMA = "msrobotika.bi.suite.ingest.v1"
URL = re.compile(r"^http://127\.0\.0\.1:([0-9]{1,5})$")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, target):
        return None


OPENER = build_opener(NoRedirect)


def local_address(url: str) -> str:
    found = URL.fullmatch(url)
    if not found or not 1 <= int(found.group(1)) <= 65535:
        raise ValueError("Se requiere una URL de 127.0.0.1 con puerto")
    return url


def credentials() -> tuple[str, str]:
    bus = os.environ.get("AB_SUITE_TOKEN", "")
    bi = os.environ.get("ABBI_SUITE_WRITE_TOKEN", "")
    if not re.fullmatch(r"[a-f0-9]{64}", bus):
        raise ValueError("Configura AB_SUITE_TOKEN (monitor, 64 caracteres hexadecimales)")
    if len(bi) < 32:
        raise ValueError("Configura ABBI_SUITE_WRITE_TOKEN (mínimo 32 caracteres)")
    return bus, bi


def bi_request(base: str, token: str, route: str, payload: dict | None = None) -> dict:
    local_address(base)
    data = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
    request = Request(base + route, method="GET" if data is None else "POST",
                      data=data, headers={
                          "X-ABBI-Suite-Token": token,
                          **({"Content-Type": "application/json"} if data is not None else {})
                      })
    with OPENER.open(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError("Respuesta inesperada de AB-BI")
        return json.load(response)


def run(*, bus_url: str, bi_url: str, batch_size: int = 5,
        max_rows: int = 40_000) -> int:
    local_address(bus_url)
    local_address(bi_url)
    if not 1 <= batch_size <= 50 or not 1 <= max_rows <= 40_000:
        raise ValueError("Límites de lote o sesión incorrectos")
    bus_token, bi_token = credentials()
    session = hashlib.sha256(bus_token.encode("ascii")).hexdigest()[:24]
    status = bi_request(bi_url, bi_token, "/api/suite/status")
    cursor = status["last_sequence"] if status.get("session_id") == session else 0
    pending = []
    added = 0

    def flush() -> int:
        nonlocal pending, cursor
        if not pending:
            return 0
        response = bi_request(bi_url, bi_token, "/api/suite/ingest", {
            "schema": SCHEMA, "session_id": session, "rows": pending
        })
        if response.get("inserted", 0) + response.get("duplicates", 0) != len(pending):
            raise RuntimeError("AB-BI no confirmó todos los registros")
        count = response["inserted"]
        cursor = max(cursor, response["last_sequence"])
        pending = []
        return count

    print(f"Suite Core → AB-BI: {bus_url} → {bi_url}, desde evento {cursor}")
    try:
        for event in events_from_sse(bus_url, bus_token, cursor):
            row = snapshot_to_row(event)
            if row is None or row["sequence"] <= cursor:
                continue
            pending.append(row)
            if len(pending) >= batch_size or added + len(pending) >= max_rows:
                added += flush()
                print(f"Importadas {added} lecturas; último evento {cursor}")
                if added >= max_rows:
                    break
    except KeyboardInterrupt:
        print("\nDeteniendo con las lecturas ya recibidas…")
    finally:
        if pending:
            added += flush()
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description="AB-Suite Core → tabla AB-BI Studio en vivo")
    parser.add_argument("--bus-url", default="http://127.0.0.1:4175")
    parser.add_argument("--bi-url", default="http://127.0.0.1:8765")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--max-rows", type=int, default=40_000)
    a = parser.parse_args()
    try:
        inserted = run(bus_url=a.bus_url, bi_url=a.bi_url,
                       batch_size=a.batch_size, max_rows=a.max_rows)
        print(f"Finalizado: {inserted} lecturas insertadas en el modelo AB-BI.")
        return 0
    except (ValueError, HTTPError, URLError, OSError, RuntimeError, KeyError) as error:
        print(f"Suite Live: {error}", file=sys.stderr)
        print("Un HTTP 409 del bus significa pérdida de histórico: no se salta el cursor.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
