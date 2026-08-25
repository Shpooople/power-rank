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

// NEU: kleiner farbiger Kreis-Chip mit Rangzahl - für die Legacy-Stats,
// statt reinem "· Rang X"-Text
const RankChip = ({ rank }) => {
  if (rank == null) return null;
  return (
    <span className="rank-chip" style={{ backgroundColor: colorForRank(rank) }}>
      #{rank}
    </span>
  );
};

// NEU: Platzierungs-Historie als kleine Pokal-Reihe (Top 3 als Medaille,
// Rest als Zahl-Chip)
const PLACE_MEDALS = { 1: '🥇', 2: '🥈', 3: '🥉' };
const PlacementRow = ({ placements }) => (
  <div className="placement-row">
    {placements.map((pl, i) => (
      <span className="placement-chip" key={i}>
        <span className="placement-medal">{PLACE_MEDALS[pl.place] || `#${pl.place}`}</span>
        <span className="placement-season">{pl.season}</span>
      </span>
    ))}
  </div>
);

// NEU: kleine Chip-Reihe für Pro-Saison-Aufschlüsselungen (z.B. Punkte oder
// Waiver-Moves pro Saison) - wiederverwendbar über valueKey
const SeasonBreakdownRow = ({ items, valueKey }) => (
  <div className="season-breakdown-row">
    {items.map((item, i) => (
      <span className="season-breakdown-chip" key={i}>
        <span className="season-breakdown-season">{item.season}</span>
        <span className="season-breakdown-value">{item[valueKey]}</span>
      </span>
    ))}
  </div>
);

