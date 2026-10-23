"""Validated live telemetry table for AB-BI Studio's existing semantic model.

Input only from a deliberate localhost companion process with a private token.
No Core SDK import, no duplicate BI engine and no industrial control.
"""
from __future__ import annotations

import copy
import math
import re

from .semantic import SemanticError, model_validate

TABLE = "SuitePLC"
SCHEMA = "msrobotika.bi.suite.ingest.v1"
FIELDS = (
    "sequence", "received_at", "simulated_ms", "scenario", "mode", "scan",
    "Q0_0", "Q0_1", "Q0_2", "AI0", "counter_C0", "process_value",
    "process_unit", "active_faults"
)
SESSION_PATTERN = re.compile(r"^[0-9a-f]{24}$")
MAX_BATCH = 50


def parse_row(row: object) -> dict:
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise SemanticError("La lectura Suite no coincide con el contrato tabular")
    if (isinstance(row["sequence"], bool) or
            not isinstance(row["sequence"], int) or row["sequence"] < 1):
        raise SemanticError("Sequence de evento inválida")
    for key in ("simulated_ms", "scan", "counter_C0"):
        value = row[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SemanticError("Contador o tiempo lógico inválido: " + key)
    for key in ("Q0_0", "Q0_1", "Q0_2"):
        if row[key] not in (0, 1) or isinstance(row[key], bool):
            raise SemanticError("Señal digital inválida: " + key)
    for key in ("AI0", "process_value"):
        value = row[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isfinite(value)):
            raise SemanticError("Señal analógica no finita: " + key)
    if row["mode"] not in ("RUN", "STOP", "PAUSE"):
        raise SemanticError("Modo CPU inválido")
    if (not isinstance(row["scenario"], str) or
            not re.fullmatch(r"[a-zA-Z0-9_-]{1,50}", row["scenario"])):
        raise SemanticError("Escenario inválido")
    if row["process_unit"] not in ("percent", "packages", "none"):
        raise SemanticError("Unidad no admitida")
    if (not isinstance(row["received_at"], str) or
            not 1 <= len(row["received_at"]) <= 64):
        raise SemanticError("Hora de recepción inválida")
    if (not isinstance(row["active_faults"], str) or
            len(row["active_faults"]) > 256):
        raise SemanticError("Lista de fallos demasiado extensa")
    return dict(row)


def append_batch(model: dict, batch: object, session: str):
    """Return (validated new model, inserted, duplicates). No mutation on failure."""
    if not isinstance(session, str) or not SESSION_PATTERN.fullmatch(session):
        raise SemanticError("Identificador de sesión del bus inválido")
    if not isinstance(batch, list) or not 1 <= len(batch) <= MAX_BATCH:
        raise SemanticError("El lote debe contener entre 1 y 50 lecturas")

    metadata = model.get("suite_live")
    existing = model.get("tables", {}).get(TABLE)
    if existing is not None and not (
        isinstance(metadata, dict) and metadata.get("table") == TABLE
    ):
        raise SemanticError("Ya existe una tabla SuitePLC ajena al conector")

    previous_seq = metadata.get("last_sequence", 0) if (
        isinstance(metadata, dict) and metadata.get("session_id") == session) else 0
    retained = [] if existing is None else list(existing)
    added, skipped, cursor = 0, 0, previous_seq
    for raw in batch:
        row = parse_row(raw)
        seq = row["sequence"]
        if seq <= cursor:
            skipped += 1
            continue
        retained.append({"session_id": session, **row})
        cursor = seq
        added += 1
    if not added:
        return model, 0, skipped
    candidate = copy.copy(model)
    candidate["tables"] = {**model["tables"], TABLE: retained}
    candidate["suite_live"] = {
        "table": TABLE, "session_id": session,
        "last_sequence": cursor, "total_rows": len(retained)
    }
    model_validate(candidate)
    return candidate, added, skipped
