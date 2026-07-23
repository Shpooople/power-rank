import React, { useState, useEffect } from 'react';
import './app.css';  
import './header.css';  
import './explanation.css';  
import Header from './header';
import TeamSection from './teamSection';
import Explanation from './explanation';

const App = () => {
  const [teams, setTeams] = useState([]);
  const [weekLabel, setWeekLabel] = useState(null); // z.B. "Woche 13" oder "Vorsaison"
  const [historyIndex, setHistoryIndex] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null); // null = aktuelle Woche (powerrank.json)

  // Verfügbare historische Wochen laden (falls es schon welche gibt)
  useEffect(() => {
    fetch("./history/index.json")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        const entries = Array.isArray(data) ? data : [];
        // Neueste zuerst im Dropdown
        entries.sort((a, b) => (b.season - a.season) || (b.week - a.week));
        setHistoryIndex(entries);
      })
      .catch(() => setHistoryIndex([]));
  }, []);

  // Daten laden - entweder die aktuelle Woche oder eine ausgewählte historische Woche
  useEffect(() => {
    const url = selectedFile ? `./history/${selectedFile}` : "./powerrank.json";
    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        console.log("Fetched data:", data); // Log data for debugging

        // Sort teams by POWER RANK in descending order
        const sorted = data.sort((a, b) => b["POWER RANK"] - a["POWER RANK"]);

        // Filter teams to only show those ranked from 12 to 1
        const filteredTeams = sorted.filter(team => team["POWER RANK"] >= 1 && team["POWER RANK"] <= 12);

        if (filteredTeams.length > 0) {
          // Das Script liefert jetzt ein eindeutiges Anzeige-Label direkt mit,
          // statt es fragil aus der Anzahl der Week-Spalten abzuleiten.
          setWeekLabel(filteredTeams[0]["DISPLAY_WEEK_LABEL"] || null);
        } else {
          console.error("No teams available.");
        }

        // Set sorted and filtered teams in state
        setTeams(filteredTeams);
      })
      .catch((error) => {
        console.error("Error fetching JSON data:", error);
      });
  }, [selectedFile]);

  return (
    <div className="App">
      {/* Pass the week label und die History-Auswahl an die Header-Komponente */}
      <Header
        weekLabel={weekLabel}
        historyIndex={historyIndex}
        selectedFile={selectedFile}
        onSelectFile={setSelectedFile}
      />

      {teams.map((team, index) => (
        <TeamSection key={index} team={team} />
      ))}

      <Explanation />
    </div>
  );
};

export default App;
