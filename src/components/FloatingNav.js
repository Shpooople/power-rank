import React, { useState } from 'react';
import './FloatingNav.css';

// Ein-/ausklappbare Navigationsleiste am rechten Bildschirmrand - zeigt
// oben einen Sprung zur Liga-Statistik, danach Platzierung + Teamname jedes
// Teams. Antippen scrollt sanft zum jeweiligen Ziel (Anker-IDs werden in
// App.js/LeagueStats.js vergeben).
const FloatingNav = ({ teams }) => {
  const [open, setOpen] = useState(false);

  if (!teams || teams.length === 0) return null;

  const scrollToId = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    setOpen(false);
  };

  return (
    <div className="floating-nav">
      <button
        type="button"
        className="floating-nav-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Navigation einklappen' : 'Navigation ausklappen'}
      >
        {open ? '✕' : '☰'}
      </button>
      {open && (
        <div className="floating-nav-list">
          <button
            type="button"
            className="floating-nav-item floating-nav-special"
            onClick={() => scrollToId('league-stats-anchor')}
          >
            <span className="floating-nav-rank">📊</span>
            <span className="floating-nav-name">Liga Statistik</span>
          </button>
          <div className="floating-nav-divider" />
          {teams.map((team, index) => {
            const name = team["Team Name"] === "No Team Name" ? team["Display Name"] : team["Team Name"];
            return (
              <button
                type="button"
                key={index}
                className="floating-nav-item"
                onClick={() => scrollToId(`team-anchor-${index}`)}
              >
                <span className="floating-nav-rank">#{team["POWER RANK"]}</span>
                <span className="floating-nav-name">{name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FloatingNav;
