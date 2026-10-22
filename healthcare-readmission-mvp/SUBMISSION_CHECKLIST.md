# Submission Checklist — Diabetes Readmission Intervention Queue

Testleaf FDE Week 2 Mini Project  
Reference: Assignment PDF Sections 11, 13, 14

---

## Acceptance Criteria (Section 11)

| # | Criterion | Status | How to Verify |
|---|---|---|---|
| 1 | Dataset loaded into PostgreSQL without manually inserting individual encounters | PASS | Run `data_loader.py`; it bulk-inserts 101,766 rows via `executemany` |
| 2 | Risk score calculated without using `readmitted` | PASS | `test_readmitted_not_a_scoring_parameter` pytest; `readmitted` is not a parameter of `calculate_risk_score()` |
| 3 | MEDIUM and HIGH risk cases appear in the care queue | PASS | `GET /care-queue` returns 8,538 rows; `GET /care-queue/high` returns 2,358 |
| 4 | Intervention status updated and persists after FastAPI restarts | PASS | PostgreSQL-backed; `test_update_persists` verified; restart the server and re-fetch the same encounter |
| 5 | Operational summary calculated from stored data | PASS | `GET /operations/summary` — queries live from `patient_encounters` + `care_interventions` |
| 6 | Readmission analysis compares risk groups against historical `<30` outcomes | PASS | `GET /operations/readmission-analysis` — HIGH 28.6%, MEDIUM 21.6%, LOW 10.0% |
| 7 | Routes return useful HTTP errors for missing encounter IDs | PASS | `GET /encounters/9999999` → 404; `PATCH /interventions/9999999` → 404 |
| 8 | SQL is parameterized; no user-supplied values concatenated into SQL strings | PASS | All queries use `%s`; f-strings only used for column names from hardcoded sets |
| 9 | Code follows main / models / service / repository / database separation | PASS | Each file has a single responsibility documented in `README.md` |

---

## Mandatory FastAPI Endpoints (Section 9)

| # | Method | Endpoint | Implemented | Test Coverage |
|---|---|---|---|---|
| 1 | GET | `/encounters` | YES | `TestListEncounters` — 8 tests |
| 2 | GET | `/encounters/{encounter_id}` | YES | `TestGetEncounter` — 4 tests |
| 3 | GET | `/care-queue` | YES | `TestCareQueue` — 6 tests |
| 4 | GET | `/care-queue/high` | YES | `TestCareQueueHigh` — 4 tests |
| 5 | PATCH | `/interventions/{encounter_id}` | YES | `TestUpdateIntervention` — 10 tests |
| 6 | GET | `/operations/summary` | YES | `TestOperationsSummary` — 11 tests |
| 7 | GET | `/operations/readmission-analysis` | YES | `TestReadmissionAnalysis` — 13 tests |
| 8 | GET | `/management/dashboard` | YES | `TestManagementDashboard` — 13 tests |

---

## Test Results

Run the full suite:
```bash
cd healthcare-readmission-mvp
python3 -m pytest tests/ -v
```

Expected: **100 passed, 0 failed**

| Test file | Tests | Coverage |
|---|---|---|
| `tests/test_service.py` | 36 | Risk scoring: all 5 rules, boundary conditions, data leakage guard |
| `tests/test_endpoints.py` | 32 | Phases 4 endpoints: pagination, filtering, PATCH, 404/422 errors |
| `tests/test_phase5.py` | 37 (sic, counted above) | Operations summary, readmission analysis, dashboard |

> Note: tests modify `care_interventions` rows in the shared database. The `restore_intervention` pytest fixture in `tests/conftest.py` saves and restores state after each PATCH test to prevent permanent side-effects.

---

## Submission Deliverables (Section 13)

| Deliverable | Status | Location |
|---|---|---|
| GitHub repository (public) | TODO — push and share link | `https://github.com/sunilpingili/fde` |
| `README.md` — business problem, users, assumptions, architecture, API list, run instructions | DONE | `README.md` |
| `schema.sql` | DONE | `schema.sql` |
| `data_loader.py` | DONE | `data_loader.py` |
| FastAPI source files (`main.py`, `models.py`, `service.py`, `repository.py`, `database.py`) | DONE | project root |
| Swagger screenshot showing key endpoints | TODO — capture manually | `screenshots/swagger_all_endpoints.png` |
| PostgreSQL screenshot showing loaded records | TODO — capture manually | `screenshots/postgres_tables.png` |
| 3–5 minute demo video | TODO — record manually | See `DEMO_SCRIPT.md` |

---

## Pre-Submission Verification Steps

