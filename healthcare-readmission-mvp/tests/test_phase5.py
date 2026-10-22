"""
Phase 5 integration tests: /operations/summary, /operations/readmission-analysis,
/management/dashboard.

Validation reference values (calculated from the loaded dataset, not hardcoded
into the application):
  Total encounters : 101,766
  HIGH             : 2,358   (~2.3%)
  MEDIUM           : 6,180   (~6.1%)
  LOW              : 93,228  (~91.6%)
  Care queue       : 8,538
  HIGH <30d rate   : ~28.6%
  MEDIUM <30d rate : ~21.6%
  LOW <30d rate    : ~10.0%
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# Tolerance for floating-point comparisons
RATE_TOLERANCE = 0.5  # percentage points


# ---------------------------------------------------------------------------
# GET /operations/summary
# ---------------------------------------------------------------------------

class TestOperationsSummary:
    def test_returns_200(self):
        assert client.get("/operations/summary").status_code == 200

    def test_required_fields_present(self):
        data = client.get("/operations/summary").json()
        for field in (
            "total_encounters", "high_risk", "medium_risk", "low_risk",
            "total_interventions", "pending_interventions",
            "completed_interventions", "by_status",
        ):
            assert field in data, f"Missing field: {field!r}"

    def test_total_encounters(self):
        data = client.get("/operations/summary").json()
        assert data["total_encounters"] == 101_766

    def test_risk_distribution(self):
        data = client.get("/operations/summary").json()
        assert data["high_risk"] == 2_358
        assert data["medium_risk"] == 6_180
        assert data["low_risk"] == 93_228

    def test_risk_levels_sum_to_total(self):
        data = client.get("/operations/summary").json()
        assert data["high_risk"] + data["medium_risk"] + data["low_risk"] == data["total_encounters"]

    def test_total_interventions_equals_care_queue(self):
        data = client.get("/operations/summary").json()
        assert data["total_interventions"] == 8_538

    def test_pending_plus_completed_equals_total_interventions(self):
        data = client.get("/operations/summary").json()
        assert (
            data["pending_interventions"] + data["completed_interventions"]
            == data["total_interventions"]
        )

    def test_by_status_sums_to_total_interventions(self):
        data = client.get("/operations/summary").json()
        assert sum(data["by_status"].values()) == data["total_interventions"]

    def test_by_status_contains_valid_statuses(self):
        data = client.get("/operations/summary").json()
        valid = {"PENDING_REVIEW", "ASSIGNED", "CONTACTED", "FOLLOW_UP_SCHEDULED", "CLOSED"}
        for status in data["by_status"]:
            assert status in valid, f"Unexpected status: {status!r}"

    def test_completed_is_closed_only(self):
        """Completed must equal the CLOSED count; all others count as pending."""
        data = client.get("/operations/summary").json()
        closed = data["by_status"].get("CLOSED", 0)
        assert data["completed_interventions"] == closed

    def test_no_negative_counts(self):
        data = client.get("/operations/summary").json()
        for key in ("total_encounters", "high_risk", "medium_risk", "low_risk",
                    "total_interventions", "pending_interventions", "completed_interventions"):
            assert data[key] >= 0, f"Negative value for {key!r}"


# ---------------------------------------------------------------------------
# GET /operations/readmission-analysis
# ---------------------------------------------------------------------------

class TestReadmissionAnalysis:
    def test_returns_200(self):
        assert client.get("/operations/readmission-analysis").status_code == 200

    def test_required_fields_present(self):
        data = client.get("/operations/readmission-analysis").json()
        assert "note" in data
        assert "by_risk_level" in data
        assert "high_to_low_readmission_ratio" in data

    def test_note_is_non_empty_string(self):
        data = client.get("/operations/readmission-analysis").json()
        assert isinstance(data["note"], str)
        assert len(data["note"]) > 0

    def test_all_three_risk_levels_present(self):
        data = client.get("/operations/readmission-analysis").json()
        levels = {row["risk_level"] for row in data["by_risk_level"]}
        assert levels == {"HIGH", "MEDIUM", "LOW"}

    def test_per_level_fields_present(self):
        data = client.get("/operations/readmission-analysis").json()
        for row in data["by_risk_level"]:
            for field in ("risk_level", "total_encounters",
                          "readmitted_under_30_days", "readmission_rate_pct"):
                assert field in row, f"Missing field {field!r} in {row}"

    def test_high_readmission_rate(self):
        data = client.get("/operations/readmission-analysis").json()
        high = next(r for r in data["by_risk_level"] if r["risk_level"] == "HIGH")
        assert abs(high["readmission_rate_pct"] - 28.58) <= RATE_TOLERANCE, (
            f"HIGH readmission rate {high['readmission_rate_pct']:.2f}% "
            f"not within {RATE_TOLERANCE}pp of 28.58%"
        )

    def test_medium_readmission_rate(self):
        data = client.get("/operations/readmission-analysis").json()
        medium = next(r for r in data["by_risk_level"] if r["risk_level"] == "MEDIUM")
        assert abs(medium["readmission_rate_pct"] - 21.60) <= RATE_TOLERANCE

    def test_low_readmission_rate(self):
        data = client.get("/operations/readmission-analysis").json()
        low = next(r for r in data["by_risk_level"] if r["risk_level"] == "LOW")
        assert abs(low["readmission_rate_pct"] - 10.03) <= RATE_TOLERANCE

    def test_high_rate_greater_than_medium_greater_than_low(self):
        """HIGH risk should have a higher historical readmission rate than LOW."""
        data = client.get("/operations/readmission-analysis").json()
        by_level = {r["risk_level"]: r["readmission_rate_pct"] for r in data["by_risk_level"]}
        assert by_level["HIGH"] > by_level["MEDIUM"] > by_level["LOW"], (
            "Risk tiers should be ordered HIGH > MEDIUM > LOW in historical readmission rate"
        )

    def test_ratio_is_positive_float(self):
        data = client.get("/operations/readmission-analysis").json()
        ratio = data["high_to_low_readmission_ratio"]
        assert ratio is not None
        assert ratio > 1.0, "HIGH-risk readmission rate should be more than 1× the LOW rate"

    def test_encounter_counts_match_summary(self):
        """Counts in readmission analysis must match /operations/summary."""
        analysis = client.get("/operations/readmission-analysis").json()
        summary = client.get("/operations/summary").json()
        by_level = {r["risk_level"]: r["total_encounters"] for r in analysis["by_risk_level"]}
        assert by_level["HIGH"] == summary["high_risk"]
        assert by_level["MEDIUM"] == summary["medium_risk"]
        assert by_level["LOW"] == summary["low_risk"]

    def test_readmitted_count_does_not_exceed_total(self):
        data = client.get("/operations/readmission-analysis").json()
        for row in data["by_risk_level"]:
            assert row["readmitted_under_30_days"] <= row["total_encounters"], (
                f"{row['risk_level']}: readmitted_under_30_days exceeds total_encounters"
            )

    def test_rate_calculated_correctly(self):
        """rate_pct must equal readmitted / total * 100 (within floating-point tolerance)."""
        data = client.get("/operations/readmission-analysis").json()
        for row in data["by_risk_level"]:
            expected = row["readmitted_under_30_days"] / row["total_encounters"] * 100
            assert abs(row["readmission_rate_pct"] - expected) < 0.01, (
                f"{row['risk_level']}: rate {row['readmission_rate_pct']} "
                f"doesn't match calculated {expected:.2f}"
            )


# ---------------------------------------------------------------------------
# GET /management/dashboard
# ---------------------------------------------------------------------------

class TestManagementDashboard:
    def test_returns_200(self):
        assert client.get("/management/dashboard").status_code == 200

    def test_required_fields_present(self):
        data = client.get("/management/dashboard").json()
        for field in (
            "total_encounters", "risk_distribution", "care_queue_size",
            "high_risk_queue_size", "medium_risk_queue_size",
            "intervention_backlog", "completed_interventions",
            "pct_selected_for_intervention", "historical_readmission_rates",
        ):
            assert field in data, f"Missing field: {field!r}"

    def test_total_encounters(self):
        data = client.get("/management/dashboard").json()
        assert data["total_encounters"] == 101_766

    def test_risk_distribution_keys(self):
        data = client.get("/management/dashboard").json()
        assert set(data["risk_distribution"].keys()) == {"HIGH", "MEDIUM", "LOW"}

    def test_risk_distribution_values(self):
        data = client.get("/management/dashboard").json()
        dist = data["risk_distribution"]
        assert dist["HIGH"] == 2_358
        assert dist["MEDIUM"] == 6_180
        assert dist["LOW"] == 93_228

    def test_care_queue_size_equals_high_plus_medium(self):
        data = client.get("/management/dashboard").json()
        assert data["care_queue_size"] == data["high_risk_queue_size"] + data["medium_risk_queue_size"]

    def test_care_queue_size(self):
        data = client.get("/management/dashboard").json()
        assert data["care_queue_size"] == 8_538

    def test_backlog_plus_completed_equals_care_queue(self):
        data = client.get("/management/dashboard").json()
        assert (
            data["intervention_backlog"] + data["completed_interventions"]
            == data["care_queue_size"]
        )

    def test_pct_selected_for_intervention(self):
        data = client.get("/management/dashboard").json()
        expected = 8_538 / 101_766 * 100
        assert abs(data["pct_selected_for_intervention"] - expected) < 0.1

    def test_historical_readmission_rates_keys(self):
        data = client.get("/management/dashboard").json()
        assert set(data["historical_readmission_rates"].keys()) == {"HIGH", "MEDIUM", "LOW"}

    def test_historical_readmission_rates_values(self):
        data = client.get("/management/dashboard").json()
        rates = data["historical_readmission_rates"]
        assert abs(rates["HIGH"] - 28.58) <= RATE_TOLERANCE
        assert abs(rates["MEDIUM"] - 21.60) <= RATE_TOLERANCE
        assert abs(rates["LOW"] - 10.03) <= RATE_TOLERANCE

    def test_consistent_with_summary(self):
        """Dashboard totals must match /operations/summary."""
        dash = client.get("/management/dashboard").json()
        summ = client.get("/operations/summary").json()
        assert dash["total_encounters"] == summ["total_encounters"]
        assert dash["care_queue_size"] == summ["total_interventions"]
        assert dash["completed_interventions"] == summ["completed_interventions"]

    def test_no_division_by_zero_with_real_data(self):
        """Verify endpoint does not error when data is present."""
        response = client.get("/management/dashboard")
        assert response.status_code == 200
        assert response.json()["pct_selected_for_intervention"] >= 0
