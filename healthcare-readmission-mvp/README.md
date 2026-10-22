# Diabetes Readmission Intervention Queue

**Testleaf FDE Program — Week 2 Mini Project**
Stack: Python · FastAPI · PostgreSQL · psycopg3

> **LEARNING PROTOTYPE — Not for clinical decision-making.**
> This application was built as a training exercise. It is not a clinically validated scoring system and must not be used for real patient care decisions.

---

## Business Problem

A hospital has 101,766 historical diabetes inpatient encounters and is concerned about patients returning within 30 days of discharge. The care-management team cannot manually review every discharged patient with limited staff.

**Primary business decision:** Which recently discharged diabetes patients should the care-management team review first?

### Users and Outcomes

| User | What They Need | Business Outcome |
|---|---|---|
| Care Management Team | Prioritized review queue | Focus limited capacity on higher-risk cases |
| Hospital Operations | Queue and workload visibility | Understand intervention volume and backlog |
| Clinical Leadership | Explainable rationale | Review whether prioritization is operationally sensible |
| Finance / Transformation | Outcome and value signals | Assess whether the intervention is worth scaling |

---

## FDE Discovery

### What the Dataset Tells Us

| Area | Finding |
|---|---|
| Historical encounters | 101,766 diabetes inpatient encounters |
| Historical <30-day readmissions | 11,357 encounters (11.2% of total) |
| Prior healthcare utilization | `number_inpatient`, `number_emergency`, `number_outpatient` — complete for all rows |
| Operational / treatment attributes | `time_in_hospital`, `num_medications`, `discharge_disposition_id`, `admission_type_id` — complete |
| Historical outcome | `readmitted` ∈ {NO, <30, >30} — present for all rows; used ONLY for retrospective evaluation |

### What We Do NOT Know

- Which of the <30-day readmissions were preventable
- Cost of a single readmission event
- Current care-management capacity or existing discharge workflow
- Cost of a care-management intervention call
- Whether the rule thresholds have clinical validity

### MVP Hypothesis

- Prior healthcare utilization (inpatient, emergency, outpatient visits) is a reasonable proxy for care complexity after discharge
- A simple rule-based risk score is explainable enough for clinical leadership to review and challenge
- A risk queue (MEDIUM + HIGH only ≈ 8.4% of encounters) gives the team a tractable daily workload
- Historical `readmitted` can be used after scoring to evaluate whether the rule identified a higher-risk population — and it does (HIGH rate: 28.6% vs LOW rate: 10.0%)

---

## Dataset Analysis

**Source:** `data/diabetic_data.csv`  
**Total encounters:** 101,766  
**Required columns used:** 12 (all present, 0 missing values in scope fields)

### Required Columns

| Column | Type | Role in Application |
|---|---|---|
| `encounter_id` | Integer | Primary key |
| `patient_nbr` | Integer | Patient identifier (one patient may have multiple encounters) |
| `age` | String band | Age group e.g. `[50-60)` |
| `time_in_hospital` | Integer | Days admitted — used in risk scoring |
| `number_inpatient` | Integer | Prior inpatient visits (past year) — used in risk scoring |
| `number_emergency` | Integer | Prior emergency visits (past year) — used in risk scoring |
| `number_outpatient` | Integer | Prior outpatient visits (past year) — used in risk scoring |
| `num_medications` | Integer | Medications prescribed — used in risk scoring |
| `num_lab_procedures` | Integer | Lab tests ordered — stored, not scored |
| `discharge_disposition_id` | Integer | Where discharged — stored for context |
| `admission_type_id` | Integer | Admission type — stored for context |
| `readmitted` | String | Historical outcome: `NO`, `<30`, `>30` — **NEVER used in risk scoring** |

### Readmission Distribution

| Value | Count | % |
|---|---|---|
| NO (not readmitted) | 54,864 | 53.9% |
| >30 (readmitted after 30 days) | 35,545 | 34.9% |
| <30 (readmitted within 30 days) | 11,357 | 11.2% |

### Age Distribution

Dataset skews elderly (60–90 age range = 65% of encounters), consistent with a diabetes readmission study.

---

## Risk Scoring Rule

> **Critical data leakage rule:** `readmitted` is the historical outcome.
> It is stored in the database but **NEVER used** to calculate `risk_score` or `risk_level`.
> It is used ONLY in `/operations/readmission-analysis` for retrospective evaluation after scoring.

### Scoring Formula (Section 5 of assignment)

