"""
Integration tests for Phase 4 FastAPI endpoints.
Requires healthcare_readmission_db to be running and populated (run data_loader.py first).

Encounter IDs used for care-queue and PATCH tests come from DB fixtures in conftest.py,
not hardcoded constants, because the care-queue endpoints apply LIMIT 500 and a specific
ORDER BY. Hardcoding encounter 5654628 (risk_score=5, rank=708 in HIGH queue) caused two
test failures in Phase 4 — it sits outside the LIMIT 500 window.

Hardcoded constants are only used for encounters that do NOT depend on the care-queue
pagination window:
  LOW_ENCOUNTER_ID    — tests that a LOW-risk encounter has no intervention (any low-risk ID works)
  MISSING_ENCOUNTER_ID — tests 404 responses (must not exist in the DB)
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

LOW_ENCOUNTER_ID = 2278392       # score 0, LOW risk — confirmed in Phase 1 dataset analysis
MISSING_ENCOUNTER_ID = 9999999   # not present in diabetic_data.csv


# ---------------------------------------------------------------------------
# GET /encounters
# ---------------------------------------------------------------------------

class TestListEncounters:
    def test_returns_200(self):
        assert client.get("/encounters").status_code == 200

    def test_returns_list(self):
        data = client.get("/encounters").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_default_limit_100(self):
        assert len(client.get("/encounters").json()) <= 100

    def test_custom_limit(self):
        response = client.get("/encounters?limit=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_offset_pagination(self):
        page1 = client.get("/encounters?limit=10&offset=0").json()
        page2 = client.get("/encounters?limit=10&offset=10").json()
        assert {r["encounter_id"] for r in page1}.isdisjoint(
            {r["encounter_id"] for r in page2}
        ), "Paginated pages must not overlap"

    def test_readmitted_not_in_response(self):
        row = client.get("/encounters?limit=1").json()[0]
        assert "readmitted" not in row, (
            "readmitted is the historical outcome and must never appear in encounter responses"
        )

    def test_required_fields_present(self):
        row = client.get("/encounters?limit=1").json()[0]
        for field in ("encounter_id", "patient_nbr", "age", "risk_score", "risk_level"):
            assert field in row

    def test_invalid_limit_returns_422(self):
        assert client.get("/encounters?limit=0").status_code == 422
        assert client.get("/encounters?limit=1001").status_code == 422


# ---------------------------------------------------------------------------
# GET /encounters/{encounter_id}
# ---------------------------------------------------------------------------

class TestGetEncounter:
    def test_known_high_risk_encounter(self, high_encounter_id):
        response = client.get(f"/encounters/{high_encounter_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["encounter_id"] == high_encounter_id
        assert data["risk_level"] == "HIGH"
        assert data["risk_score"] >= 5

    def test_known_low_risk_encounter(self):
        response = client.get(f"/encounters/{LOW_ENCOUNTER_ID}")
        assert response.status_code == 200
        assert response.json()["risk_level"] == "LOW"

    def test_missing_encounter_returns_404(self):
        response = client.get(f"/encounters/{MISSING_ENCOUNTER_ID}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_readmitted_not_in_response(self, high_encounter_id):
        row = client.get(f"/encounters/{high_encounter_id}").json()
        assert "readmitted" not in row


# ---------------------------------------------------------------------------
# GET /care-queue
# ---------------------------------------------------------------------------

class TestCareQueue:
    def test_returns_200(self):
        assert client.get("/care-queue").status_code == 200

    def test_returns_list(self):
        data = client.get("/care-queue").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_only_medium_and_high(self):
        data = client.get("/care-queue").json()
        levels = {row["risk_level"] for row in data}
        assert levels.issubset({"MEDIUM", "HIGH"}), (
            f"care-queue must only contain MEDIUM and HIGH, got: {levels}"
        )

    def test_low_risk_not_in_queue(self):
        data = client.get("/care-queue").json()
        ids = {row["encounter_id"] for row in data}
        assert LOW_ENCOUNTER_ID not in ids, "LOW risk encounters must not appear in the care queue"

    def test_intervention_fields_present(self):
        row = client.get("/care-queue").json()[0]
        for field in ("intervention_id", "status", "created_at", "updated_at"):
            assert field in row, f"Expected field {field!r} in care-queue response"

    def test_sorted_highest_risk_first(self):
        data = client.get("/care-queue").json()
        scores = [row["risk_score"] for row in data]
        assert scores == sorted(scores, reverse=True), "care-queue must be sorted by risk_score DESC"


# ---------------------------------------------------------------------------
# GET /care-queue/high
# ---------------------------------------------------------------------------

class TestCareQueueHigh:
    def test_returns_200(self):
        assert client.get("/care-queue/high").status_code == 200

    def test_only_high_risk(self):
        data = client.get("/care-queue/high").json()
        levels = {row["risk_level"] for row in data}
        assert levels == {"HIGH"}, f"care-queue/high must only contain HIGH, got: {levels}"

    def test_known_high_encounter_present(self, high_encounter_id):
        """
        Verify the first HIGH encounter in the sorted queue appears in the response.
        Uses DB fixture (not hardcoded ID) because the endpoint applies LIMIT 500
        ordered by risk_score DESC — encounters beyond rank 500 would not appear.
        """
        data = client.get("/care-queue/high").json()
        ids = {row["encounter_id"] for row in data}
        assert high_encounter_id in ids, (
            f"Encounter {high_encounter_id} (rank 1 in HIGH queue) must appear in /care-queue/high"
        )

    def test_medium_not_in_high_queue(self, medium_encounter_id):
        data = client.get("/care-queue/high").json()
        ids = {row["encounter_id"] for row in data}
        assert medium_encounter_id not in ids, (
            "MEDIUM risk encounters must not appear in /care-queue/high"
        )


# ---------------------------------------------------------------------------
# PATCH /interventions/{encounter_id}
# ---------------------------------------------------------------------------

class TestUpdateIntervention:
    def test_update_status(self, high_encounter_id, restore_intervention):
        restore_intervention(high_encounter_id)
        response = client.patch(
            f"/interventions/{high_encounter_id}",
            json={"status": "ASSIGNED"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ASSIGNED"
        assert data["encounter_id"] == high_encounter_id

    def test_update_assigned_to(self, medium_encounter_id, restore_intervention):
        restore_intervention(medium_encounter_id)
        response = client.patch(
            f"/interventions/{medium_encounter_id}",
            json={"assigned_to": "Care Team A"},
        )
        assert response.status_code == 200
        assert response.json()["assigned_to"] == "Care Team A"

    def test_update_notes(self, high_encounter_id, restore_intervention):
        restore_intervention(high_encounter_id)
        response = client.patch(
            f"/interventions/{high_encounter_id}",
            json={"notes": "Follow-up call scheduled for Monday"},
        )
        assert response.status_code == 200
        assert response.json()["notes"] == "Follow-up call scheduled for Monday"

    def test_update_all_fields(self, medium_encounter_id, restore_intervention):
        restore_intervention(medium_encounter_id)
        response = client.patch(
            f"/interventions/{medium_encounter_id}",
            json={
                "status": "CONTACTED",
                "assigned_to": "Care Team B",
                "notes": "Patient answered, appointment booked",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CONTACTED"
        assert data["assigned_to"] == "Care Team B"
        assert data["notes"] == "Patient answered, appointment booked"

    def test_update_persists(self, high_encounter_id, restore_intervention):
        """
        Verify a PATCH survives a subsequent read from the database.
        Uses a DB-fixture encounter (rank 1 in HIGH queue) so it appears
        in the LIMIT 500 care-queue response used to re-fetch the row.
        restore_intervention rolls back the change after the test.
        """
        restore_intervention(high_encounter_id)

        patch_resp = client.patch(
            f"/interventions/{high_encounter_id}",
            json={"status": "FOLLOW_UP_SCHEDULED", "assigned_to": "Dr. Patel"},
        )
        assert patch_resp.status_code == 200, (
            f"PATCH failed: {patch_resp.status_code} {patch_resp.json()}"
        )

        queue = client.get("/care-queue/high").json()
        row = next((r for r in queue if r["encounter_id"] == high_encounter_id), None)
        assert row is not None, (
            f"Encounter {high_encounter_id} not found in /care-queue/high after PATCH. "
            "Check that this fixture ID is within the LIMIT 500 window."
        )
        assert row["status"] == "FOLLOW_UP_SCHEDULED"
        assert row["assigned_to"] == "Dr. Patel"

    def test_invalid_status_returns_422(self, high_encounter_id):
        response = client.patch(
            f"/interventions/{high_encounter_id}",
            json={"status": "INVALID_STATUS"},
        )
        assert response.status_code == 422

    def test_empty_body_returns_422(self, high_encounter_id):
        response = client.patch(f"/interventions/{high_encounter_id}", json={})
        assert response.status_code == 422

    def test_missing_encounter_returns_404(self):
        response = client.patch(
            f"/interventions/{MISSING_ENCOUNTER_ID}",
            json={"status": "ASSIGNED"},
        )
        assert response.status_code == 404

    def test_low_risk_encounter_returns_404(self):
        """LOW risk encounters have no intervention row — must return 404."""
        response = client.patch(
            f"/interventions/{LOW_ENCOUNTER_ID}",
            json={"status": "ASSIGNED"},
        )
        assert response.status_code == 404
        assert "care intervention" in response.json()["detail"].lower()

    def test_all_valid_statuses_accepted(self, medium_encounter_id, restore_intervention):
        restore_intervention(medium_encounter_id)
        valid_statuses = [
            "PENDING_REVIEW", "ASSIGNED", "CONTACTED",
            "FOLLOW_UP_SCHEDULED", "CLOSED",
        ]
        for status in valid_statuses:
            response = client.patch(
                f"/interventions/{medium_encounter_id}",
                json={"status": status},
            )
            assert response.status_code == 200, (
                f"Status {status!r} should be valid, got {response.status_code}: {response.json()}"
            )
