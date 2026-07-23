import React from 'react';
import './header.css'; // Assuming you have a dedicated header stylesheet

const Header = ({ weekLabel, historyIndex, selectedFile, onSelectFile }) => {
  const isPreseason = weekLabel === 'Vorsaison';

  return (
    <header id="header" className="header">
      <img
        src="./thf_color.svg" // Ensure the path is correct and the logo is placed in the public folder
        alt="Fantasy League Logo"
        className="logo"
      />
      <h1>THE HANSON FAMILY</h1>
      <h2>Power Rankings - {weekLabel ? weekLabel : 'Lädt...'}</h2>

      {historyIndex.length > 0 && (
        <select
          className="week-selector"
          value={selectedFile || ''}
          onChange={(e) => onSelectFile(e.target.value || null)}
        >
          <option value="">Aktuelle Woche</option>
          {historyIndex.map((entry) => (
            <option key={entry.file} value={entry.file}>
              {entry.label}
            </option>
          ))}
        </select>
      )}

      <p className="intro">
        Jede Woche werden hier alle Teams nach ihrer gesamten aber auch aktuellen Performance eingestuft. Alles ohne Hot Takes und persönlicher Meinung, sondern nach einem selbst erstelltem Modell.
      </p>
      {isPreseason && (
        <p className="preseason-note">
          Die Saison hat noch nicht begonnen - hier siehst du zur Orientierung Daten aus der Vorsaison.
        </p>
      )}
      <a href="#explanation" className="jump-to-bottom">
        Erklärung
      </a>
    </header>
  );
};

export default Header;