```
risk_score = 0
  + 3  if number_inpatient  >= 3
  + 2  if number_emergency  >= 2
  + 1  if number_outpatient >= 3
  + 1  if time_in_hospital  >= 7
  + 1  if num_medications   >= 20

Risk Level:
  0–2  → LOW
  3–4  → MEDIUM
  5–8  → HIGH
```

Maximum possible score: 8 (all five conditions met simultaneously).  
These weights are learning assumptions from the assignment — not clinically validated.

### Risk Level Distribution

| Risk Level | Encounters | % |
|---|---|---|
| HIGH (score ≥ 5) | 2,358 | 2.3% |
| MEDIUM (score 3–4) | 6,180 | 6.1% |
| LOW (score 0–2) | 93,228 | 91.6% |

Care queue (MEDIUM + HIGH): **8,538 encounters** — approximately 8.4% of discharges.

### Sample Encounters (from dataset)

| Encounter | Inpatient | Emergency | Outpatient | Days | Meds | Score | Level | Historical readmitted |
|---|---|---|---|---|---|---|---|---|
| 5654628 | 5 (+3) | 0 | 9 (+1) | 6 | 27 (+1) | 5 | HIGH | <30 |
| 7825020 | 3 (+3) | 0 | 0 | 7 (+1) | 27 (+1) | 5 | HIGH | <30 |
| 2549268 | 3 (+3) | 0 | 0 | 6 | 19 | 3 | MEDIUM | <30 |
| 2278392 | 0 | 0 | 0 | 1 | 1 | 0 | LOW | NO |

### Retrospective Validation

After scoring (using `readmitted` only as a check, not in the rule):

| Risk Level | Encounters | Readmitted <30 days | Rate |
|---|---|---|---|
| HIGH | 2,358 | 674 | **28.6%** |
| MEDIUM | 6,180 | 1,335 | **21.6%** |
| LOW | 93,228 | 9,348 | **10.0%** |

HIGH-risk encounters are **2.9× more likely** to appear in the historical <30-day readmission cohort than LOW-risk. The rule has measurable operational signal.

---

## Architecture

```
diabetic_data.csv
      ↓
  data_loader.py          reads CSV, computes risk_score/risk_level, bulk-inserts
      ↓
  PostgreSQL              healthcare_readmission_db
  (patient_encounters
   care_interventions)
      ↑
  database.py             connection management, schema init
  repository.py           all SQL (parameterized), no business logic
  service.py              risk scoring, metric computation, no SQL
  main.py                 FastAPI routes, HTTP error handling
      ↑
  Swagger / API Consumer  http://localhost:8004/docs
```

### File Responsibilities

| File | Responsibility |
|---|---|
| `database.py` | psycopg3 connection, loads `.env`, runs `schema.sql` on startup |
| `schema.sql` | Table definitions, constraints, indexes — idempotent (`IF NOT EXISTS`) |
| `data_loader.py` | Reads CSV, calls `service.py` for scoring, bulk-inserts via `ON CONFLICT DO NOTHING` |
| `service.py` | `calculate_risk_score()`, `classify_risk_level()`, operational metric assembly |
| `repository.py` | All SQL queries — parameterized `%s` only, no user input in SQL strings |
| `models.py` | Pydantic request/response models — validation, serialization |
| `main.py` | FastAPI routes, HTTP status codes, error responses |
| `conftest.py` | pytest fixtures: DB-derived encounter IDs, intervention state restore |
| `tests/` | 100 automated tests across service, endpoints, and Phase 5 metrics |

---

## Database Design

### Table A — `patient_encounters`

```sql
CREATE TABLE IF NOT EXISTS patient_encounters (
    encounter_id             BIGINT      PRIMARY KEY,
    patient_nbr              BIGINT      NOT NULL,
    age                      VARCHAR(10) NOT NULL,
    time_in_hospital         INTEGER     NOT NULL,
    number_inpatient         INTEGER     NOT NULL,
    number_emergency         INTEGER     NOT NULL,
    number_outpatient        INTEGER     NOT NULL,
    num_medications          INTEGER     NOT NULL,
    num_lab_procedures       INTEGER     NOT NULL,
    discharge_disposition_id INTEGER     NOT NULL,
    admission_type_id        INTEGER     NOT NULL,
    readmitted  VARCHAR(5)  NOT NULL CHECK (readmitted IN ('NO','<30','>30')),
    risk_score  INTEGER     NOT NULL CHECK (risk_score >= 0 AND risk_score <= 8),
    risk_level  VARCHAR(10) NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH'))
);
```

### Table B — `care_interventions`

