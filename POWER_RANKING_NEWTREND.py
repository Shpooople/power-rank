import requests
import pandas as pd
from datetime import datetime
import os
import math
import statistics

# --- NEU: Woche und Saison automatisch von Sleeper ermitteln ---
# Sleeper stellt den globalen NFL-Status bereit, inkl. aktueller Woche & Saison.
state_response = requests.get("https://api.sleeper.app/v1/state/nfl")
nfl_state = state_response.json()

season = nfl_state["season"]  # z.B. "2025"

# WICHTIG: Bitte nach dem ersten Testlauf prüfen, ob "week" bereits die
# abgeschlossene Woche ist oder die kommende. Sleeper zählt "week" meist als
# die *aktuell laufende* Woche. Falls deine bisherige manuelle current_week
# immer "die letzte abgeschlossene Woche" war, ggf. auf nfl_state["week"] - 1
# anpassen. Einmal gegen deinen bisherigen manuellen Wert gegenchecken.
current_week = nfl_state["week"] - 1
if current_week < 1:
    current_week = 1

print(f"Ermittelte Saison: {season}, aktuelle Woche: {current_week}")

# Sleeper API for fetching rosters, players, etc.
league_id = "1368162392545988608"  # Aktuelle/eigentliche Liga-ID (Saison 2026)

# --- NEU: Fallback auf Woche 13 der letzten abgeschlossenen Saison, solange die
# reguläre Saison noch nicht läuft. Wichtig: Die hinterlegte league_id "rollt"
# bei Sleeper oft erst manuell auf die neue Saison um. Wir prüfen daher zuerst,
# zu welcher Saison die Liga-ID selbst gehört, statt blind eine Saison
# zurückzurechnen - sonst landet man leicht zwei Saisons zu früh (siehe Bug:
# 2026 -> fälschlich 2024 statt 2025).
if nfl_state.get("season_type") != "regular":
    print(f"Saison-Typ ist '{nfl_state.get('season_type')}' - reguläre Saison läuft noch nicht.")
    try:
        league_info = requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()
    except Exception as e:
        league_info = {}
        print(f"Liga-Infos konnten nicht geladen werden: {e}")

    league_own_season = league_info.get("season")

    if league_own_season and league_own_season != nfl_state.get("season"):
        # Die hinterlegte Liga-ID ist noch nicht auf die neue Saison
        # "hochgerollt" - sie IST bereits die zuletzt abgeschlossene Saison.
        season = league_own_season
        current_week = 13
        print(f"Fallback aktiv: Liga {league_id} ist bereits die Vorjahres-Liga (Saison {season}), Woche {current_week}.")
    else:
        # Liga-ID gehört schon zur neuen Saison (die aber noch nicht läuft) ->
        # einen Schritt über previous_league_id zur letzten Saison zurückgehen.
        previous_league_id = league_info.get("previous_league_id")
        if previous_league_id:
            try:
                prev_league_info = requests.get(f"https://api.sleeper.app/v1/league/{previous_league_id}").json()
                league_id = previous_league_id
                season = prev_league_info.get("season", str(int(season) - 1))
                current_week = 13
                print(f"Fallback aktiv: Vorjahres-Liga {league_id}, Saison {season}, Woche {current_week}.")
            except Exception as e:
                print(f"Vorjahres-Liga konnte nicht geladen werden: {e}")
        else:
            print("Keine Vorjahres-Liga gefunden - bleibe bei Woche 1 der aktuellen (noch leeren) Saison.")

weeks = range(1, current_week + 1)  # Include only weeks that have been played
url_rosters = f"https://api.sleeper.app/v1/league/{league_id}/rosters"
url_players = "https://api.sleeper.app/v1/players/nfl"
url_users = f"https://api.sleeper.app/v1/league/{league_id}/users"

# Fetch player data for player names and positions
response_rosters = requests.get(url_rosters)
rosters = response_rosters.json()
response_players = requests.get(url_players)
players = response_players.json()
response_users = requests.get(url_users)
users = response_users.json()

# --- Anzeige-Hinweis für die Vorsaison ---
# Chart, Trend und Adjusted Average nutzen jetzt alle dieselbe Datenquelle
# (weekly_points, weiter unten befüllt über die bereits korrekt ermittelte
# league_id/season) - das verhindert Inkonsistenzen zwischen Chart und Trend.
season_type = nfl_state.get("season_type", "regular")
using_previous_season_chart_data = season_type != "regular"

# --- NEU: Punkte pro Spiel statt Gesamtpunkte für die Positionsstärke ---
# Wir holen uns für jede gespielte Woche die kompletten Sleeper-Stats aller
# Spieler (ein API-Call pro Woche, wie beim Projections-Endpoint weiter unten)
# und zählen selbst mit: in wie vielen Wochen hat ein Spieler tatsächlich
# gespielt, und wie viele Half-PPR-Punkte hat er insgesamt gemacht.
# PPG = Gesamtpunkte / Spiele. Das ersetzt die vorherige externe CSV-Quelle
# (hvpkod/NFL-Data) komplett - spart eine Abhängigkeit und matched über
# Spieler-IDs statt über (fehleranfällige) Namensvergleiche.
games_played_by_player = {}
total_points_by_player = {}

