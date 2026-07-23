import React, { useState, useEffect, useRef } from 'react';
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
    "QB Strength Rank": qbRank,
    "RB Strength Rank": rbRank,
    "WR Strength Rank": wrRank,
    "TE Strength Rank": teRank,
    "K Strength Rank": kRank,
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

  // NEU: Bar-Chart statt Pentagon - Kategorien, Werte, Ränge und Farbcodierung
  const strengthCategories = ['QB', 'RB', 'WR', 'TE', 'K'];
  const strengthValues = [qbStrength, rbStrength, wrStrength, teStrength, kStrength];
  const strengthRanks = [qbRank, rbRank, wrRank, teRank, kRank];

  // NEU: 12-stufige Farbskala nach Liga-Rang (Platz 1 = Hellblau, Platz 12 =
  // Rot), nicht nach absolutem Wert - Rang 1 ist immer der höchste Balken.
  const RANK_COLOR_SCALE = [
    '#5FD3F3', // Platz 1 - Hellblau
    '#4FD9D0', // Platz 2 - Türkis
    '#4FD9A8', // Platz 3 - grünliches Türkis
    '#6BD96B', // Platz 4 - Grün
    '#9CD95C', // Platz 5
    '#C7D95C', // Platz 6
    '#D9D95C', // Platz 7 - Gelb
    '#D4A657', // Platz 8 - Gold
    '#E08E45', // Platz 9 - Orange
    '#E37A45', // Platz 10
    '#E2665B', // Platz 11 - Rot-Orange
    '#B93A34', // Platz 12 - Rot
  ];

  const colorForRank = (rank) => {
    const idx = Math.min(Math.max(rank, 1), RANK_COLOR_SCALE.length) - 1;
    return RANK_COLOR_SCALE[idx];
  };

  const barColors = strengthRanks.map(colorForRank);

  // NEU: Balken wachsen + Linie zeichnet sich Woche für Woche, sobald die
  // Charts zum ersten Mal ins Bild scrollen (ein gemeinsamer Observer)
  const [barsRevealed, setBarsRevealed] = useState(false);
  const [lineRevealCount, setLineRevealCount] = useState(0);
  const chartsContainerRef = useRef(null);

  const weekKeys = Object.keys(weekData);
  const weekValues = Object.values(weekData);

  useEffect(() => {
    const el = chartsContainerRef.current;
    if (!el) return undefined;
    let interval;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setBarsRevealed(true);
            let count = 0;
            interval = setInterval(() => {
              count += 1;
              setLineRevealCount(count);
              if (count >= weekKeys.length) {
                clearInterval(interval);
              }
            }, 120);
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      if (interval) clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const displayedStrengthValues = barsRevealed ? strengthValues : strengthValues.map(() => 0);

  const displayedWeekX = weekKeys.slice(0, lineRevealCount).map((key, index) => index + 1);
  const displayedWeekY = weekValues.slice(0, lineRevealCount);
  const weekYMin = weekValues.length ? Math.min(...weekValues) : 0;
  const weekYMax = weekValues.length ? Math.max(...weekValues) : 100;
  const weekYPadding = (weekYMax - weekYMin) * 0.15 || 10;

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

        <div className="charts-container" ref={chartsContainerRef}>
          {/* Positionsstärke als farbcodierter Bar-Chart */}
          <div className="chart-touch-wrapper">
            <Plot
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              data={[{
                type: 'bar',
                x: strengthCategories,
                y: displayedStrengthValues,
                customdata: strengthRanks,
                marker: { color: barColors },
                hovertemplate: '<b>%{x}</b><br>Wert: %{y}/100<br>Rang %{customdata} von 12<extra></extra>'
              }]}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                dragmode: false,
                transition: { duration: 800, easing: 'cubic-in-out' },
                hovermode: 'closest',
                hoverlabel: {
                  bgcolor: CHART_COLORS.surface,
                  bordercolor: CHART_COLORS.accent,
                  font: { color: CHART_COLORS.text, family: 'Roboto, sans-serif', size: 13 }
                },
                title: {
                  text: 'AKTUELLE TEAMSTÄRKE',
                  font: {
                    family: 'Roboto, sans-serif',
                    weight: 'bold',
                    size: 16,
                    color: CHART_COLORS.text
                  }
                },
                xaxis: {
                  fixedrange: true,
                  tickfont: {
                    family: 'Roboto, sans-serif',
                    weight: 'bold',
                    size: 13,
                    color: CHART_COLORS.text
                  },
                  linecolor: CHART_COLORS.grid
                },
                yaxis: {
                  fixedrange: true,
                  range: [0, 100],
                  gridcolor: CHART_COLORS.grid,
                  tickfont: {
                    family: 'Roboto, sans-serif',
                    size: 12,
                    color: CHART_COLORS.textMuted
                  }
                },
                showlegend: false,
                height: 350,
                margin: {
                  l: 30,
                  r: 20,
                  t: 50,
                  b: 30
                },
              }}
              config={{
                displayModeBar: false,
                responsive: true,
                scrollZoom: false,
                doubleClick: false
              }}
            />
          </div>
          {/* Line Chart */}
          <div className="chart-touch-wrapper">
            <Plot
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              data={[{
                type: 'scatter',
                x: displayedWeekX,
                y: displayedWeekY,
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
                dragmode: false,
                transition: { duration: 150, easing: 'linear' },
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
                  fixedrange: true,
                  range: [0.5, weekKeys.length + 0.5],
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
                  fixedrange: true,
                  range: [Math.max(0, weekYMin - weekYPadding), weekYMax + weekYPadding],
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
                responsive: true,
                scrollZoom: false,
                doubleClick: false
              }}
            />
          </div>
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
