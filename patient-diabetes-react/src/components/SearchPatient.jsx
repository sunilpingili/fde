import { useState } from "react";
import RiskBadge from "./RiskBadge";

const API_URL = "http://localhost:8004";

function formatUtc(isoString) {
  if (!isoString) return "—";
  const d = new Date(isoString);
  return d.toLocaleString("en-US", {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "UTC", timeZoneName: "short",
  });
}

function SearchPatient({ onSelectEncounter }) {
  const [patientNbr, setPatientNbr] = useState("");
  const [riskLevel,  setRiskLevel]  = useState("");
  const [riskScore,  setRiskScore]  = useState("");
  const [results,    setResults]    = useState([]);
  const [searched,   setSearched]   = useState(false);
  const [loading,    setLoading]    = useState(false);
  const [error,      setError]      = useState(null);

  async function handleSearch() {
    const params = new URLSearchParams();
    if (patientNbr) params.append("patient_nbr", patientNbr);
    if (riskLevel)  params.append("risk_level",  riskLevel);
    if (riskScore)  params.append("risk_score",  riskScore);
    params.append("limit", "100");

    setLoading(true);
    setError(null);
    setSearched(false);

    try {
      const res = await fetch(`${API_URL}/encounters/search?${params}`);
      if (!res.ok) throw new Error(`Server returned ${res.status} — check that the API is running.`);
      const data = await res.json();
      setResults(data);
      setSearched(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") handleSearch();
  }

  function renderBody() {
    if (loading) {
      return (
        <div className="state-box">
          <div className="state-icon">⏳</div>
          <p>Searching encounters…</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="state-box error">
          <div className="state-icon">⚠️</div>
          <p><strong>Error:</strong> {error}</p>
        </div>
      );
    }

    if (!searched) {
      return (
        <div className="state-box">
          <div className="state-icon">🔍</div>
          <p>Enter one or more filters above and click <strong>Search</strong> to find encounters.</p>
        </div>
      );
    }

    if (results.length === 0) {
      return (
        <div className="state-box">
          <div className="state-icon">📋</div>
          <p>No encounters matched your filters. Try broadening your search.</p>
        </div>
      );
    }

    return (
      <>
        <div className="results-meta">
          <span className="count">{results.length} encounter{results.length !== 1 ? "s" : ""} found</span>
          <span>Showing up to 100 results · sorted by risk score</span>
        </div>
        <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Encounter ID</th>
              <th>Patient Number</th>
              <th>Age</th>
              <th>Risk Score</th>
              <th>Risk Level</th>
              <th>Status</th>
              <th>Last Updated (UTC)</th>
            </tr>
          </thead>
          <tbody>
            {results.map((enc) => (
              <tr key={enc.encounter_id}>
                <td className="encounter-id">
                  <button
                    className="link-btn"
                    onClick={() => onSelectEncounter(enc)}
                  >
                    {enc.encounter_id}
                  </button>
                </td>
                <td>{enc.patient_nbr}</td>
                <td>{enc.age}</td>
                <td className="score">{enc.risk_score} / 8</td>
                <td><RiskBadge level={enc.risk_level} /></td>
                <td className={enc.intervention_status ? "status-cell" : "status-none"}>
                  {enc.intervention_status ?? "—"}
                </td>
                <td className={`timestamp ${enc.intervention_updated_at ? "status-cell" : "status-none"}`}>
                  {formatUtc(enc.intervention_updated_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Patient Search</h1>
        <p className="subtitle">Find and review diabetes hospital encounters.</p>
      </div>

      <div className="card">
        {/* Search form */}
        <div className="search-panel">
          <div className="panel-title">Filter Encounters</div>
          <div className="form-grid">
            <div className="form-field">
              <label htmlFor="patientNbr">Patient Number</label>
              <input
                id="patientNbr"
                type="text"
                value={patientNbr}
                onChange={(e) => setPatientNbr(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="e.g. 84002391"
              />
            </div>

            <div className="form-field">
              <label htmlFor="riskLevel">Risk Level</label>
              <select
                id="riskLevel"
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value)}
              >
                <option value="">All levels</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor="riskScore">Min Risk Score</label>
              <input
                id="riskScore"
                type="number"
                min="0"
                max="8"
                value={riskScore}
                onChange={(e) => setRiskScore(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="0 – 8"
              />
            </div>

            <button
              className="btn-search"
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? "Searching…" : "Search"}
            </button>
          </div>
        </div>

        {/* Results / state */}
        <div className="results-panel">
          {renderBody()}
        </div>
      </div>

      <p className="disclaimer">
        Learning Prototype — Not for Clinical Use
      </p>
    </div>
  );
}

export default SearchPatient;
