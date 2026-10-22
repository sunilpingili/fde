"""
data_loader.py — Load diabetic_data.csv into PostgreSQL.

Idempotent: safe to run multiple times.
- patient_encounters: ON CONFLICT (encounter_id) DO NOTHING
- care_interventions:  ON CONFLICT (encounter_id) DO NOTHING
  (preserves any status/owner/notes already set by the care team)

Run from inside the healthcare-readmission-mvp directory:
    python3 data_loader.py
"""

import csv
import sys
from pathlib import Path

from database import get_connection, init_db
from service import calculate_risk_score, classify_risk_level

DATA_FILE = Path(__file__).parent / "data" / "diabetic_data.csv"
BATCH_SIZE = 2000

REQUIRED_COLUMNS = {
    "encounter_id", "patient_nbr", "age", "time_in_hospital",
    "number_inpatient", "number_emergency", "number_outpatient",
    "num_medications", "num_lab_procedures",
    "discharge_disposition_id", "admission_type_id", "readmitted",
}


def _read_csv() -> tuple[list[tuple], list[tuple]]:
    """
    Parse the CSV and return two lists of tuples ready for executemany:
      encounter_rows  — for patient_encounters
      intervention_ids — for care_interventions (MEDIUM + HIGH only)
    """
    if not DATA_FILE.exists():
        sys.exit(f"Dataset not found: {DATA_FILE}")

    encounter_rows: list[tuple] = []
    intervention_ids: list[tuple] = []

    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"CSV is missing required columns: {missing}")

        for row in reader:
            score = calculate_risk_score(
                number_inpatient=int(row["number_inpatient"]),
                number_emergency=int(row["number_emergency"]),
                number_outpatient=int(row["number_outpatient"]),
                time_in_hospital=int(row["time_in_hospital"]),
                num_medications=int(row["num_medications"]),
            )
            level = classify_risk_level(score)

            encounter_rows.append((
                int(row["encounter_id"]),
                int(row["patient_nbr"]),
                row["age"],
                int(row["time_in_hospital"]),
                int(row["number_inpatient"]),
                int(row["number_emergency"]),
                int(row["number_outpatient"]),
                int(row["num_medications"]),
                int(row["num_lab_procedures"]),
                int(row["discharge_disposition_id"]),
                int(row["admission_type_id"]),
                row["readmitted"],   # stored for retrospective analysis only
                score,
                level,
            ))

            if level in ("MEDIUM", "HIGH"):
                intervention_ids.append((int(row["encounter_id"]),))

    return encounter_rows, intervention_ids


def _insert_batches(cur, sql: str, rows: list[tuple], batch_size: int = BATCH_SIZE):
    """Execute parameterized INSERT in chunks to avoid sending 100k rows at once."""
    for i in range(0, len(rows), batch_size):
        cur.executemany(sql, rows[i : i + batch_size])


def load():
    print("Reading CSV …")
    encounter_rows, intervention_ids = _read_csv()
    print(f"  {len(encounter_rows):,} encounters parsed from CSV")
    print(f"  {len(intervention_ids):,} MEDIUM/HIGH encounters will enter the care queue")

    print("Ensuring schema exists …")
    init_db()

    enc_sql = """
        INSERT INTO patient_encounters (
            encounter_id, patient_nbr, age, time_in_hospital,
            number_inpatient, number_emergency, number_outpatient,
            num_medications, num_lab_procedures,
            discharge_disposition_id, admission_type_id,
            readmitted, risk_score, risk_level
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (encounter_id) DO NOTHING
    """

    inv_sql = """
        INSERT INTO care_interventions (encounter_id)
        VALUES (%s)
        ON CONFLICT (encounter_id) DO NOTHING
    """

    print("Loading encounters into PostgreSQL …")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _insert_batches(cur, enc_sql, encounter_rows)
            _insert_batches(cur, inv_sql, intervention_ids)
        conn.commit()

    print("Load complete. Querying summary …\n")
    _print_summary()


def _print_summary():
    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COUNT(*) FROM patient_encounters")
            total = cur.fetchone()[0]

            cur.execute(
                "SELECT risk_level, COUNT(*) FROM patient_encounters GROUP BY risk_level ORDER BY risk_level"
            )
            level_counts = {row[0]: row[1] for row in cur.fetchall()}

            cur.execute("SELECT COUNT(*) FROM care_interventions")
            queue_total = cur.fetchone()[0]

            cur.execute(
                "SELECT status, COUNT(*) FROM care_interventions GROUP BY status ORDER BY status"
            )
            status_counts = {row[0]: row[1] for row in cur.fetchall()}

            # Retrospective readmission rate by risk level
            # `readmitted` is ONLY used here — NEVER in scoring
            cur.execute("""
                SELECT
                    risk_level,
                    COUNT(*) AS total,
                    SUM(CASE WHEN readmitted = '<30' THEN 1 ELSE 0 END) AS under_30
                FROM patient_encounters
                GROUP BY risk_level
                ORDER BY risk_level
            """)
            readmission_rows = cur.fetchall()

    print("=" * 52)
    print("LOAD SUMMARY")
    print("=" * 52)
    print(f"{'Total encounters loaded:':<35} {total:>7,}")
    print()
    print("Risk distribution:")
    for level in ("HIGH", "MEDIUM", "LOW"):
        n = level_counts.get(level, 0)
        pct = n / total * 100 if total else 0
        print(f"  {level:<8}  {n:>7,}  ({pct:.1f}%)")
    print()
    print(f"{'Care queue size (MEDIUM + HIGH):':<35} {queue_total:>7,}")
    print("Intervention statuses:")
    for status, count in status_counts.items():
        print(f"  {status:<25} {count:>7,}")
    print()
    print("Historical readmission rates by risk level (retrospective — NOT used in scoring):")
    for risk_level, total_n, under30 in readmission_rows:
        rate = under30 / total_n * 100 if total_n else 0
        print(f"  {risk_level:<8}  {total_n:>7,} encounters  {under30:>5,} readmitted <30d  ({rate:.1f}%)")
    print("=" * 52)


if __name__ == "__main__":
    load()
