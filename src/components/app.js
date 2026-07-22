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

  useEffect(() => {
    // Fetch JSON data
    fetch("./powerrank.json")
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
  }, []);

  return (
    <div className="App">
      {/* Pass the week label to the Header */}
      <Header weekLabel={weekLabel} />
      
      {teams.map((team, index) => (
        <TeamSection key={index} team={team} />
      ))}

      <Explanation />
    </div>
  );
};

export default App;
