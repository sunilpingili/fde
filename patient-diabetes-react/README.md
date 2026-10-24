# Patient Diabetes React Frontend

A React frontend for the Diabetes Readmission Intervention Queue project, built as part of the FDE (Full-stack Developer Engineering) program at Testleaf.

> **Learning Prototype — Not for Clinical Use**

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup and Installation](#setup-and-installation)
- [Running the App](#running-the-app)
- [Features](#features)
  - [Patient Search](#patient-search)
  - [Update Intervention](#update-intervention)
- [Component Architecture](#component-architecture)
- [API Integration](#api-integration)
- [State Management](#state-management)
- [Styling](#styling)
- [Build](#build)
- [Known Limitations](#known-limitations)

---

## Overview

This single-page React application connects to the FastAPI backend (`http://localhost:8004`) to allow hospital staff to:

1. **Search** for diabetes patient encounters by patient number, risk level, and risk score
2. **Review** current intervention status and last-updated timestamp directly from the search results
3. **Update** the care-management workflow for HIGH and MEDIUM risk encounters (status, assigned-to, notes)

The app was built incrementally as part of a learning exercise — one screen at a time — to demonstrate React state, controlled components, `fetch` API calls, conditional rendering, and component composition.

---

## Tech Stack

| Tool | Version | Purpose |
|---|---|---|
| React | 19.3 | UI library |
| Vite | 8.3 | Build tool and dev server |
| JavaScript (JSX) | ES2022 | Component language |
| Plain CSS | — | Styling (no CSS framework) |
| concurrently | latest | Run API + UI with one command |
| oxlint | 1.88 | Linter |

No routing library (e.g. React Router) is used. Page navigation is handled by a `currentPage` state variable in `App.jsx`.

---

## Prerequisites

1. **Node.js** 18+ and **npm** installed
2. **FastAPI backend** running at `http://localhost:8004`
   - See `/healthcare-readmission-mvp/README.md` for backend setup
   - The backend must be running before using the frontend

---

## Project Structure

```
patient-diabetes-react/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── SearchPatient.jsx     # Patient search form + results table
│   │   ├── InterventionUpdate.jsx # PATCH intervention form
│   │   └── RiskBadge.jsx         # Shared risk level badge component
│   ├── App.jsx                   # Root — owns page navigation state
│   ├── App.css                   # All styles (single stylesheet)
│   └── main.jsx                  # React entry point
├── index.html
├── package.json
├── vite.config.js
└── README.md
```

---

## Setup and Installation

```bash
# From the repo root
cd patient-diabetes-react

# Install dependencies (includes concurrently)
npm install
```

---

## Running the App

### Start both servers with one command (recommended)

```bash
npm run start
```

This uses `concurrently` to launch the FastAPI backend and the Vite frontend together in the same terminal window. Logs are colour-coded:

- **Blue `[API]`** — uvicorn output (FastAPI on port 8004)
- **Green `[UI]`** — Vite output (React on port 5173)

Press `Ctrl+C` once to stop both servers.

> Run this from the `patient-diabetes-react/` directory. The `dev:api` script navigates to `../healthcare-readmission-mvp` automatically.

### Run servers separately

If you need separate terminal windows (e.g. to see logs independently):

```bash
# Terminal 1 — FastAPI backend
npm run dev:api

# Terminal 2 — React frontend
npm run dev
```

### All npm scripts

| Script | What it does |
|---|---|
| `npm run start` | Starts FastAPI + Vite together (recommended) |
| `npm run dev` | Vite dev server only (frontend) |
| `npm run dev:api` | uvicorn only (backend, port 8004) |
| `npm run build` | Production build → `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | Run oxlint |

### Production build

```bash
npm run build
```

Output goes to `dist/`. Preview it with:

```bash
npm run preview
```

---

## Features

### Patient Search

**URL:** `http://localhost:5173` (default, search screen)

The search screen allows filtering diabetes hospital encounters using three optional filters:

| Filter | Input type | API parameter |
|---|---|---|
| Patient Number | Text | `patient_nbr` |
| Risk Level | Dropdown | `risk_level` |
| Min Risk Score | Number (0–8) | `risk_score` |

All three filters are optional. Leaving all blank and clicking **Search** returns the 100 highest-risk encounters. Filters can be combined (e.g. patient number + HIGH risk level).

Press **Enter** in any input field to trigger the search.

**Results table columns:**

| Column | Source | Notes |
|---|---|---|
| Encounter ID | `patient_encounters.encounter_id` | Clickable link — opens the Update Intervention page |
| Patient Number | `patient_encounters.patient_nbr` | — |
| Age | `patient_encounters.age` | Age bracket, e.g. `[50-60]` |
| Risk Score | `patient_encounters.risk_score` | Displayed as `X / 8` |
| Risk Level | `patient_encounters.risk_level` | Colour-coded badge: HIGH (red), MEDIUM (orange), LOW (green) |
| Status | `care_interventions.status` | Intervention workflow status; `—` for LOW risk (no intervention record) |
| Last Updated (UTC) | `care_interventions.updated_at` | Timestamp of last PATCH update; `—` if never updated |

Results are sorted by risk score descending (highest risk first), then by encounter ID. Capped at 100 rows per search.

**State feedback:**

| State | Display |
|---|---|
| Before first search | Instructional prompt |
| Loading | Spinner message |
| API error | Red error box with server message |
| No results | Empty state message |
| Results found | Count bar + table |

---

### Update Intervention

Accessed by clicking any **Encounter ID** link in the search results.

Displays read-only encounter summary at the top (Encounter ID, Patient Number, Age, Risk Score, Risk Level badge). Below that, a form with three editable fields:

| Field | Input type | API field | Valid values |
|---|---|---|---|
| Status | Dropdown | `status` | `PENDING_REVIEW`, `ASSIGNED`, `CONTACTED`, `FOLLOW_UP_SCHEDULED`, `CLOSED` |
| Assigned To | Text | `assigned_to` | Any string, e.g. `Dr. Smith` |
| Notes | Textarea | `notes` | Free text |

All three fields are optional — you can update just one. The client validates that at least one field is filled before sending the request.

After clicking **Update**:
- **Success:** Green result box appears below the form showing the full updated intervention record (status, assigned_to, notes, updated_at)
- **404 error:** Shown if you click a LOW risk encounter (those have no care intervention record — only HIGH and MEDIUM are in the care queue)
- **Validation error:** Pydantic error messages are extracted from the API's `detail` array and displayed in a human-readable format

Click **← Back to Search** to return to the search page. Your previous search results are preserved.

---

## Component Architecture

```
App.jsx
│  State: currentPage ("search" | "intervention")
│  State: selectedEncounter (encounter object | null)
│
├── SearchPatient.jsx          (currentPage === "search")
│   Props: onSelectEncounter(enc)
│   State: patientNbr, riskLevel, riskScore (form inputs)
│          results, searched, loading, error (search state)
│   Renders: RiskBadge
│
└── InterventionUpdate.jsx     (currentPage === "intervention")
    Props: encounter (the clicked row), onBack()
    State: status, assignedTo, notes (form inputs)
           result, loading, error (update state)
    Renders: RiskBadge

RiskBadge.jsx
    Props: level ("HIGH" | "MEDIUM" | "LOW")
    Pure display — no state
```

**Why no React Router?**
The app has two screens and uses a single state variable (`currentPage`) to switch between them. Adding a router for two pages would be unnecessary complexity at this learning stage. The selected encounter object is passed directly via props instead of via URL params.

---

## API Integration

Base URL: `http://localhost:8004` (defined as `API_URL` constant in each component)

### Endpoints used

#### `GET /encounters/search`

Called by `SearchPatient.jsx` → `handleSearch()`.

```
GET /encounters/search?patient_nbr=84002391&risk_level=HIGH&limit=100
```

Query parameters are built with `URLSearchParams`. Only non-empty values are appended:

```js
const params = new URLSearchParams();
if (patientNbr) params.append("patient_nbr", patientNbr);
if (riskLevel)  params.append("risk_level",  riskLevel);
if (riskScore)  params.append("risk_score",  riskScore);
params.append("limit", "100");
```

Response is an array of encounter objects. Each includes `intervention_status` and `intervention_updated_at` from a LEFT JOIN on `care_interventions` in the backend.

#### `PATCH /interventions/{encounter_id}`

Called by `InterventionUpdate.jsx` → `handleUpdate()`.

```
PATCH /interventions/67162368
Content-Type: application/json

{ "status": "ASSIGNED", "assigned_to": "Dr. Smith", "notes": "Follow-up booked" }
```

Only fields the user filled in are included in the body. Returns the updated `care_interventions` row on success, or a 422 validation error if an invalid status value is sent.

### Error handling

- Non-OK responses are caught and displayed as readable messages
- Pydantic validation errors (`detail` is an array) are joined: `body.detail.map(e => e.msg).join("; ")`
- 404 from PATCH is explained as "no intervention record" (LOW risk encounter)
- Network errors (backend not running) are caught by the `try/catch` block

### Timestamp formatting

```js
function formatUtc(isoString) {
  if (!isoString) return "—";
  const d = new Date(isoString);
  return d.toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "UTC",          // forces UTC display — never local timezone
    timeZoneName: "short",    // appends "UTC" to the output
  });
}
```

The `timeZone: "UTC"` option forces the display to UTC regardless of the browser's local timezone. The label "UTC" comes from `timeZoneName: "short"` applied to that forced timezone.

---

## State Management

No external state library (Redux, Zustand, etc.) is used. All state is plain `useState` hooks.

### App.jsx
| State | Type | Purpose |
|---|---|---|
| `currentPage` | `"search" \| "intervention"` | Which screen to render |
| `selectedEncounter` | `object \| null` | The encounter row passed to the update page |

### SearchPatient.jsx
| State | Type | Purpose |
|---|---|---|
| `patientNbr` | `string` | Controlled input for patient number filter |
| `riskLevel` | `string` | Controlled select for risk level filter |
| `riskScore` | `string` | Controlled input for risk score filter |
| `results` | `array` | API response stored after a successful search |
| `searched` | `boolean` | Guards the results section — false = show prompt, true = show results or empty state |
| `loading` | `boolean` | Disables Search button and shows spinner |
| `error` | `string \| null` | API or network error message |

### InterventionUpdate.jsx
| State | Type | Purpose |
|---|---|---|
| `status` | `string` | Controlled select for status |
| `assignedTo` | `string` | Controlled input for assigned_to |
| `notes` | `string` | Controlled textarea for notes |
| `result` | `object \| null` | API response after successful PATCH |
| `loading` | `boolean` | Disables Update button |
| `error` | `string \| null` | Error message from PATCH |

---

## Styling

All styles live in `src/App.css`. No CSS framework or preprocessor is used.

### Layout
- Page width: `width: 94%; max-width: 1600px` — scales with viewport, caps on ultra-wide screens
- Card: white background, `border-radius: 10px`, `box-shadow` for depth
- Search form: flexbox row (`display: flex; align-items: flex-end`) — 3 inputs + button on one line on desktop

### Table
- Wrapped in `.table-scroll` (`overflow-x: auto`) for horizontal scroll on narrow screens
- `table { width: max-content; min-width: 100% }` — expands to fill available space but scrolls when wider than the viewport
- `white-space: nowrap` on `th` and `td` prevents content wrapping
- Column `min-width` values ensure each column has enough room:
  - Encounter ID: 120px, Risk Score: 80px, Status: 170px, Last Updated: 200px

### Risk badges
Inline pill badges using colour-coded background + text:

| Level | Background | Text |
|---|---|---|
| HIGH | `#fed7d7` (red-100) | `#9b2c2c` (red-800) |
| MEDIUM | `#feebc8` (orange-100) | `#7b341e` (orange-800) |
| LOW | `#c6f6d5` (green-100) | `#276749` (green-800) |

---

## Build

```
dist/index.html          ~0.47 kB (gzip: 0.30 kB)
dist/assets/index.css    ~8.2 kB  (gzip: 2.4 kB)
dist/assets/index.js     ~229 kB  (gzip: 71 kB)   ← React + ReactDOM included
```

---

## Known Limitations

- **No authentication** — any user can view and update any encounter
- **No pagination UI** — results are capped at 100 rows; no next-page button
- **CORS is open (`allow_origins=["*"]`)** — suitable for local development only; must be restricted before any deployment
- **API URL is hardcoded** — `http://localhost:8004` is set as a constant in each component; a `.env` file should be used for different environments
- **No optimistic UI** — after updating an intervention, the search results table is not automatically refreshed; re-run the search to see the new status and timestamp
- **LOW risk encounters** — clicking their Encounter ID opens the update form but the PATCH will return 404 since only HIGH and MEDIUM encounters have a `care_interventions` record; the form shows a clear error message explaining this
