# Day 5 — TypeScript Interface & Fetch Practice

Classwork: TypeScript interfaces, typed arrays, and calling your own FastAPI.

---

## Files

| File | What it does |
|---|---|
| `encounter_interface.ts` | Steps 1 & 2 — define interface, create hardcoded array, print it |
| `encounter_fetch.ts` | Step 3 — copy of the interface + fetch from your own API |

---

## Step 1 & 2 — Interface and Hardcoded Array (`encounter_interface.ts`)

### What is a TypeScript interface?

An **interface** is a blueprint that describes the shape of an object. Any object typed as
`Encounter` must have exactly these fields with exactly these types. If you try to add a field
that isn't in the interface, TypeScript gives a compile-time error before the code even runs.

```ts
interface Encounter {
  encounter_id: number;
  patient_id:   number;
  risk_score:   number;
  risk_level:   string;
  age:          string;
}
```

### Hardcoded array

```ts
const encounters: Encounter[] = [
  { encounter_id: 67162368, patient_id: 71658174, risk_score: 8, risk_level: "HIGH",   age: "[70-80)" },
  { encounter_id: 2552952,  patient_id: 89382658, risk_score: 4, risk_level: "MEDIUM", age: "[60-70)" },
  { encounter_id: 2278392,  patient_id: 8299552,  risk_score: 0, risk_level: "LOW",    age: "[50-60)" },
];
```

`Encounter[]` means "an array where every item must be of type Encounter."

### Run it

```bash
npx tsx encounter_interface.ts
```

### Expected output

```
=== Hardcoded Encounter Array ===
[
  { encounter_id: 67162368, patient_id: 71658174, risk_score: 8, risk_level: 'HIGH',   age: '[70-80)' },
  { encounter_id: 2552952,  patient_id: 89382658, risk_score: 4, risk_level: 'MEDIUM', age: '[60-70)' },
  { encounter_id: 2278392,  patient_id: 8299552,  risk_score: 0, risk_level: 'LOW',    age: '[50-60)' }
]

=== Individual Encounters ===
ID: 67162368 | Patient: 71658174 | Score: 8 | Level: HIGH   | Age: [70-80)
ID: 2552952  | Patient: 89382658 | Score: 4 | Level: MEDIUM | Age: [60-70)
ID: 2278392  | Patient: 8299552  | Score: 0 | Level: LOW    | Age: [50-60)
```

---

## Step 3 — Fetch from Your Own API (`encounter_fetch.ts`)

### What it does

Calls `GET /encounters/{encounter_id}` on your running FastAPI and prints the response as JSON.

The file defines two interfaces:

- `EncounterApiResponse` — matches the full shape returned by the API (13 fields, mirrors `EncounterOut` in `models.py`)
- `Encounter` — the simpler 5-field interface from Steps 1 & 2

After fetching, it maps the API response into the simpler `Encounter` interface to show how you
can reshape data from an external source into your own type.

### Pre-requisite: start the API

```bash
# From healthcare-readmission-mvp/
cd /Users/sunil/Documents/myprojects/fde_oct_1/healthcare-readmission-mvp
uvicorn main:app --reload --port 8004
```

Swagger docs: http://localhost:8004/docs

### Run it

```bash
# In a second terminal, from this folder
npx tsx encounter_fetch.ts
```

### Expected output

```
Fetching encounter 2278392 from: http://localhost:8004/encounters/2278392

=== API Response (full JSON) ===
{
  "encounter_id": 2278392,
  "patient_nbr": 8299552,
  "age": "[50-60)",
  "time_in_hospital": 1,
  "number_inpatient": 0,
  "number_emergency": 0,
  "number_outpatient": 0,
  "num_medications": 18,
  "num_lab_procedures": 41,
  "discharge_disposition_id": 1,
  "admission_type_id": 6,
  "risk_score": 0,
  "risk_level": "LOW"
}

=== Mapped to Encounter interface ===
{ encounter_id: 2278392, patient_id: 8299552, risk_score: 0, risk_level: 'LOW', age: '[50-60)' }
```

### Try different encounter IDs

Change `ENCOUNTER_ID` at the bottom of `encounter_fetch.ts`:

| Encounter ID | Risk Level | Score | Notes |
|---|---|---|---|
| `2278392` | LOW | 0 | Default in the file |
| `67162368` | HIGH | 8 | Highest scoring encounter in the dataset |
| `2552952` | MEDIUM | 4 | First MEDIUM encounter |
| `9999999` | — | — | Does not exist → API returns 404 |

---

## How to run TypeScript without compiling

This project uses `tsx`, which runs TypeScript files directly without a separate compile step.

```bash
npx tsx <filename>.ts
```

Node.js version: v22.20.0
tsx version: v4.23.15