// NEU: dunklere, aber farblich ähnliche Variante einer Hex-Farbe - für die
// Bank-Balken (Team-Depth), damit sie zum jeweiligen Positions-Balken passen
// NEU: dunklere, aber farblich ähnliche Variante einer Hex-Farbe, mit
// einstellbarer Transparenz - für das Fade-in der Zahlen in den
// Positionsstärke-Balken
const darkenColorAlpha = (hex, amount, alpha) => {
  const h = hex.replace('#', '');
  const r = Math.round(parseInt(h.substring(0, 2), 16) * (1 - amount));
  const g = Math.round(parseInt(h.substring(2, 4), 16) * (1 - amount));
  const b = Math.round(parseInt(h.substring(4, 6), 16) * (1 - amount));
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

// NEU: Farbverlauf für den Saisonverlauf-Chart, entlang derselben Skala wie
// die Positionsstärke (rot = wenig Punkte, blau = viele Punkte) - t=0..1
// bezogen auf das jeweils EIGENE Min/Max der Saison eines Teams (individuelle
// Skala bleibt erhalten, nur die Farbe macht den Vergleich zwischen Teams
// auf den ersten Blick erkennbar).
// NEU: Farbverlauf im Saisonverlauf - anders als die individuelle Y-Achsen-
// Skala (die bleibt pro Team unterschiedlich) ist die FARBE jetzt an feste,
// liga-weite Punktbereiche gekoppelt, damit Farben zwischen verschiedenen
// Team-Karten direkt vergleichbar sind (60 Punkte sind immer rot, egal bei
// welchem Team).
const LEAGUE_POINT_BANDS = [
  { max: 80, color: '#B93A34' },       // unter 80: Rot
  { max: 100, color: '#E2665B' },      // 80-100: Rot-Orange
  { max: 120, color: '#D4A657' },      // 100-120: Gelb-Orange
  { max: 140, color: '#9CD95C' },      // 120-140: Gelb-Grün
  { max: 160, color: '#6BD96B' },      // 140-160: Grün
  { max: Infinity, color: '#4FD9D0' }, // ab 160: Türkis
];

const colorForLeaguePoints = (v) => {
  const band = LEAGUE_POINT_BANDS.find((b) => v < b.max);
  return band ? band.color : LEAGUE_POINT_BANDS[LEAGUE_POINT_BANDS.length - 1].color;
};

// Emoji-Zuordnung je Badge-Code (Script liefert Codes statt Emojis direkt,
// damit Homer-Badges zusätzlich ein image_url-Feld fürs Team-Logo haben können)
const BADGE_EMOJIS = {
  hospital: '🩹',
  homer: '🏟️',
  unlucky: '🍀',
  rising: '📈',
  falling: '📉',
  giant_killer: '💥',
  clutch: '🦷',
  fire: '🔥',
  cold: '🥶',
  rollercoaster: '🎢',
  consistent: '⚓',
  bench: '🪑',
  crown: '👑',
  blunder: '🤡',
  perfect: '🥇',
  bigbang: '💣',
  bust: '🫠',
  dragon: '🐉',
  lock: '🔒',
  wizard: '🎣',
  superfan: '🏟️',
  airraid: '🎯',
  groundpound: '🚜',
  touchdown: '🏈',
  egg: '🥚',
  footboot: '👢',
  money: '💰',
  ruin: '🏚️',
  shield: '🛡️',
  hammer: '🔨',
  kindergarten: '🧸',
  oldfolks: '🦖',
};

// Kleines Badge-Icon mit Hover- (Desktop) bzw. Tap-Tooltip (Mobile)
const BadgeIcon = ({ badge }) => {
  const [open, setOpen] = useState(false);
  return (
    <span
      className={`badge-icon${badge.icon === 'superfan' ? ' badge-icon-superfan' : ''}`}
      tabIndex={0}
      onClick={() => setOpen((o) => !o)}
      onBlur={() => setOpen(false)}
    >
      {badge.image_url ? (
        <img
          src={badge.image_url}
          alt={badge.label}
          className="badge-icon-image"
          onError={(e) => { e.target.style.display = 'none'; }}
        />
      ) : (
        <span className="badge-icon-emoji">{BADGE_EMOJIS[badge.icon] || badge.icon}</span>
      )}
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
  // Nach Fantasy-Punkten absteigend sortieren, ohne die Original-Reihenfolge
  // der Props zu verändern.
  const sortedPlayers = [...players].sort(
    (a, b) => (b.total_pts ?? 0) - (a.total_pts ?? 0)
  );
  return (
    <div className="roster-position-group">
      <h4 className="roster-position-label">{label}</h4>
      {sortedPlayers.map((p, i) => {
        const statLine = formatPositionStats(label, p);
        const dimmed = p.in_strength === false && p.in_bank !== true;
        return (
          <div className={`roster-player-row${dimmed ? ' bench-player' : ''}`} key={i}>
            <img
              src={p.image_url}
              alt={p.name}
              className="roster-player-image"
              onError={(e) => { e.target.src = './thf_color.svg'; }}
            />
            <div className="roster-player-details">
              <span
                className={`roster-player-name${p.my_guy ? ' my-guy' : ''}`}
                title={p.my_guy ? `Schon ${p.my_guy_seasons}. Saison bei diesem Team` : undefined}
              >
                {p.name}{p.my_guy ? ' — My Guy' : ''}
                {p.in_bank === true && <span className="bench-tag">Bank</span>}
              </span>
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
    "LAST_WEEK_POWER_RANK": lastWeekPowerRank,
    "POWER_RANK_DELTA": powerRankDelta,
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
    // NEU: Anzahl der Spieler, die flexibel (inkl. FLEX-Slots) in die
    // jeweilige Positionsstärke eingerechnet wurden
    "QB Strength Count": qbCount,
    "RB Strength Count": rbCount,
    "WR Strength Count": wrCount,
    "TE Strength Count": teCount,
    "K Strength Count": kCount,
    "Bench Strength": benchStrength,
    "Bench Strength Rank": benchRank,
    "Bench Strength Count": benchCount,
    "COMMENTS": comment,
    // NEU: Prediction-Quiz-Scores (Biggest Football Brain Contest) - Array
    // aus {name, score}, ein Eintrag pro Person (auch bei Co-Owner-Teams
    // mehrere möglich, da beim Quiz individuell abgestimmt wird)
    "QUIZ_SCORES": quizScores = [],
    "FAAB_REMAINING": faabRemaining,
    "LEGACY_STATS": legacyStats,
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
  // Bank ist jetzt eine eigene 6. Kategorie (Top-4 Flex-Reserve), kein
  // eigener Balken mehr pro Einzelposition.
  const strengthCategories = ['QB', 'RB', 'WR', 'TE', 'K', 'Bank'];
  const strengthValues = [qbStrength, rbStrength, wrStrength, teStrength, kStrength, benchStrength];
  const strengthRanks = [qbRank, rbRank, wrRank, teRank, kRank, benchRank];
  const strengthCounts = [qbCount, rbCount, wrCount, teCount, kCount, benchCount];
  // Historische Wochen (Backfill) haben keine Positionsstärke-Daten
  const hasStrengthData = strengthValues.some((v) => v != null);

  const barColors = strengthRanks.map(colorForRank);

  // NEU: Balken wachsen + Linie "fährt" sichtbar von Punkt zu Punkt, sobald
  // die Charts zum ersten Mal ins Bild scrollen (ein gemeinsamer Observer,
  // Animation läuft per requestAnimationFrame statt fester Zeitschritte -
  // dadurch flüssig statt abgehackt)
  const [barsRevealed, setBarsRevealed] = useState(false);
  const [numbersOpacity, setNumbersOpacity] = useState(0);
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

            // Zahlen faden erst ein, NACHDEM die Balken-Wachstumsanimation
            // abgeschlossen ist (die dauert 800ms, siehe layout.transition
            // beim Positionsstärke-Chart weiter unten).
            const BAR_GROW_DURATION = 800;
            let numbersRafId;
            const fadeTimeout = setTimeout(() => {
              const fadeDuration = 400;
              const fadeStart = performance.now();
              const fadeStep = (now) => {
                const progress = Math.min((now - fadeStart) / fadeDuration, 1);
                setNumbersOpacity(progress);
                if (progress < 1) {
                  numbersRafId = requestAnimationFrame(fadeStep);
                }
              };
              numbersRafId = requestAnimationFrame(fadeStep);
            }, BAR_GROW_DURATION);

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
            observerCleanupExtras.push(() => {
              clearTimeout(fadeTimeout);
              if (numbersRafId) cancelAnimationFrame(numbersRafId);
            });
          }
        });
      },
      { threshold: 0.3 }
    );
    const observerCleanupExtras = [];
    observer.observe(el);
    return () => {
      observer.disconnect();
      if (rafId) cancelAnimationFrame(rafId);
      observerCleanupExtras.forEach((fn) => fn());
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

  // Farbe pro Punkt: feste liga-weite Punktbereiche (siehe LEAGUE_POINT_BANDS
  // oben), NICHT von weekYMin/weekYMax abhängig - die Achsen-Skala bleibt
  // zwar individuell pro Team, die Farbe aber ligaweit vergleichbar.
  const colorForWeekValue = colorForLeaguePoints;
  const weekPointColors = displayedWeekY.map(colorForWeekValue);
  // Plotly unterstützt keine echten Verlaufslinien in einem Trace - daher
  // wird die Linie in einzelne 2-Punkt-Segmente zerlegt, jedes eingefärbt
  // mit der Mischfarbe seiner beiden Endpunkte.
  const gradientLineSegments = [];
  for (let i = 0; i < displayedWeekX.length - 1; i++) {
    gradientLineSegments.push({
      type: 'scatter',
      x: [displayedWeekX[i], displayedWeekX[i + 1]],
      y: [displayedWeekY[i], displayedWeekY[i + 1]],
      mode: 'lines',
      line: { color: weekPointColors[i + 1], width: 3 },
      hoverinfo: 'skip',
      showlegend: false,
    });
  }

  return (
    <div className="team-section">

      <div className="team-header-row">
        <span className="rank-badge">#{team["POWER RANK"]}</span>
        <h2 className="team-title">
          {name === "No Team Name" ? displayName : name}
          <span className="team-record"> ({wins}-{losses})</span>
        </h2>
      </div>

      {lastWeekPowerRank != null && (
        <p className="rank-movement">
          Letzte Woche Rang {lastWeekPowerRank}{' '}
          {powerRankDelta === 0 ? (
            <span className="rank-same">(-)</span>
          ) : powerRankDelta > 0 ? (
            <span className="rank-up">(▲{powerRankDelta})</span>
          ) : (
            <span className="rank-down">(▼{Math.abs(powerRankDelta)})</span>
          )}
        </p>
      )}

      {faabRemaining != null && (
        <p className="faab-line">💰 FAAB: <strong>{faabRemaining}</strong></p>
      )}

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

      {quizScores.length > 0 && (
        <p className="quiz-score-line">
          🧠 Biggest Football Brain Contest:{' '}
          {quizScores.map((q, i) => (
            <span key={i}>
              {q.name}: <strong>{q.score} Punkte</strong>
              {i < quizScores.length - 1 ? ' · ' : ''}
            </span>
          ))}
        </p>
      )}

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
          {/* Positionsstärke als farbcodierter Bar-Chart - nur wenn Daten vorhanden (fehlt bei historischen Wochen) */}
          {hasStrengthData && (
          <div className="chart-touch-wrapper">
            <Plot
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              data={[
                {
                  type: 'bar',
                  x: strengthCategories,
                  y: displayedStrengthValues,
                  customdata: strengthRanks.map((r, i) => [r, strengthCounts[i]]),
                  text: strengthRanks.map((r) => (r != null ? `<b>${r}</b>` : '')),
                  textposition: 'inside',
                  insidetextanchor: 'start',
                  textfont: {
                    color: barColors.map((c) => darkenColorAlpha(c, 0.45, numbersOpacity)),
                    family: 'Roboto Condensed, sans-serif',
                    size: 22
                  },
                  marker: { color: barColors },
                  hovertemplate: '<b>%{x}</b><br>Wert: %{y}/100<br>Rang %{customdata[0]} von 12<br>Spieler gezählt: %{customdata[1]}<extra></extra>'
                }
              ]}
              layout={{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                dragmode: false,
                barmode: 'overlay',
                transition: { duration: 800, easing: 'cubic-in-out' },
                hovermode: 'closest',
                hoverlabel: {
                  bgcolor: CHART_COLORS.surface,
                  bordercolor: CHART_COLORS.accent,
                  font: { color: CHART_COLORS.text, family: 'Roboto, sans-serif', size: 13 }
                },
                title: {
                  text: 'AKTUELLE TEAMSTÄRKE',
                  y: 0.95,
                  yanchor: 'top',
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
          )}
          {/* Line Chart */}
          <div className="chart-touch-wrapper">
            <Plot
              useResizeHandler={true}
              style={{ width: '100%', height: '100%' }}
              data={[
                ...gradientLineSegments,
                {
                  type: 'scatter',
                  x: displayedWeekX,
                  y: displayedWeekY,
                  line: {
                    color: 'transparent',
                    width: 0
                  },
                  mode: 'markers',
                  marker: {
                    size: 9,
                    color: weekPointColors,
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
                  y: 0.95,
                  yanchor: 'top',
                  font: {
                    family: 'Roboto, sans-serif',
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
        </div>

        {/* Roster: jetzt mit Spielerbild + Detail-Stats, ausklappbar - nur wenn Kader-Daten vorhanden (fehlen bei historischen Wochen) */}
        {(qb.length + rb.length + wr.length + te.length + k.length + def_.length) > 0 && (
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
        )}
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

      {legacyStats && (legacyStats.win_pct != null || legacyStats.most_owned?.length > 0) && (
        <details className="collapsible team-legacy">
          <summary>Legacy Stats anzeigen</summary>
          <div className="collapsible-content">

            <h4 className="legacy-section-title">Platzierungen und Erfolge</h4>

            {(legacyStats.angstgegner || legacyStats.opfer) && (
              <div className="legacy-rivals">
                {legacyStats.angstgegner && (
                  <div className="legacy-rival-card legacy-rival-nemesis">
                    <span className="legacy-rival-emoji">😱</span>
                    <div>
                      <span className="legacy-rival-label">Angstgegner</span>
                      <span className="legacy-rival-name">{legacyStats.angstgegner.name}</span>
                      <span className="legacy-rival-record">
                        {legacyStats.angstgegner.wins}-{legacyStats.angstgegner.losses}
                        {legacyStats.angstgegner.ties > 0 ? `-${legacyStats.angstgegner.ties}` : ''}
                      </span>
                    </div>
                  </div>
                )}
                {legacyStats.opfer && (
                  <div className="legacy-rival-card legacy-rival-victim">
                    <span className="legacy-rival-emoji">😈</span>
                    <div>
                      <span className="legacy-rival-label">Opfer</span>
                      <span className="legacy-rival-name">{legacyStats.opfer.name}</span>
                      <span className="legacy-rival-record">
                        {legacyStats.opfer.wins}-{legacyStats.opfer.losses}
                        {legacyStats.opfer.ties > 0 ? `-${legacyStats.opfer.ties}` : ''}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {legacyStats.win_pct != null && (
              <p className="legacy-line">
                <strong>All-Time Win%:</strong> {legacyStats.win_pct}%{' '}
                ({legacyStats.wins}-{legacyStats.losses}{legacyStats.ties > 0 ? `-${legacyStats.ties}` : ''})
                <RankChip rank={legacyStats.win_pct_rank} />
              </p>
            )}

            {legacyStats.avg_placement != null && (
              <p className="legacy-line">
                <strong>Ø Endplatzierung:</strong> {legacyStats.avg_placement}
                <RankChip rank={legacyStats.avg_placement_rank} />
              </p>
            )}

            {legacyStats.placements?.length > 0 && (
              <div className="legacy-line">
                <strong>Platzierungen:</strong>
                <PlacementRow placements={legacyStats.placements} />
              </div>
            )}

            <h4 className="legacy-section-title">Scoring</h4>

            {legacyStats.all_time_points != null && (
              <div className="legacy-line">
                <strong>All-Time Gesamtpunkte:</strong> {legacyStats.all_time_points}
                <RankChip rank={legacyStats.all_time_points_rank} />
                {legacyStats.points_by_season?.length > 0 && (
                  <SeasonBreakdownRow items={legacyStats.points_by_season} valueKey="points" />
                )}
              </div>
            )}

            {legacyStats.high_week && (
              <p className="legacy-line">
                <strong>Höchster Wochenscore:</strong> {legacyStats.high_week.points} Punkte{' '}
                (Saison {legacyStats.high_week.season}, Woche {legacyStats.high_week.week})
                <RankChip rank={legacyStats.high_week_rank} />
              </p>
            )}

            {legacyStats.low_week && (
              <p className="legacy-line">
                <strong>Niedrigster Wochenscore:</strong> {legacyStats.low_week.points} Punkte{' '}
                (Saison {legacyStats.low_week.season}, Woche {legacyStats.low_week.week})
                <RankChip rank={legacyStats.low_week_rank} />
              </p>
            )}

            {legacyStats.high_player_week && (
              <p className="legacy-line">
                <strong>Bester Einzelspieler-Score:</strong> {legacyStats.high_player_week.player} mit{' '}
                {legacyStats.high_player_week.points} Punkten{' '}
                (Saison {legacyStats.high_player_week.season}, Woche {legacyStats.high_player_week.week})
                <RankChip rank={legacyStats.high_player_week_rank} />
              </p>
            )}

            <h4 className="legacy-section-title">Activity</h4>

            <div className="legacy-line">
              <strong>Waiver-Wire-Moves (all-time):</strong> {legacyStats.waiver_moves}
              <RankChip rank={legacyStats.waiver_moves_rank} />
              {legacyStats.waiver_moves_by_season?.length > 0 && (
                <SeasonBreakdownRow items={legacyStats.waiver_moves_by_season} valueKey="count" />
              )}
            </div>

            <div className="legacy-line">
              <strong>Trades (all-time):</strong> {legacyStats.trades}
              <RankChip rank={legacyStats.trades_rank} />
              {legacyStats.trades_by_season?.length > 0 && (
                <SeasonBreakdownRow items={legacyStats.trades_by_season} valueKey="count" />
              )}
            </div>

            {legacyStats.most_owned?.length > 0 && (
              <div className="legacy-most-owned">
                <strong>Lieblingsspieler</strong>
                <div className="legacy-most-owned-cards">
                  {legacyStats.most_owned.map((p, i) => {
                    const maxWeeks = Math.max(...legacyStats.most_owned.map((x) => x.weeks));
                    const size = 36 + (p.weeks / maxWeeks) * 40; // 36-76px, nach Wochen skaliert
                    return (
                      <div className="legacy-owned-player" key={i}>
                        <img
                          src={p.image_url}
                          alt={p.name}
                          style={{ width: size, height: size }}
                          className="legacy-owned-player-image"
                          onError={(e) => { e.target.src = './thf_color.svg'; }}
                        />
                        <span className="legacy-owned-player-name">{p.name}</span>
                        <span className="legacy-owned-player-weeks">{p.weeks} Wochen</span>
                      </div>
                    );
                  })}
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