# --- NEU: Rohstats für die Roster-Anzeige (Comp/Att, Yards, TDs etc.) ---
# Werden in derselben Schleife mitgesammelt - kein zusätzlicher API-Call nötig.
SEASON_STAT_KEYS = [
    'pass_cmp', 'pass_att', 'pass_yd', 'pass_td',
    'rush_att', 'rush_yd', 'rush_td',
    'rec', 'rec_tgt', 'rec_yd', 'rec_td',
    'fgm', 'fga', 'xpm', 'xpa',
    'sack', 'int', 'fum_rec', 'def_td'
]
season_stats_by_player = {}
# NEU: Rohstats NUR der aktuellen (letzten abgeschlossenen) Woche separat
# sichern - für die Performer-Karten, die Wochen- statt Saison-Stats zeigen sollen.
current_week_player_stats = {}

for wk in weeks:
    try:
        stats_url = (
            f"https://api.sleeper.app/stats/nfl/{season}/{wk}"
            "?season_type=regular&position[]=QB&position[]=RB&position[]=WR"
            "&position[]=TE&position[]=K&position[]=DEF"
        )
        stats_response = requests.get(stats_url)
        week_stats = stats_response.json() or []
        for entry in week_stats:
            pid = entry.get('player_id')
            if not pid:
                continue
            stats = entry.get('stats', {}) or {}
            if wk == current_week:
                current_week_player_stats[pid] = stats
            # "gp" liefert Sleeper meist direkt mit. Falls das Feld fehlt,
            # darf NICHT "irgendein Stats-Feld ist vorhanden" als Signal
            # reichen - Sleeper liefert oft auch für verletzte/inaktive
            # Spieler einen (nullwertigen) Stats-Eintrag, weil deren TEAM ja
            # gespielt hat. Wir prüfen stattdessen gezielt auf echte
            # Aktivitäts-Indikatoren über alle Positionen hinweg.
            played = stats.get('gp')
            if played is None:
                activity_keys = [
                    'off_snp', 'st_snp', 'def_snp',
                    'pass_att', 'rush_att', 'rec_tgt',
                    'fga', 'xpa', 'idp_tkl'
                ]
                played = 1 if any(stats.get(k, 0) for k in activity_keys) else 0
            if played:
                games_played_by_player[pid] = games_played_by_player.get(pid, 0) + 1
            pts = stats.get('pts_half_ppr', stats.get('pts_std', stats.get('pts_ppr', 0))) or 0
            total_points_by_player[pid] = total_points_by_player.get(pid, 0) + pts

            player_season = season_stats_by_player.setdefault(pid, {k: 0 for k in SEASON_STAT_KEYS})
            for k in SEASON_STAT_KEYS:
                player_season[k] += stats.get(k, 0) or 0
    except Exception as e:
        print(f"Stats für Woche {wk} konnten nicht geladen werden: {e}")

def ppg(pid):
    games = games_played_by_player.get(pid, 0)
    if games <= 0:
        return 0
    return total_points_by_player.get(pid, 0) / games

# Helper function to calculate position strength based on points-per-game
def calculate_strength(player_ids, num_players):
    player_ppgs = sorted((ppg(pid) for pid in player_ids), reverse=True)
    return round(sum(player_ppgs[:num_players]), 1)

# --- NEU: Detail-Stats + Spielerbild fürs Roster ---
# Die _from-Varianten arbeiten auf einem rohen Stats-Dict (egal ob Saison-
# Summe oder Einzelwoche) - so lassen sie sich für Roster (Saison) UND
# Performer-Karten (nur aktuelle Woche) wiederverwenden.
def _qb_stats_from(s):
    return {
        "comp": int(s.get('pass_cmp', 0)),
        "att": int(s.get('pass_att', 0)),
        "pass_yd": int(s.get('pass_yd', 0)),
        "rush_yd": int(s.get('rush_yd', 0)),
        "td": int(s.get('pass_td', 0) + s.get('rush_td', 0)),
    }

def _rb_stats_from(s):
    att = s.get('rush_att', 0)
    yd = s.get('rush_yd', 0)
    ypc = round(yd / att, 1) if att else 0
    return {
        "att": int(att),
        "yd": int(yd),
        "ypc": ypc,
        "td": int(s.get('rush_td', 0) + s.get('rec_td', 0)),
    }

def _wr_stats_from(s):
    return {
        "targets": int(s.get('rec_tgt', 0)),
        "catches": int(s.get('rec', 0)),
        "yd": int(s.get('rec_yd', 0)),
        "td": int(s.get('rec_td', 0) + s.get('rush_td', 0)),
    }

def _k_stats_from(s):
    return {
        "fgm": int(s.get('fgm', 0)),
        "fga": int(s.get('fga', 0)),
        "xpm": int(s.get('xpm', 0)),
        "xpa": int(s.get('xpa', 0)),
    }

def _def_stats_from(s):
    return {
        "sack": int(s.get('sack', 0)),
        "int": int(s.get('int', 0)),
        "fum_rec": int(s.get('fum_rec', 0)),
        "td": int(s.get('def_td', 0)),
    }

