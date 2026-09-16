import React, { useState } from 'react';
import './FloatingNav.css';

// Ein-/ausklappbare Navigationsleiste am rechten Bildschirmrand - zeigt
// Platzierung + Teamname jedes Teams, antippen scrollt sanft zur jeweiligen
// Team-Karte (die dafür in App.js eine eindeutige Anker-ID bekommt).
const FloatingNav = ({ teams }) => {
  const [open, setOpen] = useState(false);

  if (!teams || teams.length === 0) return null;

  const scrollToTeam = (index) => {
    const el = document.getElementById(`team-anchor-${index}`);
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
          {teams.map((team, index) => {
            const name = team["Team Name"] === "No Team Name" ? team["Display Name"] : team["Team Name"];
            return (
              <button
                type="button"
                key={index}
                className="floating-nav-item"
                onClick={() => scrollToTeam(index)}
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
