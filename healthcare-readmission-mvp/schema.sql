-- Diabetes Readmission Intervention Queue — PostgreSQL Schema
-- Safe to run repeatedly: all statements use IF NOT EXISTS / DO NOTHING

-- Table A: patient_encounters
-- Stores one row per encounter loaded from diabetic_data.csv.
-- risk_score and risk_level are computed at load time (data_loader.py).
-- The readmitted column is stored for retrospective analysis ONLY —
-- it is never used to calculate risk_score or risk_level.

CREATE TABLE IF NOT EXISTS patient_encounters (
    encounter_id             BIGINT        PRIMARY KEY,
    patient_nbr              BIGINT        NOT NULL,
    age                      VARCHAR(10)   NOT NULL,
    time_in_hospital         INTEGER       NOT NULL,
    number_inpatient         INTEGER       NOT NULL,
    number_emergency         INTEGER       NOT NULL,
    number_outpatient        INTEGER       NOT NULL,
    num_medications          INTEGER       NOT NULL,
    num_lab_procedures       INTEGER       NOT NULL,
    discharge_disposition_id INTEGER       NOT NULL,
    admission_type_id        INTEGER       NOT NULL,
    readmitted               VARCHAR(5)    NOT NULL
                             CHECK (readmitted IN ('NO', '<30', '>30')),
    risk_score               INTEGER       NOT NULL
                             CHECK (risk_score >= 0 AND risk_score <= 8),
    risk_level               VARCHAR(10)   NOT NULL
                             CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'))
);

-- Table B: care_interventions
-- One row per encounter in the care queue (MEDIUM or HIGH risk).
-- Created automatically when data_loader.py seeds patient_encounters.
-- UNIQUE on encounter_id enforces one active intervention per encounter for this MVP.

CREATE TABLE IF NOT EXISTS care_interventions (
    intervention_id  SERIAL        PRIMARY KEY,
    encounter_id     BIGINT        NOT NULL UNIQUE
                     REFERENCES patient_encounters(encounter_id) ON DELETE CASCADE,
    status           VARCHAR(30)   NOT NULL DEFAULT 'PENDING_REVIEW'
                     CHECK (status IN (
                         'PENDING_REVIEW',
                         'ASSIGNED',
                         'CONTACTED',
                         'FOLLOW_UP_SCHEDULED',
                         'CLOSED'
                     )),
    assigned_to      VARCHAR(100),
    notes            TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_pe_risk_level
    ON patient_encounters (risk_level);

CREATE INDEX IF NOT EXISTS idx_pe_patient_nbr
    ON patient_encounters (patient_nbr);

CREATE INDEX IF NOT EXISTS idx_ci_status
    ON care_interventions (status);

CREATE INDEX IF NOT EXISTS idx_ci_encounter_id
    ON care_interventions (encounter_id);
