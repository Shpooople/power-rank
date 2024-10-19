import React from 'react';
import './header.css'; // Assuming you have a dedicated header stylesheet

const Header = ({ currentWeek }) => {
  return (
    <header id="header" className="header">
      <img
        src="./thf_color.svg" // Ensure the path is correct and the logo is placed in the public folder
        alt="Fantasy League Logo"
        className="logo"
      />
      <h1>THE HANSON FAMILY</h1>
      <h2>Power Rankings - Week {currentWeek ? currentWeek : 'Loading...'}</h2> {/* Display the current week */}
      <p className="intro">
        Jede Woche werden hier alle Teams nach ihrer gesamten aber auch aktuellen Performance eingestuft. Alles ohne Hot Takes und persönlicher Meinung, sondern nach einem selbst erstelltem Modell.
      </p>
      <a href="#explanation" className="jump-to-bottom">
        Erklärung
      </a>
    </header>
  );
};

export default Header;