### 1. Confirm database is populated
```bash
/Applications/Postgres.app/Contents/Versions/latest/bin/psql \
  -h localhost -U fde_user -d healthcare_readmission_db \
  -c "SELECT risk_level, COUNT(*) FROM patient_encounters GROUP BY risk_level ORDER BY risk_level;"
```
Expected:
```
 risk_level | count
------------+-------
 HIGH       |  2358
 LOW        | 93228
 MEDIUM     |  6180
```

### 2. Confirm interventions exist
```bash
/Applications/Postgres.app/Contents/Versions/latest/bin/psql \
  -h localhost -U fde_user -d healthcare_readmission_db \
  -c "SELECT COUNT(*) FROM care_interventions;"
```
Expected: `8538`

### 3. Run full test suite
```bash
cd healthcare-readmission-mvp && python3 -m pytest tests/ -v
```
Expected: **100 passed**

### 4. Start the API and open Swagger
```bash
uvicorn main:app --reload --port 8004
# Open: http://localhost:8004/docs
```

### 5. Verify persistence after restart
```bash
# 1. Update an intervention
curl -X PATCH http://localhost:8004/interventions/5654628 \
  -H "Content-Type: application/json" \
  -d '{"status":"CONTACTED","assigned_to":"Care Team A","notes":"Called patient"}'

# 2. Stop uvicorn (Ctrl+C), restart it
uvicorn main:app --reload --port 8004

# 3. Confirm the change survived
curl http://localhost:8004/care-queue | python3 -m json.tool | grep -A3 "5654628"
```

### 6. Verify .env is not tracked by git
```bash
cd .. && git check-ignore -v healthcare-readmission-mvp/.env
```
Expected: `.gitignore:5:.env  healthcare-readmission-mvp/.env`

### 7. Check no credentials are hardcoded
```bash
grep -r "FDE_Local\|password\s*=" healthcare-readmission-mvp/*.py 2>/dev/null
```
Expected: no output (all credentials come from `.env` via `python-dotenv`)

---

## Screenshots to Capture Manually

See `screenshots/README.md` for exact instructions.

| Filename | What to show |
|---|---|
| `swagger_all_endpoints.png` | Swagger UI at `/docs` with all 8 endpoints visible and expanded |
| `postgres_encounters_table.png` | pgAdmin or psql showing `patient_encounters` with row count and risk columns |
| `postgres_risk_distribution.png` | Query result: `SELECT risk_level, COUNT(*) FROM patient_encounters GROUP BY risk_level` |
| `care_queue_response.png` | Swagger UI response for `GET /care-queue` showing MEDIUM + HIGH items |
| `patch_intervention.png` | Swagger UI showing `PATCH /interventions/{encounter_id}` request and 200 response |
| `operations_summary.png` | Swagger UI response for `GET /operations/summary` |
| `readmission_analysis.png` | Swagger UI response for `GET /operations/readmission-analysis` |
| `management_dashboard.png` | Swagger UI response for `GET /management/dashboard` |

---

## GitHub Submission Instructions

1. Create a `.gitignore` entry confirms `.env` is excluded (already done)
2. Stage and commit all project files:
   ```bash
   cd /Users/sunil/Documents/myprojects/fde_oct_1
   git add healthcare-readmission-mvp/
   git status   # review before committing
   git commit -m "Add Week 2 mini project: Diabetes Readmission Intervention Queue"
   ```
3. Push to your branch and open a pull request to `main`:
   ```bash
   git push origin oct10/1
   # Then open a PR on GitHub: https://github.com/sunilpingili/fde
   ```
4. Share the repository URL with your Testleaf instructor

---

## Evaluation Rubric Self-Assessment (Section 14)

| Area | Weight | Self-Assessment |
|---|---|---|
| FDE problem understanding | 15% | Business problem, users, unknowns, hypothesis documented in README |
| Dataset ingestion / cleanup | 10% | Bulk insert via `data_loader.py`, 12 focused columns, 0 missing values, idempotent |
| PostgreSQL design | 15% | Two tables with PK, FK, CHECK constraints, indexes, CASCADE delete |
| Business / risk rules | 15% | Isolated in `service.py`, no `readmitted` dependency, 36 unit tests |
| FastAPI + layering | 20% | 8 endpoints, clean layer separation, 404/422 errors, parameterized SQL |
| Care-management workflow | 10% | Queue built at load time, PATCH updates persisted, lifecycle statuses enforced |
| Operational metrics | 10% | All 3 metrics endpoints query live data from PostgreSQL |
| README / demo quality | 5% | Full README with all required sections; demo script in `DEMO_SCRIPT.md` |
