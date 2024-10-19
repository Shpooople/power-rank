import React from 'react';
import Plot from 'react-plotly.js';
import './teamSection.css';  // Import the stylesheet

const TeamSection = ({ team }) => {

  // Adjusting to match the JSON structure
  const {
    "User ID": userID,
    "Display Name": displayName,
    "POWER RANK": powerrank,
    "Power Rank Score": powerrankscore,
    "Team Name": name,
    "Wins": wins,
    "Ties": tiesm,
    "Losses": losses,
    "Points For": pointsFor,
    "Points Against": pointsAgainst,
    "TREND": trend = 'NO TREND',
    "Trend Percentage": trenPercentage,
    "Adjusted Average": adjustedAvg,
    "QB": qb,
    "RB": rb,
    "WR": wr,
    "TE": te,
    "K": k,
    "DEF": def,
    "QB Strength": qbStrength,
    "RB Strength": rbStrength,
    "WR Strength": wrStrength,
    "TE Strength": teStrength,
    "K Strength": kStrength,
    "COMMENTS": comment,
    // Add week-wise data if needed
    ...weekData // This will spread the remaining week data into an object


  } = team;

  return (
    <div className="team-section">

      <h2>Rank {team["POWER RANK"]} - {name==="No Team Name" ?displayName:name}</h2>
      <p>
        <strong>Record:</strong> {wins}-{losses} | 
        Trend: <span className={`trend-${trend.toLowerCase()}`}>
          {trend === 'UP' ? '↑' : trend === 'DOWN' ? '↓' : '-'}
        </span> | AAvg.: {adjustedAvg}
      </p>

      <div className="team-overview">
        <div className="team-text">
          <p>{comment}</p>
        </div>

        <div className="charts-container">
          {/* Radar Chart */}
          <Plot
            data={[{
              type: 'scatterpolar',
              r: [qbStrength, rbStrength, wrStrength, teStrength, kStrength],
              theta: ['QB', 'RB', 'WR', 'TE', 'K'],
              fill: 'toself'
            }]}
            layout={{ 
                  title: {
      text: 'Aktuelle Teamstärke',  // Title text
      font: {
        family: 'Arial, sans-serif',  // Font family for the title
        size: 20,                    // Font size for the title
        color: '#333'
        }
        },         
              polar: { radialaxis: { visible: true, range: [0, 100] } },
              showlegend: false,
    margin: {
      l: 10, // Reduce left margin
      r: 30, // Reduce right margin
      t: 50, // Reduce top margin
      b: -20  // Reduce bottom margin
    }
              }}
  config={{
    displayModeBar: false // This hides the mode bar while keeping hover functionality
  }}
          
          />
          {/* Line Chart */}
          <Plot
  data={[{
    type: 'scatter',
    y: Object.values(weekData) // Week scores (use data from Week 1, Week 2, etc.)
  }]}
  layout={{
    title: {
      text: 'Saisonverlauf',  // Title text
      font: {
        family: 'Arial, sans-serif',  // Font family for the title
        size: 20,                    // Font size for the title
        color: '#333'                 // Font color for the title
      }
    },
    xaxis: { title: 'Wochen' },
    yaxis: { title: '' },
    height: 300,
    margin: {
      l: 30, // Reduce left margin
      r: 20, // Reduce right margin
      t: 30, // Reduce top margin
      b: -30  // Reduce bottom margin
    }
  }}
  config={{
    displayModeBar: false // This hides the mode bar while keeping hover functionality
  }}
  /* Properly close the Plot component here with /> */
  />
        </div>
        <div className="team-roster">
          <table>
            <thead>
              <tr>
                <th>QB</th>
                <th>RB</th>
                <th>WR</th>
                <th>TE</th>
                <th>K</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>{qb}</td>
                <td>{rb}</td>
                <td>{wr}</td>
                <td>{te}</td>
                <td>{k}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TeamSection;