# Saison-Varianten (fürs Roster)
def qb_stats(pid):
    return _qb_stats_from(season_stats_by_player.get(pid, {}))

def rb_stats(pid):
    return _rb_stats_from(season_stats_by_player.get(pid, {}))

def wr_stats(pid):
    return _wr_stats_from(season_stats_by_player.get(pid, {}))

def k_stats(pid):
    return _k_stats_from(season_stats_by_player.get(pid, {}))

def def_stats(pid):
    return _def_stats_from(season_stats_by_player.get(pid, {}))

def team_logo_url(pid):
    # Team-Defenses sind in Sleeper über das Team-Kürzel (z.B. "SF") indiziert
    # und haben kein Spielerfoto - stattdessen das Team-Logo verwenden.
    return f"https://sleepercdn.com/images/team_logos/nfl/{pid.lower()}.png"

def build_roster_entries(ids, names, extra_stats_fn=None, image_url_fn=None):
    entries = []
    for pid, player_name in zip(ids, names):
        image_url = image_url_fn(pid) if image_url_fn else f"https://sleepercdn.com/content/nfl/players/{pid}.jpg"
        entry = {
            "name": player_name,
            "image_url": image_url,
            "total_pts": round(total_points_by_player.get(pid, 0), 1),
        }
        if extra_stats_fn:
            entry.update(extra_stats_fn(pid))
        entries.append(entry)
    return entries

# Initialize lists for data collection
user_ids, team_names, display_names = [], [], []
wins, losses, ties, points_for, points_against = [], [], [], [], []
adjusted_averages, trends, trend_percentages = [], [], []
# NEU: Sammel-Listen für die Badge-Berechnungen weiter unten
injury_counts, homer_team_list, homer_count_list = [], [], []
team_weekly_points_list = []
qb_list, rb_list, wr_list, te_list, k_list, def_list = [], [], [], [], [], []
qb_strength, rb_strength, wr_strength, te_strength, k_strength = [], [], [], [], []
top_performers_list, bottom_performers_list, benchwarmer_list = [], [], []
last_week_opponent_list, last_week_result_list = [], []
this_week_opponent_list, this_week_winprob_list = [], []

# Map user_id to team_name and display_name
user_data_dict = {
    user['user_id']: {
        'team_name': user.get('metadata', {}).get('team_name', 'No Team Name'),
        'display_name': user.get('display_name', 'No Display Name')
    }
    for user in users
}

# Collect weekly points
weekly_points = {week: [] for week in weeks}
weekly_results_by_roster = {r['roster_id']: [] for r in rosters}  # 'W'/'L'/'T' pro Woche, für Serien-Badges
current_week_matchups = None
for week in weeks:
    url_matchups = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    response_matchups = requests.get(url_matchups)
    matchups = response_matchups.json()

    if week == current_week:
        current_week_matchups = matchups  # für Performer- & Gegner-Auswertung weiter unten

    week_points = {matchup['roster_id']: matchup['points'] for matchup in matchups}
    for team in rosters:
        roster_id = team['roster_id']
        weekly_points[week].append(week_points.get(roster_id, 0))

    # NEU: Sieg/Niederlage pro Team fuer diese Woche ermitteln (Serien-Badges)
    matchup_groups = {}
    for m in matchups:
        matchup_groups.setdefault(m['matchup_id'], []).append(m)
    for pair in matchup_groups.values():
        if len(pair) == 2:
            a, b = pair
            a_pts, b_pts = a.get('points', 0) or 0, b.get('points', 0) or 0
            if a_pts > b_pts:
                res_a, res_b = 'W', 'L'
            elif b_pts > a_pts:
                res_a, res_b = 'L', 'W'
            else:
                res_a, res_b = 'T', 'T'
            weekly_results_by_roster.setdefault(a['roster_id'], []).append(res_a)
            weekly_results_by_roster.setdefault(b['roster_id'], []).append(res_b)

# --- NEU: Vorbereitung für Top/Flop-Performer, Benchwarmer, Gegner & Win-Probability ---

def fetch_matchups(week):
    try:
        r = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
        data = r.json()
        return data if data else None
    except Exception:
        return None

this_week = current_week + 1  # aktuell laufende/kommende Woche (current_week = letzte ABGESCHLOSSENE Woche)
this_week_matchups = fetch_matchups(this_week)

def build_opponent_map(matchup_list):
    """Baut roster_id -> gegnerische roster_id, basierend auf gleicher matchup_id."""
    if not matchup_list:
        return {}
    by_matchup_id = {}
    for m in matchup_list:
        by_matchup_id.setdefault(m['matchup_id'], []).append(m['roster_id'])
    opponent_map = {}
    for ids in by_matchup_id.values():
        if len(ids) == 2:
            opponent_map[ids[0]] = ids[1]
            opponent_map[ids[1]] = ids[0]
    return opponent_map

last_week_opponent_map = build_opponent_map(current_week_matchups)  # current_week_matchups = letzte abgeschlossene Woche
this_week_opponent_map = build_opponent_map(this_week_matchups)

roster_id_to_owner = {r['roster_id']: r['owner_id'] for r in rosters}