```sql
CREATE TABLE IF NOT EXISTS care_interventions (
    intervention_id SERIAL      PRIMARY KEY,
    encounter_id    BIGINT      NOT NULL UNIQUE
                    REFERENCES patient_encounters(encounter_id) ON DELETE CASCADE,
    status          VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW'
                    CHECK (status IN (
                        'PENDING_REVIEW','ASSIGNED','CONTACTED',
                        'FOLLOW_UP_SCHEDULED','CLOSED'
                    )),
    assigned_to     VARCHAR(100),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Intervention lifecycle: `PENDING_REVIEW → ASSIGNED → CONTACTED → FOLLOW_UP_SCHEDULED → CLOSED`

---

## API Endpoints

All 8 mandatory endpoints from Section 9 of the assignment:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/encounters` | List encounters with pagination (`limit`, `offset`) |
| GET | `/encounters/{encounter_id}` | Single encounter — 404 if not found |
| GET | `/care-queue` | MEDIUM + HIGH risk queue, sorted by score DESC |
| GET | `/care-queue/high` | HIGH risk only, sorted by score DESC |
| PATCH | `/interventions/{encounter_id}` | Update status / assigned_to / notes |
| GET | `/operations/summary` | Encounter counts + intervention status breakdown |
| GET | `/operations/readmission-analysis` | Historical <30d readmission rates by risk tier |
| GET | `/management/dashboard` | Executive summary — volumes, queue, backlog, rates |

### Example Responses

**PATCH /interventions/5654628**
```json
{
  "status": "CONTACTED",
  "assigned_to": "Care Team A",
  "notes": "Follow-up appointment scheduled"
}
```
Response: `200 OK` with the updated `InterventionOut` object.

**GET /operations/summary** (example shape — actual values from DB):
```json
{
  "total_encounters": 101766,
  "high_risk": 2358,
  "medium_risk": 6180,
  "low_risk": 93228,
  "total_interventions": 8538,
  "pending_interventions": 8538,
  "completed_interventions": 0,
  "by_status": {"PENDING_REVIEW": 8538}
}
```

**GET /operations/readmission-analysis** (example shape):
```json
{
  "note": "readmitted is the historical outcome. It was NOT used to calculate risk_score ...",
  "by_risk_level": [
    {"risk_level": "HIGH",   "total_encounters": 2358, "readmitted_under_30_days": 674,  "readmission_rate_pct": 28.58},
    {"risk_level": "LOW",    "total_encounters": 93228,"readmitted_under_30_days": 9348, "readmission_rate_pct": 10.03},
    {"risk_level": "MEDIUM", "total_encounters": 6180, "readmitted_under_30_days": 1335, "readmission_rate_pct": 21.6}
  ],
  "high_to_low_readmission_ratio": 2.85
}
```

**GET /management/dashboard** (example shape):
```json
{
  "total_encounters": 101766,
  "risk_distribution": {"HIGH": 2358, "MEDIUM": 6180, "LOW": 93228},
  "care_queue_size": 8538,
  "high_risk_queue_size": 2358,
  "medium_risk_queue_size": 6180,
  "intervention_backlog": 8538,
  "completed_interventions": 0,
  "pct_selected_for_intervention": 8.39,
  "historical_readmission_rates": {"HIGH": 28.58, "MEDIUM": 21.6, "LOW": 10.03}
}
```

---

## PostgreSQL Setup

**Prerequisites:** PostgreSQL 18 running on `localhost:5432` (Postgres.app on macOS).

```bash
# Create the database (run once)
/Applications/Postgres.app/Contents/Versions/latest/bin/psql \
  -h localhost -U fde_user -d fde_db \
  -c "CREATE DATABASE healthcare_readmission_db OWNER fde_user;"

# Create tables (idempotent — safe to re-run)
/Applications/Postgres.app/Contents/Versions/latest/bin/psql \
  -h localhost -U fde_user -d healthcare_readmission_db \
  -f schema.sql

# Verify tables
/Applications/Postgres.app/Contents/Versions/latest/bin/psql \
  -h localhost -U fde_user -d healthcare_readmission_db \
  -c "\dt"
```

---

## Running the Project

### 1. Set up environment

```bash
cd /path/to/healthcare-readmission-mvp

# Copy and fill in credentials
cp .env.example .env
# Edit .env: set DB_PASSWORD and confirm other values
```

`.env` is covered by `.gitignore` and must never be committed.

### 2. Install dependencies

```bash
# From the repo root, with the shared venv activated:
source ../.venv/bin/activate
pip install -r requirements.txt
```

