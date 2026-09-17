import React from 'react';
import './explanation.css';

const Explanation = () => {
  return (
    <section id="explanation" className="explanation">
      <h2>Erklärung des Power Rankings</h2>
      <p>
        Der <strong>POWER RANK</strong> wird anhand einer umfassenden Analyse mehrerer Metriken berechnet, um die Leistung und den Erfolg einer Mannschaft ganzheitlich darzustellen. Die Berechnung basiert auf vier gewichteten Faktoren, die unterschiedliche Aspekte des Erfolgs berücksichtigen:
      </p>
      <ol>
        <li><strong>Erzielte Punkte (Points For)</strong> – 40 % Gewichtung: Die Offensivstärke wird durch die erzielten Punkte reflektiert. Teams, die regelmäßig viele Punkte erzielen, werden höher eingestuft.</li>
        <li><strong>Siege (Wins)</strong> – 15 % Gewichtung: Teams mit mehr Siegen erhalten einen höheren Rang, da dies ein direkter Indikator für Erfolg ist.</li>
        <li><strong>Aktuelle Form (früher "Trend")</strong> – 35 % Gewichtung: Ein gewichteter Durchschnitt der letzten 2 Wochen (siehe unten) wird ligaweit mit allen anderen Teams verglichen - je besser die aktuelle Form im Liga-Vergleich, desto höher die Einstufung.</li>
        <li><strong>Gegnerische Punkte (Points Against)</strong> – 10 % Gewichtung: Dieser Wert gibt an, wie stark die bisherigen Gegner waren und wie viel Pech das Team möglicherweise hatte. Wenn ein Team viele Punkte gegen sich hatte, könnte das darauf hindeuten, dass es gegen besonders starke Gegner antreten musste, was den bisherigen Erfolg beeinträchtigen kann.</li>
      </ol>
      <p>
        Statt des früheren "Angepassten Durchschnitts" (bei dem die beste und schlechteste Woche ausgeschlossen wurden) zeigt jede Team-Karte jetzt einfach die <strong>durchschnittlichen Punkte pro Woche (Ø Punkte)</strong> – einfacher nachvollziehbar und ohne die Kanten, die das Ausschließen von Wochen bei einer 17-Wochen-Saison mit anfangs noch sehr wenigen gespielten Wochen mit sich brachte. Dieser Wert fließt <strong>nicht</strong> in die POWER-RANK-Berechnung ein, ist rein informativ.
      </p>
      <p>
        Diese Gewichtung macht Sinn, da sie sowohl den langfristigen Erfolg (Siege, erzielte Punkte) als auch kurzfristige Entwicklungen (Aktuelle Form) und die Schwierigkeit der bisherigen Gegner (gegnerische Punkte) miteinbezieht. Der <strong>POWER RANK</strong> gibt somit eine ausgewogene Darstellung der Leistungsfähigkeit eines Teams und hilft, Stärken und Schwächen klar zu identifizieren sowie den bisherigen Spielverlauf zu berücksichtigen.
      </p>
      <p>
        Die <strong>Aktuelle Form</strong> (früher "Trend" genannt) wird berechnet, indem zunächst ein <strong>gewichteter Durchschnitt der letzten 2 Wochen</strong> pro Team ermittelt wird: Die aktuellste Woche zählt voll, die Woche davor nur halb so viel (Gewichtung 100 % / 50 %). Dieser Wert wird dann <strong>ligaweit verglichen</strong>: Die 4 Teams mit dem besten Wert bekommen "UP" (▲), die 4 Teams mit dem schwächsten Wert "DOWN" (▼), alle dazwischen "NO TREND" (▬).
      </p>
      <p>
        So wird ersichtlich, ob sich das Team im Liga-Vergleich zuletzt eher verbessert oder verschlechtert hat.
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
        Der <strong>Saisonverlauf</strong> zeigt die wöchentlichen Punktzahlen eines Teams. Die Y-Achse ist für jedes Team individuell skaliert (damit auch konstante Teams mit wenig Schwankung gut lesbar bleiben), die <strong>Farbe</strong> der Linie und Punkte ist aber ligaweit einheitlich: unter 80 Punkte erscheinen rot, 80–100 rot-orange, 100–120 gelb-orange, 120–140 gelb-grün, 140–160 grün und ab 160 türkis. So lässt sich auf einen Blick erkennen, ob eine Woche für ein Team stark oder schwach war – auch im Vergleich zu anderen Karten.
      </p>

      <h3>Roster: Bank-Markierung und "My Guy"</h3>
      <p>
        Im ausklappbaren <strong>Roster</strong> jeder Karte sind die Spieler pro Position nach Fantasy-Punkten sortiert. Manche Spieler sind <strong>gedimmt</strong> dargestellt – das sind alle, die weder als Starter noch als Top-3-Bank-Spieler in die weiter oben beschriebene Teamstärke-Berechnung einfließen. Die drei Spieler, die genau die "Bank"-Kategorie im Balkendiagramm ausmachen, bekommen zusätzlich ein kleines <strong>"Bank"-Label</strong> neben dem Namen und werden (im Gegensatz zu den übrigen gedimmten Spielern) <strong>nicht</strong> abgedunkelt – sie sind ja aktiv Teil der Wertung.
      </p>
      <p>
        Spieler, die schon seit mindestens 3 Saisons durchgehend bei diesem Team im Kader stehen (mindestens 3 Wochen pro Saison, laut Liga-Historie), werden golden mit dem Zusatz <strong>"My Guy"</strong> markiert – beim Draufhalten mit der Maus (bzw. Antippen) zeigt ein Tooltip, in der wievielten Saison der Spieler schon dabei ist.
      </p>
      <p>
        In den <strong>Legacy Stats</strong> (Lieblingsspieler-Listen) bekommen Spieler außerdem einen <strong>goldenen Ring</strong> um ihr Foto, wenn sie in einer Saison, in der das Team eine Meisterschaft gewonnen hat, im Kader standen – zu unterscheiden von "My Guy" (goldener Text wegen Kader-Treue) und dem goldenen Rand beim Superfan-Badge (siehe unten, wegen Häufung von Spielern eines NFL-Teams).
      </p>

      <h3>Alle Badges im Überblick</h3>
      <p>
        Badges erscheinen oben auf jeder Team-Karte und markieren Auffälligkeiten der aktuellen Woche oder der bisherigen Saison. Details (inkl. genauer Zahl) gibt's beim Antippen/Draufhalten auf das jeweilige Icon.
      </p>
      <p><strong>Saison- und Kader-Badges:</strong></p>
      <ul>
        <li>🩹 <strong>The Hospital</strong> – die meisten verletzten Spieler im Kader (Out/IR/Questionable/Doubtful)</li>
        <li>🏟️ <strong>[NFL-Team]-Homer</strong> – 3 oder mehr Spieler von einem echten NFL-Team im Kader</li>
        <li>🏟️ <strong>[NFL-Team]-Superfan</strong> – noch eine Stufe drüber: 5 oder mehr Spieler von einem NFL-Team (goldener Rand statt normalem Rahmen)</li>
        <li>🐉 <strong>Angstgegner</strong> – höchster Punkteschnitt pro Woche der bisherigen Saison ligaweit (Achtung: nicht zu verwechseln mit dem "Angstgegner" in den Legacy Stats – dort geht's um den Gegner, der dich am häufigsten schlägt)</li>
        <li>🎣 <strong>Waiver-Wire-Wizard</strong> – die meisten Waiver-/Free-Agent-Adds der bisherigen Saison</li>
        <li>💰 <strong>Reichstes Team</strong> – meiste FAAB übrig (bei Gleichstand bekommt niemand das Badge)</li>
        <li>🏚️ <strong>Ärmstes Team</strong> – wenigste FAAB übrig</li>
        <li>🧸 <strong>Kindergarten</strong> – die meisten Rookies im Kader</li>
        <li>🦖 <strong>Altersheim</strong> – höchstes Kader-Durchschnittsalter</li>
      </ul>
      <p><strong>Form- und Serien-Badges:</strong></p>
      <ul>
        <li>📈 <strong>Rising Star</strong> – aktuell beste "Aktuelle Form" der Liga</li>
        <li>📉 <strong>Free Fall</strong> – aktuell schwächste "Aktuelle Form" der Liga</li>
        <li>🔥 <strong>On Fire</strong> – mindestens 2 Siege in Folge</li>
        <li>🥶 <strong>Cold Streak</strong> – mindestens 2 Niederlagen in Folge</li>
        <li>🎢 <strong>Rollercoaster</strong> – größte Wochen-zu-Wochen-Schwankung der Saison</li>
        <li>⚓ <strong>Mr. Consistent</strong> – kleinste Wochen-zu-Wochen-Schwankung der Saison</li>
      </ul>
      <p><strong>Wochen-Badges (Matchup & Lineup):</strong></p>
      <ul>
        <li>👑 <strong>Liga-Krösus</strong> – höchste Punktzahl der aktuellen Woche ligaweit</li>
        <li>🍀 <strong>Pechvogel der Woche</strong> – mehr Punkte als der Liga-Median dieser Woche, trotzdem verloren</li>
        <li>💥 <strong>Giant Killer</strong> – Sieg gegen ein deutlich besser platziertes Team</li>
        <li>🔒 <strong>Punktgenau</strong> – Sieg als klar besser platziertes Team (Favoritensieg bestätigt)</li>
        <li>🦷 <strong>Nervenstark</strong> – knappster Sieg der Woche</li>
        <li>🔨 <strong>Kantersieg</strong> – größter Punkteabstand bei einem Sieg</li>
        <li>🪑 <strong>Bankdrücker</strong> – meiste Punkte auf der eigenen Bank liegen gelassen</li>
        <li>🤡 <strong>Bank-Patzer</strong> – ein Bankspieler hätte den Starter derselben Position übertroffen</li>
        <li>🥇 <strong>Perfektes Lineup</strong> – mindestens 97% der bestmöglichen Aufstellung aus dem eigenen Kader ausgeschöpft</li>
        <li>💣 <strong>Big Bang</strong> – stärkste Einzel-Starter-Leistung der Liga diese Woche</li>
        <li>🫠 <strong>Totalausfall</strong> – schwächste Einzel-Starter-Leistung der Liga diese Woche</li>
        <li>🎯 <strong>Air Raid</strong> – mindestens 40% der Wochenpunkte kamen von den WRs</li>
        <li>🚜 <strong>Ground and Pound</strong> – mindestens 40% der Wochenpunkte kamen von den RBs</li>
        <li>🏈 <strong>Touchdown Overflow</strong> – meiste Touchdowns (Starter) der vergangenen Woche</li>
        <li>🥚 <strong>Klingeling, hier kommt der Eiermann</strong> – ein Starter kam auf 0 Punkte</li>
        <li>👢 <strong>Das heißt nicht umsonst FOOTball</strong> – der eigene Kicker war besser als der beste RB, WR oder der QB im Lineup</li>
        <li>🛡️ <strong>Defense wins Championships</strong> – die eigene Defense war besser als der beste RB, WR oder der QB im Lineup</li>
      </ul>

      <p>
        Neben Power Rank, Teamstärke und Saisonverlauf gibt es noch ein paar weitere Werte auf jeder Karte: das <strong>FAAB</strong>-Restbudget fürs Waiver-Bidding und der Score aus dem ligainternen <strong>Prediction-Quiz</strong> ("Biggest Football Brain Contest").
      </p>
      <a href="#header" className="jump-to-top">
        Zurück nach oben
      </a>
    </section>
  );
};

export default Explanation;
