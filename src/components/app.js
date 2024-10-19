import React, { useState, useEffect } from 'react';
import './app.css';  
import './header.css';  
import './explanation.css';  
import Header from './header';
import TeamSection from './teamSection';
import Explanation from './explanation';

const App = () => {
  const [teams, setTeams] = useState([]);
  const [currentWeek, setCurrentWeek] = useState(null); // Track the current week

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
          const firstTeam = filteredTeams[0];

          // Extract keys that represent weeks (those starting with "Week")
          const weekKeys = Object.keys(firstTeam).filter(key => key.startsWith("Week"));

          console.log("Week Keys:", weekKeys); // Debugging log to ensure correct week keys are being picked up

          // Set the current week to be numberOfWeeks + 1
          setCurrentWeek(weekKeys.length + 1); // Current week is the last one + 1
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
      {/* Pass the current week to the Header */}
      <Header currentWeek={currentWeek} />
      
      {teams.map((team, index) => (
        <TeamSection key={index} team={team} />
      ))}

      <Explanation />
    </div>
  );
};

export default App;
