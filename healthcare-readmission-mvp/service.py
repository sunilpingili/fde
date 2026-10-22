"""
Business logic layer.
Risk scoring and classification live here so they are independent of
PostgreSQL, FastAPI, and the CSV format — making them unit-testable in isolation.

CRITICAL: calculate_risk_score must never receive or use `readmitted`.
          That field is the historical outcome; using it would be data leakage.
"""


def calculate_risk_score(
    number_inpatient: int,
    number_emergency: int,
    number_outpatient: int,
    time_in_hospital: int,
    num_medications: int,
) -> int:
    """Return a risk score 0-8 based on prior utilization and current admission."""
    score = 0
    if number_inpatient >= 3:
        score += 3
    if number_emergency >= 2:
        score += 2
    if number_outpatient >= 3:
        score += 1
    if time_in_hospital >= 7:
        score += 1
    if num_medications >= 20:
        score += 1
    return score


def classify_risk_level(risk_score: int) -> str:
    """Map a numeric score to a risk tier."""
    if risk_score >= 5:
        return "HIGH"
    if risk_score >= 3:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Phase 5 — Operational metrics
# ---------------------------------------------------------------------------

import repository as _repo  # local import to avoid circular dependency at module level


def get_operations_summary() -> dict:
    """
    Assemble the operations summary from two repository queries.

    Pending:   any intervention whose status is NOT 'CLOSED'.
    Completed: interventions with status == 'CLOSED'.
    """
    enc = _repo.get_encounter_counts_by_risk()
    by_status = _repo.get_intervention_counts_by_status()

    total_interventions = sum(by_status.values())
    completed = by_status.get("CLOSED", 0)
    pending = total_interventions - completed

    return {
        "total_encounters": enc["total"],
        "high_risk": enc["high_risk"],
        "medium_risk": enc["medium_risk"],
        "low_risk": enc["low_risk"],
        "total_interventions": total_interventions,
        "pending_interventions": pending,
        "completed_interventions": completed,
        "by_status": by_status,
    }


def get_readmission_analysis() -> dict:
    """
    Build the retrospective readmission analysis.

    readmitted is used ONLY here for evaluation. It was never used in risk
    scoring. The returned note makes this explicit so callers cannot
    misread the result as a clinically validated or causal finding.

    Division by zero: if a risk level has 0 encounters, rate is 0.0.
    high_to_low_readmission_ratio is None when LOW rate is 0 (undefined).
    """
    rows = _repo.get_readmission_by_risk_level()

    levels: list[dict] = []
    rates: dict[str, float] = {}
    for r in rows:
        rate = round(r["under_30"] / r["total"] * 100, 2) if r["total"] > 0 else 0.0
        rates[r["risk_level"]] = rate
        levels.append({
            "risk_level": r["risk_level"],
            "total_encounters": r["total"],
            "readmitted_under_30_days": r["under_30"],
            "readmission_rate_pct": rate,
        })

    high_rate = rates.get("HIGH", 0.0)
    low_rate = rates.get("LOW", 0.0)
    ratio = round(high_rate / low_rate, 2) if low_rate > 0 else None

    return {
        "note": (
            "readmitted is the historical outcome. It was NOT used to calculate "
            "risk_score or risk_level. This analysis evaluates whether the "
            "prioritization rule correlates with historical <30-day readmissions. "
            "It does not establish clinical validity or causal impact."
        ),
        "by_risk_level": levels,
        "high_to_low_readmission_ratio": ratio,
    }


def get_management_dashboard() -> dict:
    """
    Combine encounter counts, intervention counts, and readmission rates into
    an executive-level summary. All values are calculated from PostgreSQL.
    """
    enc = _repo.get_encounter_counts_by_risk()
    by_status = _repo.get_intervention_counts_by_status()
    readmission_rows = _repo.get_readmission_by_risk_level()

    total = enc["total"]
    total_interventions = sum(by_status.values())
    completed = by_status.get("CLOSED", 0)
    backlog = total_interventions - completed

    pct_selected = round(total_interventions / total * 100, 2) if total > 0 else 0.0

    rates: dict[str, float] = {}
    for r in readmission_rows:
        rate = round(r["under_30"] / r["total"] * 100, 2) if r["total"] > 0 else 0.0
        rates[r["risk_level"]] = rate

    return {
        "total_encounters": total,
        "risk_distribution": {
            "HIGH": enc["high_risk"],
            "MEDIUM": enc["medium_risk"],
            "LOW": enc["low_risk"],
        },
        "care_queue_size": enc["high_risk"] + enc["medium_risk"],
        "high_risk_queue_size": enc["high_risk"],
        "medium_risk_queue_size": enc["medium_risk"],
        "intervention_backlog": backlog,
        "completed_interventions": completed,
        "pct_selected_for_intervention": pct_selected,
        "historical_readmission_rates": rates,
    }


def score_encounter(enc: dict) -> tuple[int, str]:
    """
    Convenience wrapper: accepts a dict of encounter fields and returns
    (risk_score, risk_level). Raises KeyError if a required field is missing.
    `readmitted` must not be in the scoring inputs — pass it separately if
    you need it for retrospective analysis.
    """
    score = calculate_risk_score(
        number_inpatient=int(enc["number_inpatient"]),
        number_emergency=int(enc["number_emergency"]),
        number_outpatient=int(enc["number_outpatient"]),
        time_in_hospital=int(enc["time_in_hospital"]),
        num_medications=int(enc["num_medications"]),
    )
    return score, classify_risk_level(score)