def team_display(roster_id):
    owner_id = roster_id_to_owner.get(roster_id)
    info = user_data_dict.get(owner_id, {})
    team_name = info.get('team_name', 'No Team Name')
    display_name = info.get('display_name', 'No Display Name')
    return display_name if team_name == 'No Team Name' else team_name

# Projections für die KOMMENDE Woche laden (inoffizieller, aber weit genutzter Sleeper-Endpoint)
projections_by_player = {}
try:
    proj_url = (
        f"https://api.sleeper.app/projections/nfl/{season}/{this_week}"
        "?season_type=regular&position[]=QB&position[]=RB&position[]=WR"
        "&position[]=TE&position[]=K&position[]=DEF"
    )
    proj_response = requests.get(proj_url)
    proj_data = proj_response.json()
    for entry in proj_data:
        pid = entry.get('player_id')
        stats = entry.get('stats', {}) or {}
        # Scoring-Format: Half-PPR bevorzugt, mit Fallback auf Standard bzw. PPR.
        pts = stats.get('pts_half_ppr', stats.get('pts_std', stats.get('pts_ppr', 0))) or 0
        if pid:
            projections_by_player[pid] = pts
except Exception as e:
    print(f"Projections konnten nicht geladen werden, Win-Probability wird neutral (50%) gesetzt: {e}")

# Streuung der bisherigen Wochenpunkte liga-weit (Basis für die Win-Probability)
all_played_scores = [pts for wk in weeks for pts in weekly_points[wk] if pts > 0]
league_stdev = statistics.pstdev(all_played_scores) if len(all_played_scores) >= 2 else 0
if league_stdev == 0:
    league_stdev = 15  # Fallback-Annahme für die sehr frühe Saisonphase

def player_info(pid):
    p = players.get(pid, {})
    name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid
    position = p.get('position', '')
    week_stats_raw = current_week_player_stats.get(pid, {})
    info = {
        "name": name,
        "position": position,
        "points": 0,
        "image_url": f"https://sleepercdn.com/content/nfl/players/{pid}.jpg",
        "total_pts": round(total_points_by_player.get(pid, 0), 1),
    }
    # NEU: hier bewusst die WOCHEN-Rohstats (nicht die Saison-Summe) nutzen -
    # Top/Flop/Benchwarmer sollen zeigen, was in DIESER Woche passiert ist.
    if position == 'QB':
        info.update(_qb_stats_from(week_stats_raw))
    elif position == 'RB':
        info.update(_rb_stats_from(week_stats_raw))
    elif position in ('WR', 'TE'):
        info.update(_wr_stats_from(week_stats_raw))
    elif position == 'K':
        info.update(_k_stats_from(week_stats_raw))
    elif position == 'DEF':
        info.update(_def_stats_from(week_stats_raw))
        info["image_url"] = team_logo_url(pid)
    return info

