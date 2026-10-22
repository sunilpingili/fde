"""
Pytest fixtures shared across all endpoint and integration tests.

Why DB-derived fixtures for encounter IDs?
The care-queue endpoints return at most 500 rows sorted by risk_score DESC.
A hardcoded encounter_id like 5654628 (score=5, rank=708) falls outside
that window.  These fixtures always query the first row of the sorted queue,
so they are guaranteed to appear in page 1 regardless of score distribution.

Test isolation — no separate test database:
Loading 101,766 rows into a throwaway database for each test run is slow and
fragile. Instead, `restore_intervention` captures the DB state before each
PATCH test and restores it in teardown, leaving the shared database unchanged.
"""

import pytest
from database import get_connection


@pytest.fixture(scope="session")
def high_encounter_id() -> int:
    """
    The encounter_id of the first HIGH-risk encounter in the care queue.
    Uses the same ORDER BY as the /care-queue/high endpoint so it is
    always within the LIMIT 500 window.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pe.encounter_id
                FROM   patient_encounters pe
                JOIN   care_interventions ci ON pe.encounter_id = ci.encounter_id
                WHERE  pe.risk_level = 'HIGH'
                ORDER  BY pe.risk_score DESC, pe.encounter_id
                LIMIT  1
            """)
            row = cur.fetchone()
    assert row is not None, (
        "No HIGH risk encounters found in the database. "
        "Run data_loader.py before running the test suite."
    )
    return row[0]


@pytest.fixture(scope="session")
def medium_encounter_id() -> int:
    """
    The encounter_id of the first MEDIUM-risk encounter in the care queue.
    Same guarantee as high_encounter_id — within the LIMIT 500 window.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pe.encounter_id
                FROM   patient_encounters pe
                JOIN   care_interventions ci ON pe.encounter_id = ci.encounter_id
                WHERE  pe.risk_level = 'MEDIUM'
                ORDER  BY pe.risk_score DESC, pe.encounter_id
                LIMIT  1
            """)
            row = cur.fetchone()
    assert row is not None, (
        "No MEDIUM risk encounters found in the database. "
        "Run data_loader.py before running the test suite."
    )
    return row[0]


@pytest.fixture()
def restore_intervention():
    """
    Save an intervention's current state before a test modifies it,
    then restore it in teardown so the shared database is left unchanged.

    Usage inside a test method:
        def test_something(self, restore_intervention, high_encounter_id):
            restore_intervention(high_encounter_id)   # <-- call BEFORE patching
            client.patch(...)
    """
    saved: dict[int, dict] = {}

    def save(encounter_id: int) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status, assigned_to, notes "
                    "FROM care_interventions WHERE encounter_id = %s",
                    (encounter_id,),
                )
                row = cur.fetchone()
        if row:
            saved[encounter_id] = {
                "status": row[0],
                "assigned_to": row[1],
                "notes": row[2],
            }

    yield save

    if not saved:
        return
    with get_connection() as conn:
        with conn.cursor() as cur:
            for enc_id, state in saved.items():
                cur.execute(
                    """UPDATE care_interventions
                          SET status      = %s,
                              assigned_to = %s,
                              notes       = %s,
                              updated_at  = NOW()
                        WHERE encounter_id = %s""",
                    (state["status"], state["assigned_to"], state["notes"], enc_id),
                )
        conn.commit()
