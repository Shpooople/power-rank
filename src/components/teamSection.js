import React from 'react';
import Plot from 'react-plotly.js';
import './teamSection.css';  // Import the stylesheet

// Kleine Helfer-Komponente für eine einzelne Spieler-Karte
// (wird für Top-Performer, Flop-Performer und Benchwarmer wiederverwendet)
const PlayerCard = ({ player, note }) => {
  if (!player) return null;
  const statLine = formatPositionStats(player.position, player, { showTotal: false });
  return (
    <div className="performer-card">
      <img
        src={player.image_url}
        alt={player.name}
        className="performer-image"
        onError={(e) => { e.target.src = './thf_color.svg'; }}
      />
      <div className="performer-details">
        <span className="performer-name">{player.name}</span>
        <span className="performer-meta">
          {player.position ? `${player.position} · ` : ''}{player.points} Pkt. diese Woche
          {note ? ` (${note})` : ''}
        </span>
        {statLine && <span className="performer-stats">{statLine}</span>}
      </div>
    </div>
  );
};

const outcomeClass = (outcome) => {
  if (outcome === 'Sieg') return 'outcome-win';
  if (outcome === 'Niederlage') return 'outcome-loss';
  return 'outcome-tie';
};

// Baut die Stat-Zeile je nach Position (QB/RB/WR bekommen Detail-Stats,
// TE/K nur Name+Bild ohne Zusatzstats)
const formatPositionStats = (pos, p, { showTotal = true } = {}) => {
  const totalSuffix = showTotal ? ` · ${p.total_pts} Pkt.` : '';
  if (pos === 'QB') {
    return `${p.comp}/${p.att} Cmp · ${p.pass_yd} Pass-Yds · ${p.rush_yd} Rush-Yds · ${p.td} TD${totalSuffix}`;
  }
  if (pos === 'RB') {
    return `${p.att} Att · ${p.yd} Yds · ${p.ypc} YPC · ${p.td} TD${totalSuffix}`;
  }
  if (pos === 'WR' || pos === 'TE') {
    return `${p.targets} Tgts · ${p.catches} Rec · ${p.yd} Yds · ${p.td} TD${totalSuffix}`;
  }
  if (pos === 'K') {
    return `${p.fgm}/${p.fga} FG · ${p.xpm}/${p.xpa} XP${totalSuffix}`;
  }
  if (pos === 'DEF') {
    return `${p.sack} Sacks · ${p.int} INT · ${p.fum_rec} FumRec · ${p.td} TD${totalSuffix}`;
  }
  return null;
};

