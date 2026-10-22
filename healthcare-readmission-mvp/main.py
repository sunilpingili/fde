from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

import repository as repo
import service
from database import init_db
from models import (
    CareQueueItem, EncounterOut, InterventionOut, InterventionPatch,
    ManagementDashboard, OperationsSummary, ReadmissionAnalysis,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Diabetes Readmission Intervention Queue",
    description="Enterprise care-management backend — LEARNING PROTOTYPE ONLY",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Encounters
# ---------------------------------------------------------------------------

@app.get("/encounters", response_model=list[EncounterOut], tags=["Encounters"])
def list_encounters(
    limit: Annotated[int, Query(ge=1, le=1000, description="Max rows to return")] = 100,
    offset: Annotated[int, Query(ge=0, description="Rows to skip")] = 0,
):
    """List patient encounters with pagination. Default: first 100."""
    return repo.get_encounters(limit=limit, offset=offset)


@app.get("/encounters/{encounter_id}", response_model=EncounterOut, tags=["Encounters"])
def get_encounter(encounter_id: int):
    """Return a single encounter by encounter_id."""
    enc = repo.get_encounter(encounter_id)
    if not enc:
        raise HTTPException(status_code=404, detail=f"Encounter {encounter_id} not found")
    return enc


# ---------------------------------------------------------------------------
# Care queue
# ---------------------------------------------------------------------------

@app.get("/care-queue", response_model=list[CareQueueItem], tags=["Care Queue"])
def care_queue():
    """
    Return the MEDIUM and HIGH risk encounter queue with intervention status.
    Sorted highest risk score first. Capped at 500 rows per request.
    """
    return repo.get_care_queue(["MEDIUM", "HIGH"])


@app.get("/care-queue/high", response_model=list[CareQueueItem], tags=["Care Queue"])
def care_queue_high():
    """Return only HIGH risk encounters. Sorted highest score first."""
    return repo.get_care_queue(["HIGH"])


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

@app.patch(
    "/interventions/{encounter_id}",
    response_model=InterventionOut,
    tags=["Interventions"],
)
def update_intervention(encounter_id: int, body: InterventionPatch):
    """
    Update the care-management workflow for an encounter.
    Supply one or more of: status, assigned_to, notes.
    Only MEDIUM and HIGH risk encounters have a care intervention record.
    """
    if not repo.get_encounter(encounter_id):
        raise HTTPException(
            status_code=404,
            detail=f"Encounter {encounter_id} not found",
        )

    result = repo.update_intervention(encounter_id, body.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No care intervention found for encounter {encounter_id}. "
                "Only MEDIUM and HIGH risk encounters are in the care queue."
            ),
        )
    return result


# ---------------------------------------------------------------------------
# Operations (Phase 5)
# ---------------------------------------------------------------------------

@app.get("/operations/summary", response_model=OperationsSummary, tags=["Operations"])
def operations_summary():
    """
    Encounter counts by risk level and intervention workflow status.

    Pending: any status other than CLOSED.
    Completed: CLOSED only.
    All values are calculated from PostgreSQL — not hardcoded.
    """
    return service.get_operations_summary()


@app.get(
    "/operations/readmission-analysis",
    response_model=ReadmissionAnalysis,
    tags=["Operations"],
)
def readmission_analysis():
    """
    Retrospective comparison of historical <30-day readmission rates by risk tier.

    readmitted is used ONLY here for evaluation — never in risk scoring.
    This does not establish clinical validity or that any intervention
    caused better outcomes.
    """
    return service.get_readmission_analysis()


# ---------------------------------------------------------------------------
# Management dashboard (Phase 5)
# ---------------------------------------------------------------------------

@app.get(
    "/management/dashboard",
    response_model=ManagementDashboard,
    tags=["Management"],
)
def management_dashboard():
    """
    Executive summary: encounter volumes, risk distribution, care queue,
    intervention backlog, and historical readmission rates.
    All values calculated from PostgreSQL.
    """
    return service.get_management_dashboard()