# Process each team's data
for team in rosters:
    user_id = team['owner_id']
    user_ids.append(user_id)
    team_names.append(user_data_dict.get(user_id, {}).get('team_name', 'No Team Name'))
    display_names.append(user_data_dict.get(user_id, {}).get('display_name', 'No Display Name'))

    wins.append(team['settings'].get('wins', 0))
    losses.append(team['settings'].get('losses', 0))
    ties.append(team['settings'].get('ties', 0))
    points_for.append(team['settings'].get('fpts', 0))
    points_against.append(team['settings'].get('fpts_against', 0))

    # Collect player names (fürs Roster) UND ids (für die PPG-Berechnung)
    qb_roster, rb_roster, wr_roster, te_roster, k_roster, def_roster = [], [], [], [], [], []
    qb_ids, rb_ids, wr_ids, te_ids, k_ids, def_ids = [], [], [], [], [], []
    injury_count = 0
    nfl_team_counts = {}
    for player_id in team['players']:
        if player_id in players:
            player = players[player_id]
            player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
            position = player.get('position', '')

            # NEU: Verletzungsstatus & NFL-Team für "The Hospital"/"[Team]-Homer"
            injury_status = player.get('injury_status')
            if injury_status in ('Out', 'IR', 'Questionable', 'Doubtful'):
                injury_count += 1
            nfl_team = player.get('team')
            if nfl_team:
                nfl_team_counts[nfl_team] = nfl_team_counts.get(nfl_team, 0) + 1

            if position == 'QB':
                qb_roster.append(player_name)
                qb_ids.append(player_id)
            elif position == 'RB':
                rb_roster.append(player_name)
                rb_ids.append(player_id)
            elif position == 'WR':
                wr_roster.append(player_name)
                wr_ids.append(player_id)
            elif position == 'TE':
                te_roster.append(player_name)
                te_ids.append(player_id)
            elif position == 'K':
                k_roster.append(player_name)
                k_ids.append(player_id)
            elif position == 'DEF':
                def_roster.append(player_name)
                def_ids.append(player_id)

    injury_counts.append(injury_count)
    if nfl_team_counts:
        top_nfl_team = max(nfl_team_counts, key=nfl_team_counts.get)
        homer_team_list.append(top_nfl_team)
        homer_count_list.append(nfl_team_counts[top_nfl_team])
    else:
        homer_team_list.append(None)
        homer_count_list.append(0)

    qb_list.append(build_roster_entries(qb_ids, qb_roster, qb_stats))
    rb_list.append(build_roster_entries(rb_ids, rb_roster, rb_stats))
    wr_list.append(build_roster_entries(wr_ids, wr_roster, wr_stats))
    te_list.append(build_roster_entries(te_ids, te_roster, wr_stats))
    k_list.append(build_roster_entries(k_ids, k_roster, k_stats))
    def_list.append(build_roster_entries(def_ids, def_roster, def_stats, image_url_fn=team_logo_url))

    # Positionsstärke jetzt auf Basis von Punkten pro Spiel (PPG) statt
    # Saison-Gesamtpunkten - fairer bei Verletzungspausen/späten Einstiegen.
    qb_strength.append(calculate_strength(qb_ids, 1))
    rb_strength.append(calculate_strength(rb_ids, 3))
    wr_strength.append(calculate_strength(wr_ids, 4))
    te_strength.append(calculate_strength(te_ids, 1))
    k_strength.append(calculate_strength(k_ids, 1))

    # Adjusted Average: remove highest and lowest scoring weeks
    team_weekly_points = [weekly_points[week][rosters.index(team)] for week in weeks if weekly_points[week][rosters.index(team)] > 0]
    team_weekly_points_list.append(team_weekly_points)
    if len(team_weekly_points) > 2:
        adjusted_points = sorted(team_weekly_points)[1:-1]
        adjusted_average = sum(adjusted_points) / len(adjusted_points) if adjusted_points else 0
    else:
        adjusted_average = 0

    adjusted_averages.append(round(adjusted_average, 1))

    # Trend: Vergleich der letzten 2 Wochen mit dem EIGENEN bisherigen Schnitt
    # (statt bisher mit dem Liga-Durchschnitt) - zeigt jetzt "besser/schlechter
    # als die eigene bisherige Form", nicht "besser/schlechter als die Liga".
    if len(team_weekly_points) > 2:
        baseline_weeks = team_weekly_points[:-2]
        own_baseline_average = sum(baseline_weeks) / len(baseline_weeks) if baseline_weeks else 0
        last_two_weeks_average = sum(team_weekly_points[-2:]) / 2

        if own_baseline_average > 0:
            trend_percentage = ((last_two_weeks_average - own_baseline_average) / own_baseline_average) * 100
        else:
            trend_percentage = 0

        if trend_percentage > 7:
            trend = "UP"
        elif trend_percentage < -7:
            trend = "DOWN"
        else:
            trend = "NO TREND"
    else:
        trend = "NO TREND"
        trend_percentage = 0

    trends.append(trend)
    trend_percentages.append(round(trend_percentage, 1))

    # --- NEU: Top/Flop-Performer, Benchwarmer, Gegner & Win-Probability ---
    roster_id = team['roster_id']
    match_entry = None  # letzte ABGESCHLOSSENE Woche
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == roster_id), None)

    top_performers, bottom_performers, benchwarmer = [], [], None

    if match_entry:
        starters = [s for s in match_entry.get('starters', []) if s and s != '0']
        players_points_week = match_entry.get('players_points', {}) or {}

        starter_scores = [(pid, players_points_week.get(pid, 0)) for pid in starters]
        sorted_desc = sorted(starter_scores, key=lambda x: x[1], reverse=True)
        sorted_asc = sorted(starter_scores, key=lambda x: x[1])

        for pid, pts in sorted_desc[:3]:
            info = player_info(pid)
            info['points'] = round(pts, 1)
            top_performers.append(info)

        for pid, pts in sorted_asc[:3]:
            info = player_info(pid)
            info['points'] = round(pts, 1)
            bottom_performers.append(info)

        # WICHTIG: für den Bank-Vergleich den tatsächlichen Kader DIESER Woche nehmen
        # (match_entry['players']), nicht den aktuellen Kader von heute - sonst
        # verfälschen zwischenzeitliche Waiver/Trades das Ergebnis.
        full_roster_that_week = match_entry.get('players') or team['players']
        bench_ids = [pid for pid in full_roster_that_week if pid not in starters]
        bench_scores = [(pid, players_points_week.get(pid, 0)) for pid in bench_ids]
        if bench_scores:
            best_bench_pid, best_bench_pts = max(bench_scores, key=lambda x: x[1])
            benchwarmer = player_info(best_bench_pid)
            benchwarmer['points'] = round(best_bench_pts, 1)

    top_performers_list.append(top_performers)
    bottom_performers_list.append(bottom_performers)
    benchwarmer_list.append(benchwarmer)

    # Gegner + Ergebnis der LETZTEN (abgeschlossenen) Woche
    last_opp_roster_id = last_week_opponent_map.get(roster_id)
    last_week_opponent_name = None
    last_week_result = None
    if last_opp_roster_id is not None and match_entry:
        last_week_opponent_name = team_display(last_opp_roster_id)
        opp_match_entry_last = next((m for m in current_week_matchups if m['roster_id'] == last_opp_roster_id), None)
        if opp_match_entry_last:
            own_pts = match_entry.get('points', 0)
            opp_pts = opp_match_entry_last.get('points', 0)
            if own_pts > opp_pts:
                outcome = "Sieg"
            elif own_pts < opp_pts:
                outcome = "Niederlage"
            else:
                outcome = "Unentschieden"
            last_week_result = {
                "own_points": round(own_pts, 1),
                "opponent_points": round(opp_pts, 1),
                "outcome": outcome
            }
    last_week_opponent_list.append(last_week_opponent_name)
    last_week_result_list.append(last_week_result)

    # Gegner DIESER (kommenden) Woche + Win-Probability (basierend auf Projections)
    this_opp_roster_id = this_week_opponent_map.get(roster_id)
    this_match_entry = None
    if this_week_matchups:
        this_match_entry = next((m for m in this_week_matchups if m['roster_id'] == roster_id), None)

    own_projected_total = 0
    if this_match_entry:
        this_week_starters = [s for s in this_match_entry.get('starters', []) if s and s != '0']
        own_projected_total = sum(projections_by_player.get(pid, 0) for pid in this_week_starters)

    if this_opp_roster_id is not None:
        this_week_opponent_name = team_display(this_opp_roster_id)
        opp_match_entry_this = None
        if this_week_matchups:
            opp_match_entry_this = next((m for m in this_week_matchups if m['roster_id'] == this_opp_roster_id), None)

        opp_projected_total = 0
        if opp_match_entry_this:
            opp_starters = [s for s in opp_match_entry_this.get('starters', []) if s and s != '0']
            opp_projected_total = sum(projections_by_player.get(pid, 0) for pid in opp_starters)

        diff = own_projected_total - opp_projected_total
        # Normalverteilungsannahme: Differenz zweier unabhängiger Team-Scores
        # mit jeweiliger Streuung league_stdev -> Win-Probability per CDF (erf).
        win_prob = 0.5 * (1 + math.erf(diff / (league_stdev * 2)))
        win_prob = max(0.01, min(0.99, win_prob))
        this_week_winprob_list.append(round(win_prob * 100, 1))
    else:
        this_week_opponent_name = None
        this_week_winprob_list.append(None)
    this_week_opponent_list.append(this_week_opponent_name)

