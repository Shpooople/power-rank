import React from 'react';
import './BigBrainTop3.css';

const MEDALS = ['🥇', '🥈', '🥉'];

// Klassische Podium-Reihenfolge: Platz 2 links, Platz 1 mittig/groß, Platz 3 rechts
const PODIUM_ORDER = [1, 0, 2];

// entries: Array aus {name, score}, bereits absteigend nach score sortiert -
// diese Komponente nimmt nur die ersten 3 und stellt sie als Podium dar.
const BigBrainTop3 = ({ entries = [] }) => {
  if (!entries || entries.length < 1) return null;
  const topThree = entries.slice(0, 3);

  return (
    <div className="big-brain-top3">
      <h2 className="big-brain-title">🧠 Biggest Football Brain Contest</h2>
      <div className="big-brain-podium">
        {PODIUM_ORDER.filter((idx) => topThree[idx]).map((idx) => {
          const entry = topThree[idx];
          return (
            <div key={idx} className={`big-brain-entry big-brain-rank-${idx + 1}`}>
              <span className="big-brain-medal">{MEDALS[idx]}</span>
              <span className="big-brain-name">{entry.name}</span>
              <span className="big-brain-score">{entry.score}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default BigBrainTop3;
