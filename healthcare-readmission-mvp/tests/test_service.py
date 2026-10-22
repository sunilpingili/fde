"""
Unit tests for the risk-scoring functions in service.py.

Key constraint: calculate_risk_score must NOT accept or use `readmitted`.
These tests confirm the scoring logic in isolation — no database, no CSV.
"""

import inspect
import pytest
from service import calculate_risk_score, classify_risk_level, score_encounter


# ---------------------------------------------------------------------------
# Verify `readmitted` is not a parameter of the scoring function
# ---------------------------------------------------------------------------

def test_readmitted_not_a_scoring_parameter():
    """The scoring function must never accept `readmitted` — data leakage guard."""
    params = inspect.signature(calculate_risk_score).parameters
    assert "readmitted" not in params, (
        "calculate_risk_score must not accept `readmitted` — "
        "it is the historical outcome and must not influence the score."
    )


# ---------------------------------------------------------------------------
# calculate_risk_score — boundary conditions
# ---------------------------------------------------------------------------

def test_all_inputs_zero():
    assert calculate_risk_score(0, 0, 0, 0, 0) == 0


def test_max_possible_score():
    # number_inpatient=3 (+3), number_emergency=2 (+2), number_outpatient=3 (+1),
    # time_in_hospital=7 (+1), num_medications=20 (+1)  → total 8
    assert calculate_risk_score(3, 2, 3, 7, 20) == 8


# --- number_inpatient thresholds (+3) ---

def test_inpatient_below_threshold():
    assert calculate_risk_score(2, 0, 0, 0, 0) == 0

def test_inpatient_at_threshold():
    assert calculate_risk_score(3, 0, 0, 0, 0) == 3

def test_inpatient_above_threshold():
    assert calculate_risk_score(10, 0, 0, 0, 0) == 3


# --- number_emergency thresholds (+2) ---

def test_emergency_below_threshold():
    assert calculate_risk_score(0, 1, 0, 0, 0) == 0

def test_emergency_at_threshold():
    assert calculate_risk_score(0, 2, 0, 0, 0) == 2

def test_emergency_above_threshold():
    assert calculate_risk_score(0, 5, 0, 0, 0) == 2


# --- number_outpatient thresholds (+1) ---

def test_outpatient_below_threshold():
    assert calculate_risk_score(0, 0, 2, 0, 0) == 0

def test_outpatient_at_threshold():
    assert calculate_risk_score(0, 0, 3, 0, 0) == 1

def test_outpatient_above_threshold():
    assert calculate_risk_score(0, 0, 9, 0, 0) == 1


# --- time_in_hospital thresholds (+1) ---

def test_time_in_hospital_below_threshold():
    assert calculate_risk_score(0, 0, 0, 6, 0) == 0

def test_time_in_hospital_at_threshold():
    assert calculate_risk_score(0, 0, 0, 7, 0) == 1

def test_time_in_hospital_above_threshold():
    assert calculate_risk_score(0, 0, 0, 14, 0) == 1


# --- num_medications thresholds (+1) ---

def test_medications_below_threshold():
    assert calculate_risk_score(0, 0, 0, 0, 19) == 0

def test_medications_at_threshold():
    assert calculate_risk_score(0, 0, 0, 0, 20) == 1

def test_medications_above_threshold():
    assert calculate_risk_score(0, 0, 0, 0, 40) == 1


# --- Additive scoring ---

def test_two_conditions_combine():
    # inpatient=3 (+3) + emergency=2 (+2) = 5
    assert calculate_risk_score(3, 2, 0, 0, 0) == 5

def test_four_conditions_combine():
    # inpatient=3 (+3) + time=7 (+1) + meds=20 (+1) + outpatient=3 (+1) = 6
    assert calculate_risk_score(3, 0, 3, 7, 20) == 6


# ---------------------------------------------------------------------------
# classify_risk_level — tier boundaries
# ---------------------------------------------------------------------------

def test_level_low_at_zero():
    assert classify_risk_level(0) == "LOW"

def test_level_low_at_2():
    assert classify_risk_level(2) == "LOW"

def test_level_medium_at_3():
    assert classify_risk_level(3) == "MEDIUM"

def test_level_medium_at_4():
    assert classify_risk_level(4) == "MEDIUM"

def test_level_high_at_5():
    assert classify_risk_level(5) == "HIGH"

def test_level_high_at_8():
    assert classify_risk_level(8) == "HIGH"


# ---------------------------------------------------------------------------
# score_encounter — convenience wrapper
# ---------------------------------------------------------------------------

def test_score_encounter_low():
    enc = {
        "number_inpatient": "0",
        "number_emergency": "0",
        "number_outpatient": "0",
        "time_in_hospital": "1",
        "num_medications": "1",
    }
    score, level = score_encounter(enc)
    assert score == 0
    assert level == "LOW"


def test_score_encounter_medium():
    enc = {
        "number_inpatient": "3",
        "number_emergency": "0",
        "number_outpatient": "0",
        "time_in_hospital": "6",
        "num_medications": "19",
    }
    score, level = score_encounter(enc)
    assert score == 3
    assert level == "MEDIUM"


def test_score_encounter_high():
    enc = {
        "number_inpatient": "3",
        "number_emergency": "2",
        "number_outpatient": "0",
        "time_in_hospital": "6",
        "num_medications": "19",
    }
    score, level = score_encounter(enc)
    assert score == 5
    assert level == "HIGH"


def test_score_encounter_does_not_accept_readmitted():
    """score_encounter must work without readmitted being present."""
    enc = {
        "number_inpatient": "3",
        "number_emergency": "0",
        "number_outpatient": "0",
        "time_in_hospital": "7",
        "num_medications": "20",
    }
    # Must not raise even though `readmitted` is absent
    score, level = score_encounter(enc)
    assert score == 5
    assert level == "HIGH"


def test_score_encounter_real_high_example():
    """Matches encounter 5654628 from the dataset analysis."""
    enc = {
        "number_inpatient": "5",
        "number_emergency": "0",
        "number_outpatient": "9",
        "time_in_hospital": "6",
        "num_medications": "27",
    }
    score, level = score_encounter(enc)
    assert score == 5   # inpatient +3, outpatient +1, meds +1
    assert level == "HIGH"