# Normalize the strengths using the original normalization logic
def normalize_strength(strengths):
    max_value = max(strengths) if max(strengths) > 0 else 1
    return [round((strength / max_value) * 100) for strength in strengths]

qb_strength_normalized = normalize_strength(qb_strength)
rb_strength_normalized = normalize_strength(rb_strength)
wr_strength_normalized = normalize_strength(wr_strength)
te_strength_normalized = normalize_strength(te_strength)
k_strength_normalized = normalize_strength(k_strength)

# Create DataFrame
df = pd.DataFrame({
    "User ID": user_ids,
    "Display Name": display_names,
    "Team Name": team_names,
    "Wins": wins,
    "Losses": losses,
    "Ties": ties,
    "Points For": points_for,
    "Points Against": points_against,
    "Adjusted Average": adjusted_averages,
    "TREND": trends,
    "Trend Percentage": trend_percentages,
    "QB Strength": qb_strength_normalized,
    "RB Strength": rb_strength_normalized,
    "WR Strength": wr_strength_normalized,
    "TE Strength": te_strength_normalized,
    "K Strength": k_strength_normalized,
    "QB": qb_list,
    "RB": rb_list,
    "WR": wr_list,
    "TE": te_list,
    "K": k_list,
    "DEF": def_list,
    "TOP_PERFORMERS": top_performers_list,
    "BOTTOM_PERFORMERS": bottom_performers_list,
    "BENCHWARMER": benchwarmer_list,
    "LAST_WEEK_OPPONENT": last_week_opponent_list,
    "LAST_WEEK_RESULT": last_week_result_list,
    "THIS_WEEK_OPPONENT": this_week_opponent_list,
    "THIS_WEEK_WIN_PROB": this_week_winprob_list
})

# Power Rank calculations
power_rankings = pd.DataFrame()
power_rankings['Wins Rank'] = df['Wins'].rank(ascending=False)
power_rankings['Points For Rank'] = df['Points For'].rank(ascending=False)
power_rankings['Trend Percentage Rank'] = df['Trend Percentage'].rank(ascending=False)
power_rankings['Points Against Rank'] = df['Points Against'].rank(ascending=False)
power_rankings['Adjusted Average Rank'] = df['Adjusted Average'].rank(ascending=False)

power_rankings['Power Rank Score'] = (
    power_rankings['Wins Rank'] * 0.25 +
    power_rankings['Points For Rank'] * 0.25 +
    power_rankings['Trend Percentage Rank'] * 0.25 +
    power_rankings['Points Against Rank'] * 0.1 +
    power_rankings['Adjusted Average Rank'] * 0.15
)

df["POWER RANK"] = power_rankings['Power Rank Score'].rank(ascending=True).astype(int)
df["Power Rank Score"] = power_rankings['Power Rank Score'].round(2)

