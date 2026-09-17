import React, { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';
import './LeagueStats.css';

const METRICS = [
  { key: 'rank', label: 'Rang' },
  { key: 'points', label: 'Points Scored' },
  { key: 'against', label: 'Points Against' },
  { key: 'waiver', label: 'Waiver Moves' },
  { key: 'injuries', label: 'Injuries' },
];

// Feste, stabile Farbpalette - jedes Team bekommt seine Farbe über die
// (immer gleiche) Reihenfolge der User IDs zugewiesen, damit die Farbe
// unabhängig von der aktuellen Sortierung/Platzierung immer gleich bleibt.
const TEAM_COLOR_PALETTE = [
  '#5FD3F3', '#4FD9D0', '#4FD9A8', '#6BD96B', '#9CD95C', '#C7D95C',
  '#D9D95C', '#D4A657', '#E08E45', '#E37A45', '#E2665B', '#B93A34',
  '#A374D9', '#D974B8',
];

const teamLabel = (team) => (team["Team Name"] === "No Team Name" ? team["Display Name"] : team["Team Name"]);

const CHART_COLORS = {
  text: '#E8EDF2',
  textMuted: '#8FA3B8',
  grid: '#2A3F55',
  surface: '#1E3349',
  accent: '#D4A657',
};

const LeagueStats = ({ teams, historyIndex }) => {
  const [open, setOpen] = useState(false);
  const [metric, setMetric] = useState('rank');
  const [hiddenTeams, setHiddenTeams] = useState([]); // User IDs, die ausgeblendet sind
  const [historyData, setHistoryData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const allUserIds = useMemo(() => (teams || []).map((t) => t["User ID"]), [teams]);

  const colorForUser = (userId) => {
    const idx = allUserIds.indexOf(userId);
    return TEAM_COLOR_PALETTE[idx % TEAM_COLOR_PALETTE.length];
  };

  // Historische Wochen laden (für Rang & Injuries, da die nicht als
  // "Week N"-Spalten in der aktuellen Datei stecken) - erst, sobald die
  // Liga-Statistik tatsächlich aufgeklappt wird, um unnötige Requests zu
  // vermeiden.
  useEffect(() => {
    if (!open || historyData.length > 0 || loadingHistory) return;
    if (!historyIndex || historyIndex.length === 0) return;
    setLoadingHistory(true);
    Promise.all(
      historyIndex.map((entry) =>
        fetch(`./history/${entry.file}`)
          .then((res) => (res.ok ? res.json() : null))
          .then((data) => ({ week: entry.week, teams: data }))
          .catch(() => null)
      )
    ).then((results) => {
      setHistoryData(results.filter((r) => r && Array.isArray(r.teams)));
      setLoadingHistory(false);
    });
  }, [open, historyIndex, historyData.length, loadingHistory]);

  if (!teams || teams.length === 0) return null;

  const weekKeys = Object.keys(teams[0]).filter((k) => /^Week \d+$/.test(k));
  const weekNumbers = [...new Set(weekKeys.map((k) => parseInt(k.replace('Week ', ''), 10)))].sort((a, b) => a - b);
  const currentWeekNumber = weekNumbers.length > 0 ? weekNumbers[weekNumbers.length - 1] : null;

  const findHistoryValue = (userId, week, field) => {
    const entry = historyData.find((h) => h.week === week);
    if (!entry) return undefined;
    const teamEntry = entry.teams.find((t) => t["User ID"] === userId);
    return teamEntry ? teamEntry[field] : undefined;
  };

  const toggleTeam = (userId) => {
    setHiddenTeams((prev) => (
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    ));
  };

  const visibleTeams = teams.filter((t) => !hiddenTeams.includes(t["User ID"]));

  // Traces je nach gewählter Metrik bauen. Rang wird NICHT kumulativ
  // dargestellt (macht als Rang keinen Sinn), alle anderen schon.
  const buildTrace = (team) => {
    const userId = team["User ID"];
    let y;

    if (metric === 'rank') {
      y = weekNumbers.map((w) => {
        if (w === currentWeekNumber) return team["POWER RANK"];
        const val = findHistoryValue(userId, w, "POWER RANK");
        return val != null ? val : null;
      });
    } else if (metric === 'injuries') {
      let running = 0;
      y = weekNumbers.map((w) => {
        const val = w === currentWeekNumber ? team["INJURY_COUNT"] : findHistoryValue(userId, w, "INJURY_COUNT");
        if (val == null) return null; // vor Einführung dieses Felds keine Daten
        running += val;
        return running;
      });
    } else {
      const suffix = metric === 'points' ? '' : metric === 'against' ? ' Against' : ' Waiver';
      let running = 0;
      y = weekNumbers.map((w) => {
        running += team[`Week ${w}${suffix}`] || 0;
        return running;
      });
    }

    return {
      x: weekNumbers,
      y,
      type: 'scatter',
      mode: 'lines+markers',
      name: teamLabel(team),
      line: { color: colorForUser(userId), width: 2.5 },
      marker: { color: colorForUser(userId), size: 6 },
      connectgaps: false,
    };
  };

  const traces = visibleTeams.map(buildTrace);
  const currentMetric = METRICS.find((m) => m.key === metric);

  return (
    <details className="league-stats-section" onToggle={(e) => setOpen(e.target.open)}>
      <summary>Liga Statistik anzeigen</summary>
      <div className="league-stats-content">
        <div className="league-stats-metric-buttons">
          {METRICS.map((m) => (
            <button
              type="button"
              key={m.key}
              className={`league-stats-metric-btn${metric === m.key ? ' active' : ''}`}
              onClick={() => setMetric(m.key)}
            >
              {m.label}
            </button>
          ))}
        </div>

        {metric === 'injuries' && (
          <p className="league-stats-note">
            Hinweis: Verletzungsstatus wird nur aktuell erfasst, nicht rückwirkend - diese Kurve wächst
            deshalb erst ab der Einführung dieses Features Woche für Woche mit.
          </p>
        )}

        {loadingHistory && (metric === 'rank' || metric === 'injuries') && (
          <p className="league-stats-note">Lade Wochen-Historie...</p>
        )}

        <div className="league-stats-layout">
          <div className="league-stats-chart-wrapper">
            <Plot
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              data={traces}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                dragmode: false,
                hovermode: 'closest',
                showlegend: false,
                hoverlabel: {
                  bgcolor: CHART_COLORS.surface,
                  bordercolor: CHART_COLORS.accent,
                  font: { color: CHART_COLORS.text, family: 'Roboto, sans-serif', size: 12 }
                },
                xaxis: {
                  title: 'Woche',
                  tickvals: weekNumbers,
                  showgrid: false,
                  fixedrange: true,
                  tickfont: { family: 'Roboto, sans-serif', size: 12, color: '#5FD3F3' },
                  linecolor: CHART_COLORS.grid,
                },
                yaxis: {
                  title: currentMetric ? currentMetric.label : '',
                  autorange: metric === 'rank' ? 'reversed' : true,
                  gridcolor: CHART_COLORS.grid,
                  fixedrange: true,
                  tickfont: { family: 'Roboto, sans-serif', size: 12, color: '#5FD3F3' },
                },
                margin: { l: 50, r: 20, t: 10, b: 40 },
                height: 380,
              }}
              config={{ displayModeBar: false, responsive: true, scrollZoom: false, doubleClick: false }}
            />
          </div>

          <div className="league-stats-team-filter">
            <span className="league-stats-team-filter-title">Teams</span>
            {teams.map((t) => {
              const userId = t["User ID"];
              const isHidden = hiddenTeams.includes(userId);
              return (
                <button
                  type="button"
                  key={userId}
                  className={`league-stats-team-toggle${isHidden ? ' hidden' : ''}`}
                  onClick={() => toggleTeam(userId)}
                >
                  <span
                    className="league-stats-team-swatch"
                    style={{ backgroundColor: colorForUser(userId) }}
                  />
                  {teamLabel(t)}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </details>
  );
};

export default LeagueStats;
