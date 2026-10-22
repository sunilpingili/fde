"""
repository.py — All SQL lives here. No business logic.

Rules:
- Every query uses parameterized placeholders (%s). No user-supplied value
  is ever concatenated into an SQL string.
- Column names that appear in SET clauses come from a hardcoded `_ALLOWED`
  set defined in this file, never from user input.
- `readmitted` is never exposed through the encounter query — it belongs
  only in the retrospective analysis query (Phase 5 repository function).
"""

from database import get_connection

# Only these columns may appear in an UPDATE SET clause.
# They come from our code, not from user input, so dynamic f-string
# construction here is safe.
_INTERVENTION_UPDATABLE = {"status", "assigned_to", "notes"}


def _row_to_dict(cur, row: tuple) -> dict:
    cols = [d.name for d in cur.description]
    return dict(zip(cols, row))


# ---------------------------------------------------------------------------
# Encounters
# ---------------------------------------------------------------------------

def get_encounters(limit: int = 100, offset: int = 0) -> list[dict]:
    sql = """
        SELECT encounter_id, patient_nbr, age, time_in_hospital,
               number_inpatient, number_emergency, number_outpatient,
               num_medications, num_lab_procedures,
               discharge_disposition_id, admission_type_id,
               risk_score, risk_level
        FROM   patient_encounters
        ORDER  BY encounter_id
        LIMIT  %s OFFSET %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit, offset))
            rows = cur.fetchall()
            return [_row_to_dict(cur, r) for r in rows]


def get_encounter(encounter_id: int) -> dict | None:
    sql = """
        SELECT encounter_id, patient_nbr, age, time_in_hospital,
               number_inpatient, number_emergency, number_outpatient,
               num_medications, num_lab_procedures,
               discharge_disposition_id, admission_type_id,
               risk_score, risk_level
        FROM   patient_encounters
        WHERE  encounter_id = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(cur, row)


# ---------------------------------------------------------------------------
# Care queue
# ---------------------------------------------------------------------------

def get_care_queue(risk_levels: list[str]) -> list[dict]:
    """
    Return encounters joined with their intervention row, filtered by risk level.
    Sorted highest risk first (score DESC), then by encounter_id for stability.
    risk_levels values come from our own code, not from user input.
    """
    placeholders = ", ".join(["%s"] * len(risk_levels))
    sql = f"""
        SELECT
            pe.encounter_id, pe.patient_nbr, pe.age,
            pe.time_in_hospital, pe.number_inpatient, pe.number_emergency,
            pe.number_outpatient, pe.num_medications,
            pe.risk_score, pe.risk_level,
            ci.intervention_id, ci.status, ci.assigned_to, ci.notes,
            ci.created_at, ci.updated_at
        FROM   patient_encounters pe
        JOIN   care_interventions ci ON pe.encounter_id = ci.encounter_id
        WHERE  pe.risk_level IN ({placeholders})
        ORDER  BY pe.risk_score DESC, pe.encounter_id
        LIMIT  500
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, risk_levels)
            rows = cur.fetchall()
            return [_row_to_dict(cur, r) for r in rows]


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

def get_intervention(encounter_id: int) -> dict | None:
    sql = """
        SELECT intervention_id, encounter_id, status,
               assigned_to, notes, created_at, updated_at
        FROM   care_interventions
        WHERE  encounter_id = %s
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (encounter_id,))
            row = cur.fetchone()
            if not row:
                return None
            return _row_to_dict(cur, row)


# ---------------------------------------------------------------------------
# Phase 5 — Metrics queries
# readmitted is used ONLY in get_readmission_by_risk_level for retrospective
# analysis. It must never appear in any scoring or queue-building query.
# ---------------------------------------------------------------------------

def get_encounter_counts_by_risk() -> dict:
    """Return total encounter count and per-risk-level counts."""
    sql = """
        SELECT
            COUNT(*)                                                    AS total,
            SUM(CASE WHEN risk_level = 'HIGH'   THEN 1 ELSE 0 END)    AS high_risk,
            SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END)    AS medium_risk,
            SUM(CASE WHEN risk_level = 'LOW'    THEN 1 ELSE 0 END)    AS low_risk
        FROM patient_encounters
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    return {
        "total": int(row[0]),
        "high_risk": int(row[1]),
        "medium_risk": int(row[2]),
        "low_risk": int(row[3]),
    }


def get_intervention_counts_by_status() -> dict:
    """Return total intervention count and a breakdown by status."""
    sql = """
        SELECT status, COUNT(*) AS cnt
        FROM   care_interventions
        GROUP  BY status
        ORDER  BY status
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return {row[0]: int(row[1]) for row in rows}


def get_readmission_by_risk_level() -> list[dict]:
    """
    Return historical <30-day readmission counts grouped by risk_level.
    `readmitted` is used ONLY here — never in scoring queries.
    """
    sql = """
        SELECT
            risk_level,
            COUNT(*)                                                     AS total,
            SUM(CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END)        AS under_30
        FROM   patient_encounters
        GROUP  BY risk_level
        ORDER  BY risk_level
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
    return [
        {"risk_level": r[0], "total": int(r[1]), "under_30": int(r[2])}
        for r in rows
    ]


def update_intervention(encounter_id: int, fields: dict) -> dict | None:
    """
    Partial update of a care_interventions row.
    `fields` must only contain keys from _INTERVENTION_UPDATABLE; anything
    else is silently ignored. updated_at is always refreshed.
    Column names in the SET clause come from _INTERVENTION_UPDATABLE (hardcoded),
    never from user input — so dynamic f-string construction here is safe.
    Returns the updated row, or None if encounter_id has no intervention.
    """
    updates = {
        k: v for k, v in fields.items()
        if k in _INTERVENTION_UPDATABLE and v is not None
    }
    if not updates:
        return get_intervention(encounter_id)

    set_clause = ", ".join(f"{col} = %s" for col in updates) + ", updated_at = NOW()"
    values = list(updates.values()) + [encounter_id]

    sql = f"""
        UPDATE care_interventions
        SET    {set_clause}
        WHERE  encounter_id = %s
        RETURNING intervention_id, encounter_id, status,
                  assigned_to, notes, created_at, updated_at
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, values)
            row = cur.fetchone()
            if not row:
                return None
            result = _row_to_dict(cur, row)
        conn.commit()
    return result
