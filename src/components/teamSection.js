import React, { useState, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import './teamSection.css';  // Import the stylesheet

// NEU: 12-stufige Farbskala nach Liga-Rang (Platz 1 = Hellblau, Platz 12 =
// Rot) - wird für Teamstärke-Balken, Trend UND AAvg gemeinsam genutzt.
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

// Kleines Badge-Icon mit Hover- (Desktop) bzw. Tap-Tooltip (Mobile)
const BadgeIcon = ({ badge }) => {
  const [open, setOpen] = useState(false);
  return (
    <span
      className="badge-icon"
      tabIndex={0}
      onClick={() => setOpen((o) => !o)}
      onBlur={() => setOpen(false)}
    >
      {badge.icon}
      <span className={`badge-tooltip${open ? ' badge-tooltip-open' : ''}`}>
        <strong>{badge.label}</strong>
        <br />
        {badge.description}
      </span>
    </span>
  );
};

// Kleine Helfer-Komponente für die Trend-Anzeige (Dreieck + fetter Wert,
// eingefärbt nach Liga-Rang des Trends)
const TrendIndicator = ({ value, rank }) => {
  const isUp = value >= 0;
  const color = colorForRank(rank);
  const sign = value > 0 ? '+' : '';
  return (
    <span style={{ color, fontWeight: 'bold' }}>
      {isUp ? '▲' : '▼'} {sign}{value}%
    </span>
  );
};

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
    // eslint-disable-next-line no-unused-vars
    "TREND": trend,
    "Trend Percentage": trenPercentage,
    "TREND Rank": trendRank,
    "Adjusted Average": adjustedAvg,
    "Adjusted Average Rank": aavgRank,
    "BADGES": badges = [],
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

  const barColors = strengthRanks.map(colorForRank);

  // NEU: Balken wachsen + Linie "fährt" sichtbar von Punkt zu Punkt, sobald
  // die Charts zum ersten Mal ins Bild scrollen (ein gemeinsamer Observer,
  // Animation läuft per requestAnimationFrame statt fester Zeitschritte -
  // dadurch flüssig statt abgehackt)
  const [barsRevealed, setBarsRevealed] = useState(false);
  const [weekProgress, setWeekProgress] = useState(0);
  const chartsContainerRef = useRef(null);

  const weekKeys = Object.keys(weekData);
  const weekValues = Object.values(weekData);

  useEffect(() => {
    const el = chartsContainerRef.current;
    if (!el) return undefined;
    let rafId;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setBarsRevealed(true);

            const totalPoints = weekValues.length;
            const segments = Math.max(totalPoints - 1, 1);
            const msPerSegment = 220; // Dauer pro "Fahrt" von Punkt zu Punkt
            const totalDuration = segments * msPerSegment;
            const startTime = performance.now();

            const step = (now) => {
              const elapsed = now - startTime;
              const progress = Math.min(elapsed / totalDuration, 1) * segments;
              setWeekProgress(progress);
              if (elapsed < totalDuration) {
                rafId = requestAnimationFrame(step);
              }
            };
            rafId = requestAnimationFrame(step);
            observer.disconnect();
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
    return () => {
      observer.disconnect();
      if (rafId) cancelAnimationFrame(rafId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const displayedStrengthValues = barsRevealed ? strengthValues : strengthValues.map(() => 0);

  // weekProgress = wie viele Segmente (Punkt-zu-Punkt-Strecken) bereits
  // "gefahren" wurden, inkl. Bruchteil für die aktuell laufende Strecke
  const totalWeekPoints = weekValues.length;
  const fullCount = Math.min(Math.floor(weekProgress) + 1, totalWeekPoints);
  const segmentFraction = weekProgress - Math.floor(weekProgress);

  const displayedWeekX = weekKeys.slice(0, fullCount).map((key, index) => index + 1);
  const displayedWeekY = weekValues.slice(0, fullCount);

  if (segmentFraction > 0 && fullCount < totalWeekPoints) {
    const prevY = weekValues[fullCount - 1];
    const nextY = weekValues[fullCount];
    displayedWeekX.push(fullCount + segmentFraction);
    displayedWeekY.push(prevY + (nextY - prevY) * segmentFraction);
  }

  const weekYMin = weekValues.length ? Math.min(...weekValues) : 0;
  const weekYMax = weekValues.length ? Math.max(...weekValues) : 100;
  const weekYPadding = (weekYMax - weekYMin) * 0.15 || 10;

  return (
    <div className="team-section">

      <div className="team-header-row">
        <span className="rank-badge">#{team["POWER RANK"]}</span>
        <h2 className="team-title">
          {name === "No Team Name" ? displayName : name}
          <span className="team-record"> ({wins}-{losses})</span>
        </h2>
      </div>

      {badges.length > 0 && (
        <div className="team-badges">
          {badges.map((badge, i) => (
            <BadgeIcon key={i} badge={badge} />
          ))}
        </div>
      )}

      <p>
        Trend: <TrendIndicator value={trenPercentage} rank={trendRank} /> | AAvg.:{' '}
        <span style={{ color: colorForRank(aavgRank), fontWeight: 'bold' }}>{adjustedAvg}</span>
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
                  autorange: false,
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
              data={[
                {
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
                },
                // NEU: unsichtbare "Geister-Spur" mit den kompletten Werten -
                // hält die Achsen-Range von Anfang an stabil, ohne autorange
                // manuell abschalten zu müssen (das hatte das Chart zum
                // Verschwinden gebracht statt nur das Flackern zu beheben)
                {
                  type: 'scatter',
                  x: weekKeys.map((key, index) => index + 1),
                  y: weekValues,
                  mode: 'markers',
                  marker: { size: 0, opacity: 0 },
                  hoverinfo: 'skip',
                  showlegend: false
                }
              ]}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                dragmode: false,
                transition: { duration: 0 },
                hovermode: 'closest',
                showlegend: false,
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
                  fixedrange: true,
                  range: [0.5, weekKeys.length + 0.5],
                  tickvals: weekKeys.map((key, index) => index + 1),
                  ticktext: weekKeys.map((key, index) => index + 1),
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
