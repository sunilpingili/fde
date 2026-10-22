from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator


class InterventionStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    ASSIGNED = "ASSIGNED"
    CONTACTED = "CONTACTED"
    FOLLOW_UP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    CLOSED = "CLOSED"


# ---------------------------------------------------------------------------
# Encounter responses
# readmitted is intentionally excluded — it is the historical outcome and
# must not appear in operational API responses. It is used only in the
# retrospective readmission analysis endpoint (Phase 5).
# ---------------------------------------------------------------------------

class EncounterOut(BaseModel):
    encounter_id: int
    patient_nbr: int
    age: str
    time_in_hospital: int
    number_inpatient: int
    number_emergency: int
    number_outpatient: int
    num_medications: int
    num_lab_procedures: int
    discharge_disposition_id: int
    admission_type_id: int
    risk_score: int
    risk_level: str


# ---------------------------------------------------------------------------
# Care queue — encounter fields joined with intervention state
# ---------------------------------------------------------------------------

class CareQueueItem(BaseModel):
    encounter_id: int
    patient_nbr: int
    age: str
    time_in_hospital: int
    number_inpatient: int
    number_emergency: int
    number_outpatient: int
    num_medications: int
    risk_score: int
    risk_level: str
    intervention_id: int
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Intervention update — PATCH request body
# ---------------------------------------------------------------------------

class InterventionPatch(BaseModel):
    status: Optional[InterventionStatus] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "InterventionPatch":
        if self.status is None and self.assigned_to is None and self.notes is None:
            raise ValueError("At least one of status, assigned_to, or notes must be provided.")
        return self


# ---------------------------------------------------------------------------
# Intervention response
# ---------------------------------------------------------------------------

class InterventionOut(BaseModel):
    intervention_id: int
    encounter_id: int
    status: str
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Phase 5 — Operational metrics and management dashboard
# ---------------------------------------------------------------------------

class OperationsSummary(BaseModel):
    """
    Calculated from patient_encounters and care_interventions in PostgreSQL.

    Pending definition: any intervention not yet CLOSED.
    Completed definition: status == CLOSED.
    """
    total_encounters: int
    high_risk: int
    medium_risk: int
    low_risk: int
    total_interventions: int
    pending_interventions: int
    completed_interventions: int
    by_status: dict[str, int]


class RiskLevelReadmission(BaseModel):
    risk_level: str
    total_encounters: int
    readmitted_under_30_days: int
    readmission_rate_pct: float


class ReadmissionAnalysis(BaseModel):
    """
    Retrospective comparison of historical <30-day readmission rates by risk tier.

    IMPORTANT: `readmitted` is used ONLY here for evaluation. It was never used
    to compute risk_score or risk_level. This analysis measures whether the
    prioritization rule correlates with historical outcomes — it does NOT claim
    clinical validity or that any intervention caused a change in outcomes.
    """
    note: str
    by_risk_level: list[RiskLevelReadmission]
    high_to_low_readmission_ratio: Optional[float] = None


class ManagementDashboard(BaseModel):
    """Executive-level summary calculated from PostgreSQL."""
    total_encounters: int
    risk_distribution: dict[str, int]
    care_queue_size: int
    high_risk_queue_size: int
    medium_risk_queue_size: int
    intervention_backlog: int
    completed_interventions: int
    pct_selected_for_intervention: float
    historical_readmission_rates: dict[str, float]
