import React from 'react';

const Explanation = () => {
  return (
    <section id="explanation" className="explanation">
      <h2>Erklärung des Power Rankings</h2>
      <p>
        Der <strong>POWER RANK</strong> wird anhand einer umfassenden Analyse mehrerer Metriken berechnet, um die Leistung und den Erfolg einer Mannschaft ganzheitlich darzustellen. Die Berechnung basiert auf fünf gewichteten Faktoren, die unterschiedliche Aspekte des Erfolgs berücksichtigen:
      </p>
      <ol>
        <li><strong>Siege (Wins)</strong> – 40 % Gewichtung: Teams mit mehr Siegen erhalten einen höheren Rang, da dies ein direkter Indikator für Erfolg ist.</li>
        <li><strong>Erzielte Punkte (Points For)</strong> – 20 % Gewichtung: Die Offensivstärke wird durch die erzielten Punkte reflektiert. Teams, die regelmäßig viele Punkte erzielen, werden höher eingestuft.</li>
        <li><strong>Trend (Trend Percentage)</strong> – 20 % Gewichtung: Der aktuelle Trend der Mannschaft wird berücksichtigt. Wenn ein Team in den letzten Wochen besser abgeschnitten hat als im Durchschnitt der Saison, deutet das auf eine positive Entwicklung hin.</li>
        <li><strong>Gegnerische Punkte (Points Against)</strong> – 10 % Gewichtung: Dieser Wert gibt an, wie stark die bisherigen Gegner waren und wie viel Pech das Team möglicherweise hatte. Wenn ein Team viele Punkte gegen sich hatte, könnte das darauf hindeuten, dass es gegen besonders starke Gegner antreten musste, was den bisherigen Erfolg beeinträchtigen kann.</li>
        <li><strong>Angepasster Durchschnitt (Adjusted Average)</strong> – 10 % Gewichtung: Hier wird ein Durchschnittswert der wöchentlichen Punkte berechnet, bei dem die besten und schlechtesten Wochen ausgeschlossen werden, um die Konstanz einer Mannschaft zu bewerten.</li>
      </ol>
      <p>
        Diese Gewichtung macht Sinn, da sie sowohl den langfristigen Erfolg (Siege, erzielte Punkte) als auch kurzfristige Entwicklungen (Trend) und die Schwierigkeit der bisherigen Gegner (gegnerische Punkte) miteinbezieht. Der <strong>POWER RANK</strong> gibt somit eine ausgewogene Darstellung der Leistungsfähigkeit eines Teams und hilft, Stärken und Schwächen klar zu identifizieren sowie den bisherigen Spielverlauf zu berücksichtigen.
      </p>
      <p>
        Der <strong>Trend</strong> wird berechnet, indem die Leistung der letzten zwei Wochen mit dem bisherigen Saisondurchschnitt verglichen wird. Dazu wird der Durchschnitt der Punkte aus den letzten zwei Wochen ermittelt und mit dem Durchschnitt der restlichen Saisonpunkte verglichen.
      </p>
      <ul>
        <li>Ist der Prozentsatz <strong>über +7 %</strong>, zeigt der Trend "<strong>UP</strong>" an (bessere Leistung).</li>
        <li>Bei <strong>unter -7 %</strong> zeigt er "<strong>DOWN</strong>" (schlechtere Leistung).</li>
        <li>Liegt er dazwischen, wird "<strong>NO TREND</strong>" angezeigt.</li>
      </ul>
      <p>
        So wird ersichtlich, ob sich das Team kürzlich verbessert oder verschlechtert hat.
      </p>
      <p>
        Die <strong>Aktuelle Teamstärke</strong> wird berechnet, indem die Punkte der besten Spieler eines Teams auf den jeweiligen Positionen summiert werden. Für jede Position wird eine bestimmte Anzahl an Top-Spielern berücksichtigt, basierend auf deren Gesamtpunkte in der Saison. Dabei werden folgende Positionen einbezogen:
      </p>
      <ul>
        <li><strong>Quarterbacks (QB)</strong>: Der Punktwert des besten Quarterbacks.</li>
        <li><strong>Running Backs (RB)</strong>: Die Punktwerte der drei besten Running Backs.</li>
        <li><strong>Wide Receivers (WR)</strong>: Die Punktwerte der vier besten Wide Receivers.</li>
        <li><strong>Tight Ends (TE)</strong>: Der Punktwert des besten Tight Ends.</li>
        <li><strong>Kicker (K)</strong>: Der Punktwert des besten Kickers.</li>
      </ul>
      <p>
        Diese Summen der Punktwerte werden für jedes Team berechnet und geben die Stärke der jeweiligen Position wieder. Die stärksten Spieler auf diesen Positionen erhalten also den größten Einfluss auf die berechnete Positionsstärke.
      </p>
      <h3>Warum die Positionsstärke nicht im Power Ranking berücksichtigt wird:</h3>
      <p>
        Die Positionsstärke allein zeigt zwar, wie gut ein Team auf bestimmten Positionen besetzt ist, aber sie spiegelt nicht den gesamten Erfolg eines Teams wider. Ein Team könnte zwar starke Einzelspieler haben, aber dennoch aufgrund von schwachen Gesamtleistungen, Verletzungen oder taktischen Entscheidungen in den Spielen nicht erfolgreich sein. Das <strong>Power Ranking</strong> soll hingegen eine ganzheitliche Bewertung liefern, die sowohl die erzielten Siege, die Gesamtoffensivleistung, den Trend und die Stärke der Gegner mit einbezieht. Die Positionsstärke beeinflusst indirekt den Erfolg eines Teams, ist jedoch keine direkte Messgröße im Power Ranking.
      </p>
            <a href="#header" className="jump-to-top">
        Zurück nach oben
      </a>
    </section>
  );
};

export default Explanation;