### 3. Load the dataset

```bash
python3 data_loader.py
```

Expected output:
```
Reading CSV …
  101,766 encounters parsed from CSV
  8,538 MEDIUM/HIGH encounters will enter the care queue
Ensuring schema exists …
Loading encounters into PostgreSQL …
Load complete. Querying summary …
```

Re-running is safe — `ON CONFLICT DO NOTHING` prevents duplicates without resetting intervention state.

### 4. Start the API

```bash
uvicorn main:app --reload --port 8004
```

Swagger UI: **http://localhost:8004/docs**

### 5. Run automated tests

```bash
# Unit tests only (no database required)
python3 -m pytest tests/test_service.py -v

# Full integration test suite (database must be loaded)
python3 -m pytest tests/ -v
```

Expected: **100 passed, 0 failed**

---

## Historical Readmission Analysis

The `/operations/readmission-analysis` endpoint evaluates whether the rule-based prioritization correlates with historical outcomes:

| Risk Level | Encounters | <30-day Readmission Rate |
|---|---|---|
| HIGH | 2,358 | **28.6%** |
| MEDIUM | 6,180 | **21.6%** |
| LOW | 93,228 | **10.0%** |
| HIGH / LOW ratio | — | **2.85×** |

**Important:** This is a retrospective correlation. It shows the rule identified a group that historically had more readmissions — it does not prove the rule is clinically valid or that interventions will reduce readmissions.

---

## FDE Reflection (Section 16 of assignment)

**1. What business problem did you solve?**
The care-management team cannot manually review every discharged diabetes patient. This application converts historical encounter data into a prioritized intervention queue, so limited staff capacity is focused on the patients most likely to return within 30 days.

**2. Who is the primary user?**
The care-management team who decides which patients to contact after discharge. Secondary: hospital operations (backlog visibility) and clinical leadership (explainability review).

**3. What decision does your application improve?**
Which patients to call or schedule a follow-up for first — replacing a manual or ad-hoc review with a rule-based, explainable queue ordered by risk score.

**4. What did the dataset prove?**
The scoring rule stratifies the population meaningfully: HIGH-risk encounters had a 28.6% historical <30-day readmission rate versus 10.0% for LOW — 2.9× higher. The rule has operational signal without ML. The care queue (8.4% of encounters) captures a disproportionate share of historically readmitted patients.

**5. What assumptions did you make?**
- Prior utilization (inpatient, emergency visits in the past year) is a proxy for care complexity after discharge
- The assignment's scoring thresholds and point weights are acceptable as a starting rule — they are not clinically validated
- Each encounter is scored independently; longitudinal patient history across encounters is not aggregated
- 8,538 encounters (8.4%) is a workable queue size relative to typical care-management team capacity
- The `fde_user` PostgreSQL role has sufficient privileges — no additional role separation for this MVP

**6. What must the hospital validate before this becomes a real product?**
- Clinical review of the scoring thresholds by physician leads and care-management specialists
- Whether the rule generalizes to this specific hospital's patient population (demographics may differ from the training dataset)
- Whether care-management outreach actually reduces readmissions (requires randomized or quasi-experimental evaluation)
- HIPAA compliance, data de-identification, audit logging, and role-based access control
- Integration with the hospital's actual discharge workflow and EHR system
- Patient consent and governance requirements

**7. Would you use rules, traditional ML, an LLM, or another approach next — and why?**
Start with this rule baseline and collect operational data from care-management interventions. Then compare against a logistic regression or gradient-boosted classifier using the same 12 features — this takes approximately one additional week and yields calibrated probability scores rather than ordinal tiers. LLMs are not appropriate here: the data is entirely structured (no free text to analyze), explainability to clinical staff is mandatory, and inference latency and cost would be unjustifiable for a batch prioritization job. Traditional ML is the natural next step.

---

## Prototype Limitations and Clinical Disclaimer

- **Not clinically validated.** The scoring rule and thresholds are learning assumptions from the FDE assignment, not recommendations from clinical literature.
- **No causal claim.** The readmission analysis is a retrospective correlation — it does not prove that interventions will reduce readmissions.
- **No patient identity protection.** This prototype uses raw dataset identifiers with no de-identification, encryption, or access control. It must not be deployed with real patient data.
- **Rule does not consider all clinical factors.** Lab values, diagnoses, medications, and discharge disposition are partially or fully unused.
- **Historical dataset.** The dataset reflects a historical population that may not represent future patients or this hospital's specific population.
