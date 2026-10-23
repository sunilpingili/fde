// Step 3: Copy of the interface + fetch from your own API
// API must be running: uvicorn main:app --reload --port 8004
// Docs available at: http://localhost:8004/docs

// Same interface as before
interface Encounter {
  encounter_id: number;
  patient_id: number;    // named patient_id here; the API returns it as patient_nbr
  risk_score: number;
  risk_level: string;
  age: string;
}

// The full shape returned by GET /encounters/{encounter_id}
// Matches EncounterOut in models.py
interface EncounterApiResponse {
  encounter_id: number;
  patient_nbr: number;
  age: string;
  time_in_hospital: number;
  number_inpatient: number;
  number_emergency: number;
  number_outpatient: number;
  num_medications: number;
  num_lab_procedures: number;
  discharge_disposition_id: number;
  admission_type_id: number;
  risk_score: number;
  risk_level: string;
}

// fetchEncounter: calls GET /encounters/{id} and prints the response as JSON
async function fetchEncounter(encounterId: number): Promise<void> {
  const url = `http://localhost:8004/encounters/${encounterId}`;

  console.log(`\nFetching encounter ${encounterId} from: ${url}`);

  const response = await fetch(url);

  if (!response.ok) {
    console.error(`Error: ${response.status} ${response.statusText}`);
    return;
  }

  // Parse the response body as JSON — TypeScript types the result as EncounterApiResponse
  const data: EncounterApiResponse = await response.json();

  // Print the full JSON response
  console.log("\n=== API Response (full JSON) ===");
  console.log(JSON.stringify(data, null, 2));

  // Also map it into the simpler Encounter interface we defined
  const enc: Encounter = {
    encounter_id: data.encounter_id,
    patient_id: data.patient_nbr,
    risk_score: data.risk_score,
    risk_level: data.risk_level,
    age: data.age,
  };

  console.log("\n=== Mapped to Encounter interface ===");
  console.log(enc);
}

// Entry point — test with a HIGH risk encounter from the dataset
const ENCOUNTER_ID = 2278392; // LOW risk encounter (score=0) — safe to query
fetchEncounter(ENCOUNTER_ID);