# --- NEU: Rang pro Position (1 = stärkstes Team der Liga in dieser Kategorie) ---
# Wird für die farbcodierte Bar-Chart-Anzeige gebraucht (Wert + Rang beim Tap/Hover)
df["QB Strength Rank"] = df["QB Strength"].rank(ascending=False, method='min').astype(int)
df["RB Strength Rank"] = df["RB Strength"].rank(ascending=False, method='min').astype(int)
df["WR Strength Rank"] = df["WR Strength"].rank(ascending=False, method='min').astype(int)
df["TE Strength Rank"] = df["TE Strength"].rank(ascending=False, method='min').astype(int)
df["K Strength Rank"] = df["K Strength"].rank(ascending=False, method='min').astype(int)

# NEU: Diese beiden Ränge werden intern schon für den Power-Rank-Score
# gebraucht - jetzt zusätzlich als eigene Spalten rausgeben, damit das
# Frontend Trend und AAvg mit demselben Rang-Farbschema (Blau bis Rot)
# einfärben kann wie die Teamstärke.
df["TREND Rank"] = power_rankings['Trend Percentage Rank'].astype(int)
df["Adjusted Average Rank"] = power_rankings['Adjusted Average Rank'].astype(int)

# --- NEU: Spaßige Badges pro Team ---
# Jedes Badge wird an genau EIN Team pro Kategorie vergeben (den "Sieger"
# dieser Kategorie), nicht an jedes Team, das eine Schwelle erreicht.
badges_list = [[] for _ in range(len(df))]

def add_badge(idx, icon, label, description):
    badges_list[idx].append({"icon": icon, "label": label, "description": description})

# 1) The Hospital - meiste verletzte Spieler (Out/IR/Questionable/Doubtful)
if injury_counts and max(injury_counts) > 0:
    idx = injury_counts.index(max(injury_counts))
    add_badge(
        idx, "🩹", "The Hospital",
        f"{injury_counts[idx]} verletzte Spieler im Kader (Out/IR/Questionable/Doubtful) - die größte Krankenstation der Liga."
    )

# 2) [NFL-Team]-Homer - auffällig viele Spieler von einem echten NFL-Team
if homer_count_list and max(homer_count_list) >= 3:
    idx = homer_count_list.index(max(homer_count_list))
    nfl_team_label = homer_team_list[idx]
    add_badge(
        idx, "🏟️", f"{nfl_team_label}-Homer",
        f"{homer_count_list[idx]} Spieler von {nfl_team_label} im Kader - eindeutig ein Fan."
    )

# 3) Pechvogel der Woche - verloren trotz Punkten über dem Liga-Median dieser Woche
week_scores_for_pech = weekly_points.get(current_week, [])
if week_scores_for_pech:
    median_score = statistics.median(week_scores_for_pech)
    pech_candidates = [
        i for i in range(len(df))
        if last_week_result_list[i] and last_week_result_list[i]["outcome"] == "Niederlage"
        and last_week_result_list[i]["own_points"] > median_score
    ]
    if pech_candidates:
        idx = max(pech_candidates, key=lambda i: last_week_result_list[i]["own_points"])
        add_badge(
            idx, "🍀", "Pechvogel der Woche",
            f"{last_week_result_list[idx]['own_points']} Punkte - mehr als die halbe Liga - und trotzdem verloren."
        )

# 4) Rising Star - stärkster positiver Trend
if trend_percentages and max(trend_percentages) > 7:
    idx = trend_percentages.index(max(trend_percentages))
    add_badge(
        idx, "📈", "Rising Star",
        f"Trend von +{trend_percentages[idx]}% - aktuell das heißeste Team der Liga."
    )

# 5) Free Fall - stärkster negativer Trend
if trend_percentages and min(trend_percentages) < -7:
    idx = trend_percentages.index(min(trend_percentages))
    add_badge(
        idx, "📉", "Free Fall",
        f"Trend von {trend_percentages[idx]}% - der Sinkflug hält an."
    )

# 6) Giant Killer - Sieg gegen ein deutlich besser platziertes Team
name_to_index = {}
for i in range(len(df)):
    label = team_names[i] if team_names[i] != 'No Team Name' else display_names[i]
    name_to_index[label] = i

giant_killer_candidates = []
for i in range(len(df)):
    res = last_week_result_list[i]
    if res and res["outcome"] == "Sieg":
        opp_idx = name_to_index.get(last_week_opponent_list[i])
        if opp_idx is not None:
            own_rank = df.loc[i, "POWER RANK"]
            opp_rank = df.loc[opp_idx, "POWER RANK"]
            if own_rank > opp_rank:  # höhere Zahl = schlechter platziert
                giant_killer_candidates.append((i, own_rank - opp_rank))
if giant_killer_candidates:
    idx, gap = max(giant_killer_candidates, key=lambda x: x[1])
    add_badge(
        idx, "💥", "Giant Killer",
        f"Sieg gegen ein {gap} Plätze besser platziertes Team - Überraschungscoup der Woche."
    )

# 7) Nervenstark - knappster Sieg der Woche
win_margins = [
    (i, last_week_result_list[i]["own_points"] - last_week_result_list[i]["opponent_points"])
    for i in range(len(df))
    if last_week_result_list[i] and last_week_result_list[i]["outcome"] == "Sieg"
]
if win_margins:
    idx, margin = min(win_margins, key=lambda x: x[1])
    add_badge(
        idx, "🎯", "Nervenstark",
        f"Sieg mit nur {round(margin, 1)} Punkten Vorsprung - knapper geht's kaum."
    )

