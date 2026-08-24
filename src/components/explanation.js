import React from 'react';
import './explanation.css';

const Explanation = () => {
  return (
    <section id="explanation" className="explanation">
      <h2>Erklärung des Power Rankings</h2>
      <p>
        Der <strong>POWER RANK</strong> wird anhand einer umfassenden Analyse mehrerer Metriken berechnet, um die Leistung und den Erfolg einer Mannschaft ganzheitlich darzustellen. Die Berechnung basiert auf fünf gewichteten Faktoren, die unterschiedliche Aspekte des Erfolgs berücksichtigen:
      </p>
      <ol>
        <li><strong>Siege (Wins)</strong> – 25 % Gewichtung: Teams mit mehr Siegen erhalten einen höheren Rang, da dies ein direkter Indikator für Erfolg ist.</li>
        <li><strong>Erzielte Punkte (Points For)</strong> – 25 % Gewichtung: Die Offensivstärke wird durch die erzielten Punkte reflektiert. Teams, die regelmäßig viele Punkte erzielen, werden höher eingestuft.</li>
        <li><strong>Trend (Trend Percentage)</strong> – 25 % Gewichtung: Der aktuelle Trend der Mannschaft wird berücksichtigt. Wenn ein Team in den letzten Wochen besser abgeschnitten hat als im Durchschnitt der Saison, deutet das auf eine positive Entwicklung hin.</li>
        <li><strong>Gegnerische Punkte (Points Against)</strong> – 10 % Gewichtung: Dieser Wert gibt an, wie stark die bisherigen Gegner waren und wie viel Pech das Team möglicherweise hatte. Wenn ein Team viele Punkte gegen sich hatte, könnte das darauf hindeuten, dass es gegen besonders starke Gegner antreten musste, was den bisherigen Erfolg beeinträchtigen kann.</li>
        <li><strong>Angepasster Durchschnitt (Adjusted Average)</strong> – 15 % Gewichtung: Hier wird ein Durchschnittswert der wöchentlichen Punkte berechnet, bei dem die besten und schlechtesten Wochen ausgeschlossen werden, um die Konstanz einer Mannschaft zu bewerten.</li>
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
        Die <strong>Aktuelle Teamstärke</strong> wird jetzt flexibel anhand der tatsächlichen Aufstellungs-Regeln eurer Liga berechnet (also wie viele QB-, RB-, WR-, TE- und FLEX-Slots ihr wirklich habt), statt einer festen Anzahl Spieler pro Position. Für jedes Team werden alle Spieler nach Punkten pro Spiel (PPG) sortiert und wie in einer echten Aufstellung verteilt: zuerst die festen Positions-Slots, danach die FLEX-Slots mit den jeweils besten verbliebenen Spielern. Ein starker Running Back, der eigentlich in einen FLEX-Slot passt, zählt dabei weiterhin zur RB-Stärke. Hat ein Team also außergewöhnlich viele gute Spieler auf einer Position, können entsprechend mehr davon in die Wertung einfließen.
      </p>
      <ul>
        <li><strong>Quarterbacks (QB)</strong>, <strong>Running Backs (RB)</strong>, <strong>Wide Receivers (WR)</strong>, <strong>Tight Ends (TE)</strong> und <strong>Kicker (K)</strong> werden jeweils nach diesem Prinzip berechnet.</li>
        <li><strong>Bank</strong>: eine sechste Kategorie, die die drei besten übrig gebliebenen Flex-Spieler (RB/WR/TE) zeigt, die es nicht in die Startaufstellung geschafft haben – ein Indikator dafür, wie gut ein Team im Verletzungsfall nachrücken kann.</li>
      </ul>
      <p>
        Die Werte werden pro Kategorie auf einer Skala von 1 bis 100 normalisiert (das ligaweit stärkste Team bekommt 100, alle anderen entsprechend weniger). Die Zahl in jedem Balken zeigt den Liga-Rang (1–12) auf dieser Position; wie viele Spieler konkret eingerechnet wurden, steht beim Darüberfahren mit der Maus (bzw. Antippen auf Mobilgeräten).
      </p>
      <h3>Warum die Positionsstärke nicht im Power Ranking berücksichtigt wird:</h3>
      <p>
        Die Positionsstärke allein zeigt zwar, wie gut ein Team auf bestimmten Positionen besetzt ist, aber sie spiegelt nicht den gesamten Erfolg eines Teams wider. Ein Team könnte zwar starke Einzelspieler haben, aber dennoch aufgrund von schwachen Gesamtleistungen, Verletzungen oder taktischen Entscheidungen in den Spielen nicht erfolgreich sein. Das <strong>Power Ranking</strong> soll hingegen eine ganzheitliche Bewertung liefern, die sowohl die erzielten Siege, die Gesamtoffensivleistung, den Trend und die Stärke der Gegner mit einbezieht. Die Positionsstärke beeinflusst indirekt den Erfolg eines Teams, ist jedoch keine direkte Messgröße im Power Ranking.
      </p>
      <p>
        Der <strong>Saisonverlauf</strong> zeigt die wöchentlichen Punktzahlen eines Teams. Die Y-Achse ist für jedes Team individuell skaliert (damit auch konstante Teams mit wenig Schwankung gut lesbar bleiben), die <strong>Farbe</strong> der Linie und Punkte ist aber ligaweit einheitlich: 0–60 Punkte erscheinen rot, 60–80 rot-orange, 80–100 gelb, 100–120 gelb-grün, 120–140 grün, 140–160 türkis und ab 160 blau. So lässt sich auf einen Blick erkennen, ob eine Woche für ein Team stark oder schwach war – auch im Vergleich zu anderen Karten.
      </p>
      <p>
        Neben Power Rank, Teamstärke und Saisonverlauf gibt es noch ein paar weitere Werte auf jeder Karte: das <strong>FAAB</strong>-Restbudget fürs Waiver-Bidding, der Score aus dem ligainternen <strong>Prediction-Quiz</strong> ("Biggest Football Brain Contest"), sowie diverse <strong>Badges</strong> für Auffälligkeiten der Woche oder Saison (z.B. besonders viele verletzte Spieler, ein besonders knapper Sieg oder ein Spieler, der schon seit Jahren treu im Kader steht – als "My Guy" golden markiert). Details zu jedem Badge gibt's beim Draufklicken bzw. -tippen.
      </p>
      <a href="#header" className="jump-to-top">
        Zurück nach oben
      </a>
    </section>
  );
};

export default Explanation;
