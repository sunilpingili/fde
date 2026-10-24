import { useState } from "react";
import SearchPatient from "./components/SearchPatient";
import InterventionUpdate from "./components/InterventionUpdate";
import "./App.css";

function App() {
  const [currentPage, setCurrentPage]           = useState("search");
  const [selectedEncounter, setSelectedEncounter] = useState(null);

  function handleSelectEncounter(enc) {
    setSelectedEncounter(enc);
    setCurrentPage("intervention");
  }

  function handleBackToSearch() {
    setCurrentPage("search");
    setSelectedEncounter(null);
  }

  if (currentPage === "intervention" && selectedEncounter) {
    return (
      <InterventionUpdate
        encounter={selectedEncounter}
        onBack={handleBackToSearch}
      />
    );
  }

  return <SearchPatient onSelectEncounter={handleSelectEncounter} />;
}

export default App;