# 8) On Fire / Cold Streak - aktuelle Sieg-/Niederlagenserie
def current_streak(roster_id):
    results = weekly_results_by_roster.get(roster_id, [])
    if not results:
        return None, 0
    last = results[-1]
    if last == 'T':
        return 'T', 1
    streak_len = 0
    for r in reversed(results):
        if r == last:
            streak_len += 1
        else:
            break
    return last, streak_len

streak_info = [current_streak(team['roster_id']) for team in rosters]
win_streaks = [(i, s) for i, (res, s) in enumerate(streak_info) if res == 'W']
loss_streaks = [(i, s) for i, (res, s) in enumerate(streak_info) if res == 'L']

if win_streaks:
    idx, s = max(win_streaks, key=lambda x: x[1])
    if s >= 2:
        add_badge(idx, "🔥", "On Fire", f"{s} Siege in Folge - aktuell nicht zu stoppen.")

if loss_streaks:
    idx, s = max(loss_streaks, key=lambda x: x[1])
    if s >= 2:
        add_badge(idx, "🥶", "Cold Streak", f"{s} Niederlagen in Folge - der Ofen ist aus.")

# 9) Rollercoaster / Mr. Consistent - Schwankung der Wochenpunkte
stdevs = [
    statistics.pstdev(pts) if len(pts) >= 3 else None
    for pts in team_weekly_points_list
]
valid_stdevs = [(i, s) for i, s in enumerate(stdevs) if s is not None]
if valid_stdevs:
    idx_high, s_high = max(valid_stdevs, key=lambda x: x[1])
    add_badge(idx_high, "🎢", "Rollercoaster", f"Schwankung von ±{round(s_high, 1)} Punkten pro Woche - nie langweilig.")
    idx_low, s_low = min(valid_stdevs, key=lambda x: x[1])
    add_badge(idx_low, "⚓", "Mr. Consistent", f"Nur ±{round(s_low, 1)} Punkte Schwankung - der Fels in der Brandung.")

# 10) Bankdrücker - meiste Punkte auf der Bank liegen gelassen
bench_scores = [(i, b["points"]) for i, b in enumerate(benchwarmer_list) if b]
if bench_scores:
    idx, pts = max(bench_scores, key=lambda x: x[1])
    add_badge(idx, "🪑", "Bankdrücker", f"{pts} Punkte auf der Bank liegen gelassen - autsch.")

# 11) Liga-Krösus - höchste Punktzahl der Woche ligaweit
scores_this_week = weekly_points.get(current_week, [])
if scores_this_week:
    idx = scores_this_week.index(max(scores_this_week))
    add_badge(idx, "👑", "Liga-Krösus", f"{scores_this_week[idx]} Punkte - Highscore der Liga in dieser Woche.")

df["BADGES"] = badges_list

df['COMMENTS'] = ""

# Kommentare werden jetzt aus dem veröffentlichten Google Sheet geladen
# (statt aus der lokalen PowerRanking_Text.csv). Die Tabelle enthält zur
# Orientierung auch "Display Name" - wir brauchen daraus nur "User ID" und "TEXT".
comments_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQCnrwSeNaWZpB01mPcy6Glr9vQPk_Vq6OtgxkqcSgCmNiK-yXVYpc7QbslQI9wulq5SHQ5vwijUzKx/pub?output=csv"
text_df = pd.read_csv(comments_sheet_url)

df['User ID'] = df['User ID'].astype(str)
text_df['User ID'] = text_df['User ID'].astype(str)

df = pd.merge(df, text_df[['User ID', 'TEXT']], on='User ID', how='left')
df['COMMENTS'] = df['TEXT']
df.drop(columns=['TEXT'], inplace=True)

# Wochenpunkte für den Saisonverlauf: dieselbe Quelle (weekly_points) wie für
# Trend und Adjusted Average - Spaltenname bekommt in der Vorsaison den
# Zusatz "(Vorsaison)" nur zur Anzeige, die Daten sind identisch zur echten
# Berechnung oben.
week_column_suffix = " (Vorsaison)" if using_previous_season_chart_data else ""
weekly_points_df = pd.DataFrame(weekly_points)
weekly_points_df.columns = [f'Week {week}{week_column_suffix}' for week in weeks]

df = pd.concat([df, weekly_points_df], axis=1)

# Eindeutiges Anzeige-Label fürs Frontend (statt Woche aus Spaltenanzahl zu raten)
df["DISPLAY_WEEK_LABEL"] = "Vorsaison" if using_previous_season_chart_data else f"Woche {current_week}"

# Save to CSV (weiterhin als Backup/Debug-Datei)
csv_file = "POWERRANK.csv"
df.to_csv(csv_file, index=False)
print(f"Standings data saved to {csv_file}")

# --- NEU: Direkter JSON-Export statt Online-Konverter-Tool ---
# Pfad ggf. anpassen, falls dieses Script nicht im Repo-Root liegt.
json_file = os.path.join("public", "powerrank.json")
df.to_json(json_file, orient="records", force_ascii=False, indent=2)
print(f"JSON data saved to {json_file}")