// Eine Positionsgruppe im Roster (z.B. alle WR eines Teams)
const RosterPositionGroup = ({ label, players }) => {
  if (!players || players.length === 0) return null;
  return (
    <div className="roster-position-group">
      <h4 className="roster-position-label">{label}</h4>
      {players.map((p, i) => {
        const statLine = formatPositionStats(label, p);
        return (
          <div className="roster-player-row" key={i}>
            <img
              src={p.image_url}
              alt={p.name}
              className="roster-player-image"
              onError={(e) => { e.target.src = './thf_color.svg'; }}
            />
            <div className="roster-player-details">
              <span className="roster-player-name">{p.name}</span>
              {statLine && <span className="roster-player-stats">{statLine}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// Dark-Theme-Farben für die Plotly-Charts (müssen hier als JS-Werte stehen,
// da Plotly keine CSS-Variablen versteht)
const CHART_COLORS = {
  accent: '#D4A657',
  text: '#E8EDF2',
  textMuted: '#8FA3B8',
  grid: '#2A3F55',
  surface: '#1E3349',
};

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
    // Roster-Felder: jetzt Arrays mit {name, image_url, ...stats} statt Strings
    "QB": qb = [],
    "RB": rb = [],
    "WR": wr = [],
    "TE": te = [],
    "K": k = [],
    "DEF": def_ = [],
    "QB Strength": qbStrength,
    "RB Strength": rbStrength,
    "WR Strength": wrStrength,
    "TE Strength": teStrength,
    "K Strength": kStrength,
    "COMMENTS": comment,
    // Performer-Felder
    "TOP_PERFORMERS": topPerformers = [],
    "BOTTOM_PERFORMERS": bottomPerformers = [],
    "BENCHWARMER": benchwarmer,
    // Gegner-Felder (müssen hier destrukturiert werden, sonst landen sie
    // versehentlich im Wochenpunkte-Chart-Objekt weiter unten!)
    "LAST_WEEK_OPPONENT": lastWeekOpponent,
    "LAST_WEEK_RESULT": lastWeekResult,
    "THIS_WEEK_OPPONENT": thisWeekOpponent,
    "THIS_WEEK_WIN_PROB": thisWeekWinProb,
    "DISPLAY_WEEK_LABEL": displayWeekLabel,
    // Add week-wise data if needed
    ...weekData // This will spread the remaining week data into an object


  } = team;

  // NEU: ersten Punkt am Ende wiederholen, damit sich das Pentagon schließt
  const radarR = [qbStrength, rbStrength, wrStrength, teStrength, kStrength, qbStrength];
  const radarTheta = ['QB', 'RB', 'WR', 'TE', 'K', 'QB'];

  return (
    <div className="team-section">

      <div className="team-header-row">
        <span className="rank-badge">#{team["POWER RANK"]}</span>
        <h2 className="team-title">{name === "No Team Name" ? displayName : name}</h2>
      </div>
      <p>
        <strong>Record:</strong> {wins}-{losses} | 
        Trend: <span className={`trend-${trend.toLowerCase()}`}>
          {trend === 'UP' ? '↑' : trend === 'DOWN' ? '↓' : '-'}
        </span> | AAvg.: {adjustedAvg}
      </p>

      {(lastWeekResult || thisWeekOpponent) && (
        <div className="matchup-info">
          {lastWeekResult && (
            <p>
              <strong>Letzte Woche</strong> vs. {lastWeekOpponent}: {' '}
              <span className={outcomeClass(lastWeekResult.outcome)}>
                {lastWeekResult.outcome}
              </span>
              {' '}({lastWeekResult.own_points} : {lastWeekResult.opponent_points})
            </p>
          )}
          {thisWeekOpponent && (
            <p>
              <strong>Diese Woche:</strong> {thisWeekOpponent}
              {thisWeekWinProb != null && (
                <span className="win-prob"> · {thisWeekWinProb}% Gewinnchance</span>
              )}
            </p>
          )}
        </div>
      )}

      <div className="team-overview">
        <div className="team-text">
          <p>{comment}</p>
        </div>

        <div className="charts-container">
          {/* Radar Chart */}
          <Plot
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
            data={[{
              type: 'scatterpolar',
              r: radarR,
              theta: radarTheta,
              fill: 'toself',
              fillcolor: 'rgba(212, 166, 87, 0.25)',
              line: {
                color: CHART_COLORS.accent,
                width: 3
              },
              mode: 'lines+markers',
              marker: {
                size: 9,
                color: CHART_COLORS.accent,
                line: { color: CHART_COLORS.surface, width: 2 }
              },
              connectgaps: true,
              hovertemplate: '%{theta}: %{r}/100<extra></extra>'
            }]}
            layout={{
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              hovermode: 'closest',
              hoverlabel: {
                bgcolor: CHART_COLORS.surface,
                bordercolor: CHART_COLORS.accent,
                font: { color: CHART_COLORS.text, family: 'Roboto, sans-serif', size: 13 }
              },
              title: {
                text: 'AKTUELLE TEAMSTÄRKE',
                y: 0.98,
                yanchor: 'top',
                pad: { t: 10 },
                font: {
                  family: 'Roboto, sans-serif',
                  weight: 'bold',
                  size: 16,
                  color: CHART_COLORS.text
                }
              },
              polar: {
                bgcolor: 'transparent',
                radialaxis: {
                  visible: true,
                  range: [0, 100],
                  showticklabels: true,
                  gridcolor: CHART_COLORS.grid,
                  linecolor: CHART_COLORS.grid,
                  ticks: '',
                  tickfont: {
                    family: 'Roboto, sans-serif',
                    size: 12,
                    weight: 'bold',
                    color: CHART_COLORS.textMuted
                  }
                },
                angularaxis: {
                  rotation: 90,
                  gridcolor: CHART_COLORS.grid,
                  linecolor: CHART_COLORS.grid,
                  tickfont: {
                    family: 'Roboto, sans-serif',
                    weight: 'bold',
                    size: 12,
                    color: CHART_COLORS.text
                  }
                }
              },
              showlegend: false,
              height: 350,
              margin: {
                l: 30,
                r: 30,
                t: 70,
                b: 20
              },
            }}
            config={{
              displayModeBar: false,
              responsive: true
            }}
          />
          {/* Line Chart */}
          <Plot
            useResizeHandler={true}
            style={{ width: '100%', height: '100%' }}
            data={[{
              type: 'scatter',
              x: Object.keys(weekData).map((key, index) => index + 1),
              y: Object.values(weekData),
              line: {
                color: CHART_COLORS.accent,
                width: 3
              },
              mode: 'lines+markers',
              marker: {
                size: 9,
                color: CHART_COLORS.accent,
                line: { color: CHART_COLORS.surface, width: 2 }
              },
              hovertemplate: 'Woche %{x}<br>%{y} Punkte<extra></extra>'
            }]}
            layout={{
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              hovermode: 'closest',
              hoverlabel: {
                bgcolor: CHART_COLORS.surface,
                bordercolor: CHART_COLORS.accent,
                font: { color: CHART_COLORS.text, family: 'Roboto, sans-serif', size: 13 }
              },
              title: {
                text: 'SAISONVERLAUF',
                font: {
                  family: 'Arial, sans-serif',
                  weight: 'bold',
                  size: 16,
                  color: CHART_COLORS.text
                }
              },
              xaxis: {
                title: '',
                showgrid: false,
                zeroline: false,
                dtick: 1,
                tickfont: {
                  family: 'Roboto, sans-serif',
                  size: 12,
                  weight: 'bold',
                  color: CHART_COLORS.textMuted
                },
                linecolor: CHART_COLORS.grid
              },
              yaxis: {
                title: '',
                zeroline: false,
                showticklabels: true,
                gridcolor: CHART_COLORS.grid,
                tickfont: {
                  family: 'Roboto, sans-serif',
                  size: 12,
                  weight: 'bold',
                  color: CHART_COLORS.textMuted
                },
              },
              height: 350,
              margin: {
                l: 30,
                r: 20,
                t: 30,
                b: 30
              },
            }}
            config={{
              displayModeBar: false,
              responsive: true
            }}
          />
        </div>

        {/* Roster: jetzt mit Spielerbild + Detail-Stats, ausklappbar */}
        <details className="collapsible team-roster">
          <summary>Roster anzeigen</summary>
          <div className="collapsible-content">
            <RosterPositionGroup label="QB" players={qb} />
            <RosterPositionGroup label="RB" players={rb} />
            <RosterPositionGroup label="WR" players={wr} />
            <RosterPositionGroup label="TE" players={te} />
            <RosterPositionGroup label="K" players={k} />
            <RosterPositionGroup label="DEF" players={def_} />
          </div>
        </details>
      </div>

      {(topPerformers.length > 0 || bottomPerformers.length > 0 || benchwarmer) && (
        <details className="collapsible performers-section">
          <summary>Performer der Woche anzeigen</summary>
          <div className="collapsible-content">
            {topPerformers.length > 0 && (
              <div className="performer-group">
                <h3>Top Performer der Woche</h3>
                <div className="performer-cards">
                  {topPerformers.map((p, i) => (
                    <PlayerCard key={`top-${i}`} player={p} />
                  ))}
                </div>
              </div>
            )}

            {bottomPerformers.length > 0 && (
              <div className="performer-group">
                <h3>Flop Performer der Woche</h3>
                <div className="performer-cards">
                  {bottomPerformers.map((p, i) => (
                    <PlayerCard key={`bottom-${i}`} player={p} />
                  ))}
                </div>
              </div>
            )}

            {benchwarmer && (
              <div className="performer-group">
                <h3>Benchwarmer der Woche</h3>
                <div className="performer-cards">
                  <PlayerCard player={benchwarmer} note="Bank" />
                </div>
              </div>
            )}
          </div>
        </details>
      )}
    </div>
  );
};

export default TeamSection;
