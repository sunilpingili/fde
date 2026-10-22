# Screenshots — Capture Instructions

Place your screenshots in this folder before submitting.
The API must be running (`uvicorn main:app --reload --port 8004`) for Swagger screenshots.

---

## 1. swagger_all_endpoints.png

**Where:** `http://localhost:8004/docs`  
**What to show:** The full Swagger UI with all 8 endpoint groups visible and at least one expanded to show the route detail. Scroll to show all: Encounters, Care Queue, Interventions, Operations, Management.

---

## 2. postgres_encounters_table.png

**Where:** pgAdmin → `healthcare_readmission_db` → Tables → `patient_encounters`  
**What to show:** Right-click → View/Edit Data → show a few rows with columns: `encounter_id`, `risk_level`, `risk_score`, `readmitted`. The row count at the bottom should read 101,766.

---

## 3. postgres_risk_distribution.png

**Where:** pgAdmin Query Tool or psql terminal  
**SQL to run:**
```sql
SELECT risk_level, COUNT(*) as count
FROM patient_encounters
GROUP BY risk_level
ORDER BY risk_level;
```
**What to show:** The result table showing HIGH: 2358, LOW: 93228, MEDIUM: 6180.

---

## 4. care_queue_response.png

**Where:** `http://localhost:8004/docs` → `GET /care-queue` → Execute  
**What to show:** The 200 response body with a few MEDIUM and HIGH rows, showing `risk_level`, `risk_score`, `status`, `encounter_id`.

---

## 5. patch_intervention.png

**Where:** `http://localhost:8004/docs` → `PATCH /interventions/{encounter_id}`  
**What to show:**
1. Set `encounter_id` to `5654628`
2. Request body: `{"status": "CONTACTED", "assigned_to": "Care Team A", "notes": "Called patient"}`
3. Execute and show the 200 response with the updated intervention object

---

## 6. operations_summary.png

**Where:** `http://localhost:8004/docs` → `GET /operations/summary` → Execute  
**What to show:** The full JSON response with all fields: `total_encounters: 101766`, risk counts, intervention counts, `by_status` breakdown.

---

## 7. readmission_analysis.png

**Where:** `http://localhost:8004/docs` → `GET /operations/readmission-analysis` → Execute  
**What to show:** The JSON response with `by_risk_level` array showing rates for HIGH (~28.6%), MEDIUM (~21.6%), LOW (~10.0%), and `high_to_low_readmission_ratio`.

---

## 8. management_dashboard.png

**Where:** `http://localhost:8004/docs` → `GET /management/dashboard` → Execute  
**What to show:** The full JSON response with `risk_distribution`, `care_queue_size: 8538`, `pct_selected_for_intervention`, and `historical_readmission_rates`.
