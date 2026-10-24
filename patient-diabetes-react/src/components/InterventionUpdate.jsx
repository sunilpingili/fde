import { useState } from "react";
import RiskBadge from "./RiskBadge";

const API_URL = "http://localhost:8004";

const STATUS_OPTIONS = [
  { value: "",                   label: "— select status —" },
  { value: "PENDING_REVIEW",     label: "PENDING_REVIEW" },
  { value: "ASSIGNED",           label: "ASSIGNED" },
  { value: "CONTACTED",          label: "CONTACTED" },
  { value: "FOLLOW_UP_SCHEDULED",label: "FOLLOW_UP_SCHEDULED" },
  { value: "CLOSED",             label: "CLOSED" },
];

function Field({ label, children }) {
  return (
    <div className="update-field">
      <label>{label}</label>
      {children}
    </div>
  );
}

function InterventionUpdate({ encounter, onBack }) {
  const [status,     setStatus]     = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [notes,      setNotes]      = useState("");
  const [result,     setResult]     = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  async function handleUpdate() {
    // Build body — only include fields the user filled in
    const body = {};
    if (status)     body.status      = status;
    if (assignedTo) body.assigned_to = assignedTo;
    if (notes)      body.notes       = notes;

    if (Object.keys(body).length === 0) {
      setError("Please fill in at least one field before updating.");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(
        `${API_URL}/interventions/${encounter.encounter_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      );

      if (res.status === 404) {
        throw new Error(
          `No care intervention record found for encounter ${encounter.encounter_id}. ` +
          "Only HIGH and MEDIUM risk encounters are in the care queue."
        );
      }
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        // Pydantic returns detail as an array of validation errors
        let msg;
        if (Array.isArray(body.detail)) {
          msg = body.detail.map((e) => e.msg).join("; ");
        } else {
          msg = body.detail || `Server returned ${res.status}`;
        }
        throw new Error(msg);
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      {/* Page header */}
      <div className="page-header">
        <button className="back-link" onClick={onBack}>
          ← Back to Search
        </button>
        <h1>Update Intervention</h1>
        <p className="subtitle">
          Manage the care-management workflow for this encounter.
        </p>
      </div>

      <div className="card">
        {/* Blue title bar */}
        <div className="update-header">
          <span>Diabetes Patient Management</span>
          <RiskBadge level={encounter.risk_level} />
        </div>

        {/* Read-only encounter summary */}
        <div className="update-summary">
          <div className="summary-row">
            <span className="summary-label">Encounter ID</span>
            <span className="summary-value mono">{encounter.encounter_id}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">Patient Number</span>
            <span className="summary-value mono">{encounter.patient_nbr}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">Age</span>
            <span className="summary-value">{encounter.age}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">Risk Score</span>
            <span className="summary-value">{encounter.risk_score} / 8</span>
          </div>
        </div>

        {/* Update form */}
        <div className="update-form-panel">
          <div className="panel-title">Care Intervention Fields</div>

          <div className="update-two-col">
            <Field label="Status">
              <select value={status} onChange={(e) => setStatus(e.target.value)}>
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </Field>

            <Field label="Assigned To">
              <input
                type="text"
                value={assignedTo}
                onChange={(e) => setAssignedTo(e.target.value)}
                placeholder="e.g. Dr. Smith"
              />
            </Field>
          </div>

          <Field label="Notes">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add care notes here…"
              rows={4}
            />
          </Field>

          <div className="update-actions">
            <button
              className="btn-update"
              onClick={handleUpdate}
              disabled={loading}
            >
              {loading ? "Updating…" : "Update"}
            </button>
          </div>
        </div>

        {/* Result / error display */}
        {(result || error) && (
          <div className={`update-result ${error ? "update-result--error" : "update-result--success"}`}>
            <div className="update-result-title">
              {error ? "⚠️  Update Failed" : "✓  Update Successful"}
            </div>

            {error && <p className="update-result-message">{error}</p>}

            {result && (
              <table className="result-table">
                <tbody>
                  <tr>
                    <td className="result-key">Encounter ID</td>
                    <td className="result-val">{result.encounter_id}</td>
                  </tr>
                  <tr>
                    <td className="result-key">Status</td>
                    <td className="result-val">{result.status}</td>
                  </tr>
                  <tr>
                    <td className="result-key">Assigned To</td>
                    <td className="result-val">{result.assigned_to ?? "—"}</td>
                  </tr>
                  <tr>
                    <td className="result-key">Notes</td>
                    <td className="result-val">{result.notes ?? "—"}</td>
                  </tr>
                  <tr>
                    <td className="result-key">Updated At</td>
                    <td className="result-val">{result.updated_at ?? "—"}</td>
                  </tr>
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      <p className="disclaimer">Learning Prototype — Not for Clinical Use</p>
    </div>
  );
}

export default InterventionUpdate;
