// Step 1: Define the Encounter interface
// An interface in TypeScript is a contract — it defines the shape (structure) of an object.
// Think of it like a blueprint: any object of type Encounter MUST have these fields.

interface Encounter {
  encounter_id: number;
  patient_id: number;
  risk_score: number;
  risk_level: string;
  age: string;           // extra column — age bracket from the dataset e.g. "[50-60)"
}

// Step 2: Create an array with 2–3 hardcoded Encounter values and print it
// TypeScript knows every item in this array must match the Encounter interface.
// If you add a field that doesn't exist (or misspell one), TypeScript gives a compile error.

const encounters: Encounter[] = [
  {
    encounter_id: 67162368,
    patient_id: 71658174,
    risk_score: 8,
    risk_level: "HIGH",
    age: "[70-80)",
  },
  {
    encounter_id: 2552952,
    patient_id: 89382658,
    risk_score: 4,
    risk_level: "MEDIUM",
    age: "[60-70)",
  },
  {
    encounter_id: 2278392,
    patient_id: 8299552,
    risk_score: 0,
    risk_level: "LOW",
    age: "[50-60)",
  },
];

// Print the entire array
console.log("=== Hardcoded Encounter Array ===");
console.log(encounters);

// Print each encounter individually (shows the structure clearly)
console.log("\n=== Individual Encounters ===");
encounters.forEach((enc: Encounter) => {
  console.log(
    `ID: ${enc.encounter_id} | Patient: ${enc.patient_id} | Score: ${enc.risk_score} | Level: ${enc.risk_level} | Age: ${enc.age}`
  );
});
