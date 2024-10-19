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
              theta: ['QB', 'RB', 'WR', 'TE', 'K',],
              fill: 'toself',
              line: {
                color: '#153448',  // Change the line color (e.g., orange-red)
                width: 3           // Optional: set the line width
              },
             // text: [qbStrength, rbStrength, wrStrength, teStrength, kStrength],  // Display the values
             // textposition: 'right',  // Position the text at the top of each point
              // textfont: {
                  //  family: 'Arial, sans-serif',  // Change the font family
                   // size: 16,                    // Change the font size
                   // color: '#000',               // Change the text color
                   // weight: 'bold'               // Make the text bold
                 // },
              mode: 'lines+markers+text',  // Show markers, lines, and text
              marker: { size: 10 },  // Customize marker size
              connectgaps: true,
              line_close: true
            }]}
            layout={{ 
                  title: {
                  text: 'AKTUELLE TEAMSTÄRKE',  // Title text
                        font: {
                        family: 'Roboto, sans-serif',  // Font family for the title
                        weight: 'bold',
                        size: 16,                    // Font size for the title
                        color: '#153448'
                              }
                         },         
              polar: { radialaxis: { 
                visible: true, 
                range: [0, 100],
                showticklabels: true,
                color: '#3C5B6F',
                ticks: '',
                tickfont: {
                  family: 'Roboto, sans-serif',  // Customize tick font family
                  size: 12,
                  weight: 'bold',                     // Customize tick font size
                  color: '#222831'                 // Customize tick font color
                },  
              }, 
              angularaxis:{
                rotation: 90,
                color: '#153448',
                tickfont: {
                  family: 'Roboto, sans-serif',  // Customize theta label font family
                  weight: 'bold',
                  size: 12,                      // Customize theta label font size
                  color: '#222831'               // Customize theta label font color
                }
              }

              },
              showlegend: false,
    margin: {
      l: 30, // Reduce left margin
      r: 30, // Reduce right margin
      t: 60, // Reduce top margin
      b: -20  // Reduce bottom margin
    },
        // Transition settings for initial animation

              }}
  config={{
    displayModeBar: false, // This hides the mode bar while keeping hover functionality
    staticPlot: true
  }}
          
          />
          {/* Line Chart */}
          <Plot
  data={[{
    type: 'scatter',
    y: Object.values(weekData), // Week scores (use data from Week 1, Week 2, etc.)

                  line: {
                     color: '#153448',  // Change the line color (e.g., orange-red)
                     width: 3           // Optional: set the line width
                   },
              mode: 'lines+markers+text',  // Show markers, lines, and text
              marker: { size: 10 },  // Customize marker size
  }]}
  layout={{
    title: {
      text: 'SAISONVERLAUF',  // Title text
      font: {
        family: 'Arial, sans-serif',  // Font family for the title
        weight: 'bold',
        size: 16,                    // Font size for the title
        color: '#153448'                 // Font color for the title
      }
    },
    xaxis: { 
      title: '',
      showgrid:false,
      zeroline: false,
      tickvals: Object.keys(weekData).map((key, index) => index ),  // Custom tick values (1, 2, 3, ...)
      ticktext: Object.keys(weekData).map((key, index) => index + 1),
        tickfont: {
        family: 'Roboto, sans-serif',  // Customize tick font family
        size: 12,
        weight: 'bold',                     // Customize tick font size
        color: '#222831'                 // Customize tick font color
        }, 
    },
    yaxis: { 
      title: '',
      zeroline: false,
      showticklabels: true,
        tickfont: {
        family: 'Roboto, sans-serif',  // Customize tick font family
        size: 12,
        weight: 'bold',                     // Customize tick font size
        color: '#222831'                 // Customize tick font color
        }, 
    },
    height: 300,
    margin: {
      l: 30, // Reduce left margin
      r: 20, // Reduce right margin
      t: 30, // Reduce top margin
      b: -30  // Reduce bottom margin
    },

  }}
  config={{
    displayModeBar: false, // This hides the mode bar while keeping hover functionality
    staticPlot: true
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
