# Demo Script — 3–5 Minute Video

Diabetes Readmission Intervention Queue · Testleaf FDE Week 2

---

## Before Recording

Ensure the following are ready:
- PostgreSQL is running (`pg_isready -h localhost -p 5432`)
- API is started: `uvicorn main:app --reload --port 8004`
- Swagger UI is open: `http://localhost:8004/docs`
- pgAdmin or a terminal with psql is open
- Browser zoom level is large enough to read on video

---

## Segment 1 — Business Problem (30 seconds)

**What to say:**

> "A hospital has 101,766 historical diabetes encounters and is worried about 30-day readmissions. The care-management team can't review every discharged patient. My application answers one question: which patients should the team review first?"

> "I'm acting as the FDE — my job isn't to build a model. It's to build the workflow around the problem: ingest data, apply an explainable rule, persist it in PostgreSQL, and expose it through FastAPI."

---

## Segment 2 — Architecture (30 seconds)

**What to show:**  
Open VS Code or terminal and show the project file tree briefly.

**What to say:**

> "The application follows a strict layering pattern. `data_loader.py` reads the CSV and loads PostgreSQL. `repository.py` holds all SQL. `service.py` has the risk-scoring logic with no database dependency. `main.py` exposes FastAPI endpoints. `models.py` defines the Pydantic types."

> "Critical design rule: the `readmitted` field — the historical outcome — is never used to calculate the risk score. It is only used after scoring to evaluate whether the rule works."

---

## Segment 3 — Database and Loaded Data (45 seconds)

**What to show:**  
Run in terminal or show pgAdmin:
```sql
SELECT risk_level, COUNT(*) FROM patient_encounters GROUP BY risk_level ORDER BY risk_level;
SELECT COUNT(*) FROM care_interventions;
```

**What to say:**

> "I loaded 101,766 encounters from the UCI diabetes dataset. The risk scoring rule assigned 2,358 as HIGH risk, 6,180 as MEDIUM, and 93,228 as LOW."

> "For every MEDIUM and HIGH encounter, the loader automatically created a care_interventions row with status PENDING_REVIEW. That's 8,538 encounters entering the queue — about 8.4% of all discharges."

> "The loader is idempotent: running it again won't duplicate data or reset any statuses the care team has already updated."

---

## Segment 4 — Risk Scoring and Care Queue (45 seconds)

**What to show:**  
In Swagger UI, execute:
1. `GET /care-queue/high` — show a few HIGH risk rows
2. `GET /encounters/5654628` — show the encounter detail

**What to say:**

> "Here's the risk scoring rule — five conditions, each adding points. A patient with 3 or more prior inpatient visits gets +3 points. Two or more prior emergency visits adds +2. And so on."

> "Scores 5 and above are HIGH risk. 3–4 are MEDIUM. Below 3 are LOW."

> "The `/care-queue/high` endpoint returns only HIGH risk encounters, sorted highest score first, so the team sees the most urgent cases at the top."

> "The `readmitted` field does not appear in any encounter or queue response — it's the historical outcome and must not influence the prioritization decision."

---

## Segment 5 — PATCH Intervention Workflow (45 seconds)

**What to show:**  
In Swagger UI, execute:
```
PATCH /interventions/5654628
{
  "status": "CONTACTED",
  "assigned_to": "Care Team A",
  "notes": "Spoke with patient, follow-up call scheduled for Friday"
}
```
Show the 200 response. Then restart the API (`Ctrl+C`, `uvicorn main:app --reload --port 8004`) and re-fetch via `/care-queue/high` to show the status persisted.

**What to say:**

> "The care team updates the intervention status as they work through the queue. The workflow goes PENDING_REVIEW → ASSIGNED → CONTACTED → FOLLOW_UP_SCHEDULED → CLOSED."

> "Each PATCH persists to PostgreSQL, so the status survives an API restart. This is not in-memory state."

> "Invalid statuses return a 422 error. An empty PATCH body also returns 422. A missing encounter ID returns 404."

---

## Segment 6 — Operational Summary (30 seconds)

**What to show:**  
In Swagger UI, execute `GET /operations/summary`.

**What to say:**

> "The operations endpoint gives hospital operations a live view of the workload. Total encounters by risk level, total interventions, and a breakdown by status."

> "All values are calculated from PostgreSQL in real time — nothing is hardcoded. If the care team closes 100 interventions, the counts update immediately."

> "For this MVP, completed means CLOSED. Everything else is pending."

---

## Segment 7 — Historical Readmission Analysis (30 seconds)

**What to show:**  
In Swagger UI, execute `GET /operations/readmission-analysis`.

**What to say:**

> "This is the retrospective evaluation. After scoring all 101,766 encounters without using `readmitted`, I can now ask: did HIGH-risk patients historically have more 30-day readmissions?"

> "HIGH risk: 28.6% readmission rate. MEDIUM: 21.6%. LOW: 10.0%. The HIGH group is 2.85 times more likely to appear in the historical readmission cohort."

> "The API response includes a note making clear that this is correlation, not causation. The rule is not clinically validated."

---

## Segment 8 — Business Value and Limitations (30 seconds)

**What to say:**

> "What did I build? A workflow, not a model. The hospital now has an explainable, queryable prioritization queue. The care team has a daily list. Operations can see the backlog. Clinical leadership can see the readmission correlation and challenge the thresholds."

> "What comes next? Collect intervention outcomes. Compare the rule against a logistic regression model using the same features. If ML improves stratification, migrate the scoring to `service.py` without touching any other layer."

> "Limitations: the scoring weights are assumptions, not clinical recommendations. This prototype has no authentication, no audit logging, and no HIPAA compliance. It must not be used with real patient data."

---

## End of Demo

Total target time: **3–5 minutes**

Recording tips:
- Record at 1920×1080 or higher
- Use `uvicorn main:app --port 8004` (no `--reload` for a cleaner terminal during demo)
- Execute each API call in Swagger, not curl, so the request/response is visually clear
- Pause briefly after each response to let viewers read the JSON
