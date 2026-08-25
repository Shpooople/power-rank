import requests
import pandas as pd
from datetime import datetime
import os
import math
import statistics
import json

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

# --- NEU: Echte Slot-Konfiguration der Liga laden (für flexible
# Positionsstärke UND "Perfektes Lineup" weiter unten) - statt hardcoded
# Annahmen wird die tatsächliche Anzahl QB/RB/WR/TE/FLEX/SUPER_FLEX-Slots
# aus den Liga-Einstellungen genutzt.
try:
    league_settings_info = requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()
    roster_positions = league_settings_info.get("roster_positions", [])
except Exception:
    roster_positions = []

NON_STARTING_SLOTS = {"BN", "IR", "TAXI"}
starting_slots = [p for p in roster_positions if p not in NON_STARTING_SLOTS]
FLEX_ELIGIBLE = {
    "FLEX": {"RB", "WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
}

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
# --- NEU: Flexible Positionsstärke statt hardcoded Spieleranzahl ---
# Nutzt dieselbe Slot-Logik wie "Perfektes Lineup" (echte Liga-Konfiguration
# aus roster_positions, inkl. FLEX/SUPER_FLEX), aber auf Basis der Saison-PPG
# statt einer einzelnen Woche. Ein RB, der einen FLEX-Slot belegt, zählt zur
# RB-Stärke - hat ein Team also 4 starke RBs, können alle 4 einfließen, wenn
# sie die besten verfügbaren Flex-Optionen sind. Gibt pro Position sowohl die
# Summe der PPG als auch die Anzahl der eingerechneten Spieler zurück (die
# Anzahl wird im Frontend neben dem Balken angezeigt).
def calculate_flexible_strength(team_players_by_pos):
    pool = []
    for pos, ids in team_players_by_pos.items():
        for pid in ids:
            pool.append((pid, pos, ppg(pid)))

    used = set()
    contribution = {pos: [] for pos in team_players_by_pos}
    specific_slots_local = [s for s in starting_slots if s not in FLEX_ELIGIBLE]
    flex_slots_local = [s for s in starting_slots if s in FLEX_ELIGIBLE]

    for slot in specific_slots_local:
        candidates = sorted(
            (p for p in pool if p[1] == slot and p[0] not in used),
            key=lambda p: p[2], reverse=True
        )
        if candidates:
            best = candidates[0]
            used.add(best[0])
            contribution[best[1]].append(best[2])

    for slot in flex_slots_local:
        eligible_positions = FLEX_ELIGIBLE[slot]
        candidates = sorted(
            (p for p in pool if p[1] in eligible_positions and p[0] not in used),
            key=lambda p: p[2], reverse=True
        )
        if candidates:
            best = candidates[0]
            used.add(best[0])
            contribution[best[1]].append(best[2])

    starters = {pos: (round(sum(vals), 1), len(vals)) for pos, vals in contribution.items()}

    # NEU: Statt Bank pro Einzelposition gibt es eine einzige "Bank"-Kennzahl:
    # die 3 besten übrig gebliebenen Flex-Spieler (RB/WR/TE), unabhängig von
    # der genauen Position - spiegelt am ehesten wider, wie stark die Bank
    # im Ernstfall (Verletzung eines Starters) einspringen könnte.
    flex_bench_candidates = sorted(
        (p for p in pool if p[0] not in used and p[1] in ("RB", "WR", "TE")),
        key=lambda p: p[2], reverse=True
    )
    top3 = flex_bench_candidates[:3]
    bench_flex = (round(sum(p[2] for p in top3), 1), len(top3))
    bank_pids = {p[0] for p in top3}

    return starters, bench_flex, used, bank_pids

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

def build_roster_entries(ids, names, extra_stats_fn=None, image_url_fn=None, my_guy_fn=None, my_guy_seasons_fn=None, in_bank_fn=None, in_strength_fn=None):
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
        if my_guy_fn:
            entry["my_guy"] = my_guy_fn(pid)
        if my_guy_seasons_fn:
            entry["my_guy_seasons"] = my_guy_seasons_fn(pid)
        if in_bank_fn:
            entry["in_bank"] = in_bank_fn(pid)
        if in_strength_fn:
            entry["in_strength"] = in_strength_fn(pid)
        entries.append(entry)
    return entries

# Initialize lists for data collection
user_ids, team_names, display_names = [], [], []
wins, losses, ties, points_for, points_against = [], [], [], [], []
adjusted_averages, trends, trend_percentages = [], [], []
# NEU: Sammel-Listen für die Badge-Berechnungen weiter unten
injury_counts, homer_team_counts_list = [], []
team_weekly_points_list = []
qb_list, rb_list, wr_list, te_list, k_list, def_list = [], [], [], [], [], []
qb_strength, rb_strength, wr_strength, te_strength, k_strength = [], [], [], [], []
qb_strength_count, rb_strength_count, wr_strength_count, te_strength_count, k_strength_count = [], [], [], [], []
bench_flex_strength, bench_flex_count = [], []
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

# --- NEU: FAAB-Kontostand - Gesamtbudget der Liga einmalig abrufen, pro
# Team wird davon dann settings.waiver_budget_used abgezogen.
try:
    _league_settings_for_faab = requests.get(f"https://api.sleeper.app/v1/league/{league_id}").json()
    total_faab_budget = (_league_settings_for_faab.get("settings", {}) or {}).get("waiver_budget", 100)
except Exception:
    total_faab_budget = 100
faab_remaining_list = []

# --- NEU: "My Guy" + Legacy-Stats - läuft über die komplette Liga-Historie
# via previous_league_id (bei dieser Liga bis 2021 zurück). Alles in EINER
# Schleife berechnet, um nicht mehrfach dieselben Wochen/Saisons abzurufen.
def fetch_json_safe(url):
    try:
        r = requests.get(url)
        return r.json()
    except Exception:
        return None

season_league_ids = []
season_labels = {}  # league_id (dieser Saison) -> Saison-Label, z.B. "2025"
_walk_id = league_id
_walk_info = fetch_json_safe(f"https://api.sleeper.app/v1/league/{_walk_id}")
while _walk_id:
    season_league_ids.append(_walk_id)
    season_labels[_walk_id] = _walk_info.get("season") if _walk_info else None
    _prev = _walk_info.get("previous_league_id") if _walk_info else None
    if not _prev:
        break
    _walk_info = fetch_json_safe(f"https://api.sleeper.app/v1/league/{_prev}")
    _walk_id = _prev

print(f"Liga-Historie: {len(season_league_ids)} Saison(s) gefunden.")

qualifying_seasons_count = {}  # (owner_id, player_id) -> Anzahl qualifizierender Saisons ("My Guy")

# NEU: Legacy-Stats, jeweils keyed auf owner_id (NICHT roster_id!) - das ist
# der Fix für den Win%-Bug: roster_id wird bei Sleeper pro Saison neu
# vergeben und kann bei einem Owner-Wechsel an eine andere Person gehen.
# owner_id bleibt dagegen fest an den jeweiligen Sleeper-Account gebunden,
# nur so lässt sich Historie korrekt einem Team zuordnen.
legacy_wins = {}       # owner_id -> {'wins':,'losses':,'ties':,'points_for':}
legacy_points_by_season = {}   # owner_id -> {season_label: points_for}
legacy_player_weeks = {}   # (owner_id, pid) -> Gesamtwochen im Roster (alle Saisons)
legacy_player_points = {}  # (owner_id, pid) -> Gesamtpunkte, die der Spieler FÜR dieses Team gemacht hat
legacy_season_rosters = {}  # owner_id -> {season_label: {pid, pid, ...}} - für Championship-Ringe
legacy_high_score = {}     # owner_id -> (points, season, week)
legacy_low_score = {}      # owner_id -> (points, season, week)
legacy_high_player_score = {}  # owner_id -> (points, player_name, season, week)
legacy_placements = {}     # owner_id -> [(season, placement), ...]
legacy_waiver_moves = {}   # owner_id -> Anzahl Adds (Waiver/Free Agent)
legacy_waiver_moves_by_season = {}  # owner_id -> {season_label: Anzahl}
legacy_trades = {}         # owner_id -> Anzahl Trades
legacy_trades_by_season = {}   # owner_id -> {season_label: Anzahl}
head_to_head = {}          # owner_id -> {gegner_owner_id: {'wins':,'losses':,'ties':}}
owner_id_to_name = {u.get('user_id'): u.get('display_name') for u in users}

for s_league_id in season_league_ids:
    season_label = season_labels.get(s_league_id, "?")
    s_rosters = fetch_json_safe(f"https://api.sleeper.app/v1/league/{s_league_id}/rosters") or []
    s_roster_to_owner = {r['roster_id']: r['owner_id'] for r in s_rosters}

    # Win/Loss/Tie/Punkte nur für den TATSÄCHLICHEN Owner dieser Saison verbuchen
    for r in s_rosters:
        owner_id = r.get('owner_id')
        if not owner_id:
            continue
        settings = r.get('settings', {}) or {}
        entry = legacy_wins.setdefault(owner_id, {'wins': 0, 'losses': 0, 'ties': 0, 'points_for': 0.0})
        season_points = settings.get('fpts', 0) + settings.get('fpts_decimal', 0) / 100
        legacy_points_by_season.setdefault(owner_id, {})[season_label] = round(season_points, 1)
        entry['wins'] += settings.get('wins', 0)
        entry['losses'] += settings.get('losses', 0)
        entry['ties'] += settings.get('ties', 0)
        entry['points_for'] += season_points

    # Platzierung dieser Saison (nur falls Playoffs schon abgeschlossen sind).
    # Playoff-Teams bekommen ihre Bracket-Platzierung, alle anderen (nicht in
    # den Playoffs) werden danach nach Wins/Punkten sortiert eingeordnet -
    # sonst fehlen genau diese Saisons komplett in der Durchschnitts-Platzierung.
    bracket = fetch_json_safe(f"https://api.sleeper.app/v1/league/{s_league_id}/winners_bracket") or []
    assigned_owners_this_season = set()
    max_place_this_season = 0
    for match in bracket:
        place = match.get('p')
        if not place:
            continue
        winner_owner = s_roster_to_owner.get(match.get('w'))
        loser_owner = s_roster_to_owner.get(match.get('l'))
        if winner_owner:
            legacy_placements.setdefault(winner_owner, []).append((season_label, place))
            assigned_owners_this_season.add(winner_owner)
        if loser_owner:
            legacy_placements.setdefault(loser_owner, []).append((season_label, place + 1))
            assigned_owners_this_season.add(loser_owner)
        max_place_this_season = max(max_place_this_season, place, place + 1)

    if bracket:  # nur wenn die Playoffs dieser Saison wirklich abgeschlossen sind
        remaining = [
            r for r in s_rosters
            if r.get('owner_id') and r['owner_id'] not in assigned_owners_this_season
        ]
        remaining.sort(
            key=lambda r: (
                r.get('settings', {}).get('wins', 0),
                r.get('settings', {}).get('fpts', 0)
            ),
            reverse=True
        )
        for offset, r in enumerate(remaining):
            legacy_placements.setdefault(r['owner_id'], []).append(
                (season_label, max_place_this_season + 1 + offset)
            )

    weeks_on_roster = {}  # (owner_id, player_id) -> Anzahl Wochen DIESE Saison
    for wk in range(1, 18):  # großzügig; nicht existierende Wochen liefern einfach leer
        s_matchups = fetch_json_safe(f"https://api.sleeper.app/v1/league/{s_league_id}/matchups/{wk}")
        if not s_matchups:
            continue
        for m in s_matchups:
            owner_id = s_roster_to_owner.get(m.get('roster_id'))
            if not owner_id:
                continue

            ppw_for_points = m.get('players_points', {}) or {}
            for pid in (m.get('players') or []):
                key = (owner_id, pid)
                weeks_on_roster[key] = weeks_on_roster.get(key, 0) + 1
                # NEU: tatsächliche Punkte, die dieser Spieler FÜR DIESES TEAM
                # gemacht hat (nicht nur Anwesenheit im Roster)
                legacy_player_points[key] = legacy_player_points.get(key, 0) + (ppw_for_points.get(pid, 0) or 0)
                # NEU: welche Spieler waren in dieser Saison bei diesem Owner
                # im Roster - für die Championship-Ring-Markierung gebraucht
                legacy_season_rosters.setdefault(owner_id, {}).setdefault(season_label, set()).add(pid)

            week_points = m.get('points')
            if week_points is not None:
                if owner_id not in legacy_high_score or week_points > legacy_high_score[owner_id][0]:
                    legacy_high_score[owner_id] = (week_points, season_label, wk)
                if owner_id not in legacy_low_score or week_points < legacy_low_score[owner_id][0]:
                    legacy_low_score[owner_id] = (week_points, season_label, wk)

            ppw = m.get('players_points', {}) or {}
            for pid, pts in ppw.items():
                if pts is None:
                    continue
                if owner_id not in legacy_high_player_score or pts > legacy_high_player_score[owner_id][0]:
                    p = players.get(pid, {})
                    p_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip() or pid
                    legacy_high_player_score[owner_id] = (pts, p_name, season_label, wk)

        # NEU: Head-to-Head - Matchups dieser Woche nach matchup_id paaren,
        # um zu wissen, wer gegen wen gespielt hat (nicht nur wer wie viele
        # Punkte gemacht hat).
        matchups_by_id = {}
        for m in s_matchups:
            mid = m.get('matchup_id')
            if mid is None:
                continue
            matchups_by_id.setdefault(mid, []).append(m)

        for mid, pair in matchups_by_id.items():
            if len(pair) != 2:
                continue
            a, b = pair
            owner_a = s_roster_to_owner.get(a.get('roster_id'))
            owner_b = s_roster_to_owner.get(b.get('roster_id'))
            pts_a, pts_b = a.get('points'), b.get('points')
            if not owner_a or not owner_b or pts_a is None or pts_b is None:
                continue
            rec_a = head_to_head.setdefault(owner_a, {}).setdefault(owner_b, {'wins': 0, 'losses': 0, 'ties': 0})
            rec_b = head_to_head.setdefault(owner_b, {}).setdefault(owner_a, {'wins': 0, 'losses': 0, 'ties': 0})
            if pts_a > pts_b:
                rec_a['wins'] += 1
                rec_b['losses'] += 1
            elif pts_b > pts_a:
                rec_b['wins'] += 1
                rec_a['losses'] += 1
            else:
                rec_a['ties'] += 1
                rec_b['ties'] += 1

        # Waiver-/Free-Agent-Moves und Trades dieser Woche zählen
        s_transactions = fetch_json_safe(f"https://api.sleeper.app/v1/league/{s_league_id}/transactions/{wk}") or []
        for tx in s_transactions:
            if tx.get('status') != 'complete':
                continue

            if tx.get('type') in ('waiver', 'free_agent'):
                adds = tx.get('adds') or {}
                for roster_id in set(adds.values()):
                    owner_id = s_roster_to_owner.get(roster_id)
                    if owner_id:
                        legacy_waiver_moves[owner_id] = legacy_waiver_moves.get(owner_id, 0) + 1
                        season_moves = legacy_waiver_moves_by_season.setdefault(owner_id, {})
                        season_moves[season_label] = season_moves.get(season_label, 0) + 1

            elif tx.get('type') == 'trade':
                involved_rosters = set(tx.get('roster_ids') or [])
                if not involved_rosters:
                    adds_t = tx.get('adds') or {}
                    drops_t = tx.get('drops') or {}
                    involved_rosters = set(adds_t.values()) | set(drops_t.values())
                for roster_id in involved_rosters:
                    owner_id = s_roster_to_owner.get(roster_id)
                    if owner_id:
                        legacy_trades[owner_id] = legacy_trades.get(owner_id, 0) + 1
                        season_trades = legacy_trades_by_season.setdefault(owner_id, {})
                        season_trades[season_label] = season_trades.get(season_label, 0) + 1

    for (owner_id, pid), wk_count in weeks_on_roster.items():
        if wk_count >= 3:
            qualifying_seasons_count[(owner_id, pid)] = qualifying_seasons_count.get((owner_id, pid), 0) + 1
        legacy_player_weeks[(owner_id, pid)] = legacy_player_weeks.get((owner_id, pid), 0) + wk_count

def is_my_guy(owner_id, pid):
    return qualifying_seasons_count.get((owner_id, pid), 0) >= 3

def my_guy_seasons(owner_id, pid):
    return qualifying_seasons_count.get((owner_id, pid), 0)

def get_legacy_stats(owner_id):
    """Baut das komplette Legacy-Stats-Paket für einen Owner."""
    wl = legacy_wins.get(owner_id, {'wins': 0, 'losses': 0, 'ties': 0, 'points_for': 0.0})
    games = wl['wins'] + wl['losses'] + wl['ties']
    win_pct = round(wl['wins'] / games * 100, 1) if games > 0 else None

    placements = sorted(legacy_placements.get(owner_id, []), key=lambda x: x[0], reverse=True)
    avg_placement = round(sum(p for _, p in placements) / len(placements), 1) if placements else None

    # NEU: Spieler, mit denen dieses Team eine Meisterschaft gewonnen hat
    # (Platzierung 1 in einer Saison) - die waren in dieser Saison laut
    # legacy_season_rosters im Kader. Bekommen im Frontend einen goldenen Ring.
    championship_seasons = [s for s, p in legacy_placements.get(owner_id, []) if p == 1]
    championship_pids = set()
    for s in championship_seasons:
        championship_pids |= legacy_season_rosters.get(owner_id, {}).get(s, set())

    def player_display_name(pid):
        return f"{players.get(pid, {}).get('first_name', '')} {players.get(pid, {}).get('last_name', '')}".strip() or pid

    def player_image(pid):
        # DEF-Einträge nutzen die Team-Abkürzung als pid (z.B. "SF") - dafür
        # braucht's das NFL-Team-Logo statt eines Spielerbilds.
        return (
            team_logo_url(pid) if players.get(pid, {}).get('position') == 'DEF'
            else f"https://sleepercdn.com/content/nfl/players/{pid}.jpg"
        )

    # NEU: zwei getrennte Top-5-Listen statt einer gemeinsamen Top-10 - einmal
    # nach Wochen im Roster, einmal nach tatsächlich für das Team erzielten
    # Punkten.
    most_weeks = sorted(
        ((pid, wks) for (o, pid), wks in legacy_player_weeks.items() if o == owner_id),
        key=lambda x: x[1], reverse=True
    )[:5]
    most_weeks_named = [
        {
            "name": player_display_name(pid),
            "weeks": wks,
            "image_url": player_image(pid),
            "is_champion": pid in championship_pids,
        }
        for pid, wks in most_weeks
    ]

    most_points = sorted(
        ((pid, pts) for (o, pid), pts in legacy_player_points.items() if o == owner_id),
        key=lambda x: x[1], reverse=True
    )[:5]
    most_points_named = [
        {
            "name": player_display_name(pid),
            "points": round(pts, 1),
            "image_url": player_image(pid),
            "is_champion": pid in championship_pids,
        }
        for pid, pts in most_points
    ]

    high = legacy_high_score.get(owner_id)
    low = legacy_low_score.get(owner_id)
    high_player = legacy_high_player_score.get(owner_id)

    # NEU: Angstgegner (schlägt uns am häufigsten) & Opfer (wir schlagen ihn
    # am häufigsten), aus der Head-to-Head-Historie. Wichtig: nach VERHÄLTNIS
    # (Winrate), nicht nach absoluter Anzahl - sonst gewinnt ein Gegner mit
    # vielen Spielen und 50% Quote fälschlich gegen einen mit wenigen Spielen,
    # aber 100% Quote. Eine Mindestanzahl an Spielen (3) verhindert außerdem,
    # dass ein einzelnes Spiel (zwangsläufig 100% oder 0%) den Titel gewinnt.
    opponents = head_to_head.get(owner_id, {})
    angstgegner, opfer = None, None
    if opponents:
        MIN_GAMES = 3

        def total_games(rec):
            return rec['wins'] + rec['losses'] + rec['ties']

        # Nur Gegner berücksichtigen, die aktuell noch in der Liga sind
        # (owner_id_to_name kennt nur die JETZIGEN Mitglieder) - ehemalige
        # Owner sollen nicht als Angstgegner/Opfer auftauchen.
        current_opponents = {oid: rec for oid, rec in opponents.items() if oid in owner_id_to_name}

        qualified = {oid: rec for oid, rec in current_opponents.items() if total_games(rec) >= MIN_GAMES}
        pool = qualified if qualified else current_opponents  # Fallback, falls Liga noch zu jung ist

        if pool:
            worst = max(pool.items(), key=lambda kv: kv[1]['losses'] / total_games(kv[1]), default=(None, None))
            if worst[0] and worst[1]['losses'] > 0:
                angstgegner = {
                    "name": owner_id_to_name.get(worst[0], "Unbekannt"),
                    "wins": worst[1]['losses'], "losses": worst[1]['wins'], "ties": worst[1]['ties'],
                }
            best = max(pool.items(), key=lambda kv: kv[1]['wins'] / total_games(kv[1]), default=(None, None))
            if best[0] and best[1]['wins'] > 0:
                opfer = {
                    "name": owner_id_to_name.get(best[0], "Unbekannt"),
                    "wins": best[1]['wins'], "losses": best[1]['losses'], "ties": best[1]['ties'],
                }

    return {
        "win_pct": win_pct,
        "wins": wl['wins'], "losses": wl['losses'], "ties": wl['ties'],
        "all_time_points": round(wl['points_for'], 1) if games > 0 else None,
        "points_by_season": sorted(
            [{"season": s, "points": p} for s, p in legacy_points_by_season.get(owner_id, {}).items()],
            key=lambda x: x["season"], reverse=True
        ),
        "avg_placement": avg_placement,
        "most_weeks": most_weeks_named,
        "most_points": most_points_named,
        "waiver_moves": legacy_waiver_moves.get(owner_id, 0),
        "waiver_moves_by_season": sorted(
            [{"season": s, "count": c} for s, c in legacy_waiver_moves_by_season.get(owner_id, {}).items()],
            key=lambda x: x["season"], reverse=True
        ),
        "trades": legacy_trades.get(owner_id, 0),
        "trades_by_season": sorted(
            [{"season": s, "count": c} for s, c in legacy_trades_by_season.get(owner_id, {}).items()],
            key=lambda x: x["season"], reverse=True
        ),
        "placements": [{"season": s, "place": p} for s, p in placements],
        "high_week": ({"points": high[0], "season": high[1], "week": high[2]} if high else None),
        "low_week": ({"points": low[0], "season": low[1], "week": low[2]} if low else None),
        "high_player_week": (
            {"points": high_player[0], "player": high_player[1], "season": high_player[2], "week": high_player[3]}
            if high_player else None
        ),
        "angstgegner": angstgegner,
        "opfer": opfer,
    }

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
    faab_remaining_list.append(total_faab_budget - team['settings'].get('waiver_budget_used', 0))

    # NEU: Sleeper liefert über /rosters (team['players']) IMMER nur den
    # aktuellen/letzten Kader-Stand - bei einer bereits beendeten Saison also
    # den Stand nach den Playoffs, nicht den Stand der jeweils angezeigten
    # Woche. Der Matchup-Eintrag dieser Woche (current_week_matchups) hat
    # dagegen sein eigenes 'players'-Feld, das den Kader GENAU zum Zeitpunkt
    # dieser Woche zeigt - das ist die historisch korrekte Quelle.
    current_match_entry = None
    if current_week_matchups:
        current_match_entry = next(
            (m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None
        )
    if current_match_entry and current_match_entry.get('players'):
        roster_player_ids = current_match_entry['players']
    else:
        roster_player_ids = team['players']

    # Collect player names (fürs Roster) UND ids (für die PPG-Berechnung)
    qb_roster, rb_roster, wr_roster, te_roster, k_roster, def_roster = [], [], [], [], [], []
    qb_ids, rb_ids, wr_ids, te_ids, k_ids, def_ids = [], [], [], [], [], []
    injury_count = 0
    nfl_team_counts = {}
    for player_id in roster_player_ids:
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
    homer_team_counts_list.append(nfl_team_counts)

    # Positionsstärke jetzt flexibel auf Basis der echten Liga-Slots (inkl.
    # FLEX/SUPER_FLEX) und Punkten pro Spiel (PPG) statt hardcoded Anzahl -
    # siehe calculate_flexible_strength() weiter oben. Zusätzlich Bankstärke
    # (Team-Depth) aus denselben Spielern, die NICHT in der Startaufstellung
    # gebraucht wurden.
    flex_result, bench_flex_summary, strength_used_pids, bank_pids = calculate_flexible_strength({
        "QB": qb_ids, "RB": rb_ids, "WR": wr_ids, "TE": te_ids, "K": k_ids, "DEF": def_ids,
    })
    qb_pts, qb_cnt = flex_result.get("QB", (0, 0))
    rb_pts, rb_cnt = flex_result.get("RB", (0, 0))
    wr_pts, wr_cnt = flex_result.get("WR", (0, 0))
    te_pts, te_cnt = flex_result.get("TE", (0, 0))
    k_pts, k_cnt = flex_result.get("K", (0, 0))

    qb_strength.append(qb_pts)
    rb_strength.append(rb_pts)
    wr_strength.append(wr_pts)
    te_strength.append(te_pts)
    k_strength.append(k_pts)

    qb_strength_count.append(qb_cnt)
    rb_strength_count.append(rb_cnt)
    wr_strength_count.append(wr_cnt)
    te_strength_count.append(te_cnt)
    k_strength_count.append(k_cnt)

    bp, bc = bench_flex_summary
    bench_flex_strength.append(bp)
    bench_flex_count.append(bc)

    # NEU: fürs Roster - Bank-Label nur für die tatsächlichen Top-3-Bank-
    # Spieler, gedimmt alle anderen, die nicht in die Teamstärke einfließen
    # (weder Starter-Slot noch Top-3-Bank).
    in_bank_fn = lambda pid: pid in bank_pids
    in_strength_fn = lambda pid: pid in strength_used_pids

    qb_list.append(build_roster_entries(qb_ids, qb_roster, qb_stats, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))
    rb_list.append(build_roster_entries(rb_ids, rb_roster, rb_stats, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))
    wr_list.append(build_roster_entries(wr_ids, wr_roster, wr_stats, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))
    te_list.append(build_roster_entries(te_ids, te_roster, wr_stats, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))
    k_list.append(build_roster_entries(k_ids, k_roster, k_stats, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))
    def_list.append(build_roster_entries(def_ids, def_roster, def_stats, image_url_fn=team_logo_url, my_guy_fn=lambda pid: is_my_guy(user_id, pid), my_guy_seasons_fn=lambda pid: my_guy_seasons(user_id, pid), in_bank_fn=in_bank_fn, in_strength_fn=in_strength_fn))

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
bench_flex_normalized = normalize_strength(bench_flex_strength)

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
    "QB Strength Count": qb_strength_count,
    "RB Strength Count": rb_strength_count,
    "WR Strength Count": wr_strength_count,
    "TE Strength Count": te_strength_count,
    "K Strength Count": k_strength_count,
    "Bench Strength": bench_flex_normalized,
    "Bench Strength Count": bench_flex_count,
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

# --- NEU: Wochen-Historie & Rang-Bewegung gegenüber der letzten archivierten Woche ---
HISTORY_DIR = "public/history"
INDEX_FILE = os.path.join(HISTORY_DIR, "index.json")
os.makedirs(HISTORY_DIR, exist_ok=True)

try:
    with open(INDEX_FILE, encoding="utf-8") as f:
        history_index = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    history_index = []

# Vorwoche innerhalb DERSELBEN Saison finden (Woche 1 einer Saison hat nie
# eine Vorwoche - saisonübergreifend zu vergleichen ergibt keinen Sinn).
same_season_entries = [e for e in history_index if e["season"] == season]
previous_rank_by_user = {}
if current_week > 1 and same_season_entries:
    matching_previous = [e for e in same_season_entries if e["week"] == current_week - 1]
    if matching_previous:
        latest_previous = matching_previous[0]
        try:
            with open(os.path.join(HISTORY_DIR, latest_previous["file"]), encoding="utf-8") as f:
                previous_data = json.load(f)
            previous_rank_by_user = {rec["User ID"]: rec["POWER RANK"] for rec in previous_data}
        except Exception as e:
            print(f"Vorherige Historie-Datei konnte nicht gelesen werden: {e}")

def rank_delta_for(user_id, current_rank):
    prev_rank = previous_rank_by_user.get(str(user_id))
    if prev_rank is None:
        return None
    return prev_rank - current_rank  # positiv = aufgestiegen, negativ = gefallen

df["LAST_WEEK_POWER_RANK"] = df["User ID"].apply(lambda uid: previous_rank_by_user.get(str(uid)))
df["POWER_RANK_DELTA"] = df.apply(lambda row: rank_delta_for(row["User ID"], row["POWER RANK"]), axis=1)

# Archivieren nur beim automatischen Zeitplan-Lauf (siehe update-rankings.yml),
# damit manuelle Testläufe die Historie nicht verfälschen.
# Archivieren nur beim automatischen Zeitplan-Lauf UND nur mit echten
# Saison-Daten - solange nur der Vorsaison-Fallback aktiv ist, gibt es
# nichts Sinnvolles zu archivieren.
should_archive = os.environ.get("ARCHIVE_SNAPSHOT") == "true" and not using_previous_season_chart_data

# --- NEU: Rang pro Position (1 = stärkstes Team der Liga in dieser Kategorie) ---
# Wird für die farbcodierte Bar-Chart-Anzeige gebraucht (Wert + Rang beim Tap/Hover)
df["QB Strength Rank"] = df["QB Strength"].rank(ascending=False, method='min').astype(int)
df["RB Strength Rank"] = df["RB Strength"].rank(ascending=False, method='min').astype(int)
df["WR Strength Rank"] = df["WR Strength"].rank(ascending=False, method='min').astype(int)
df["TE Strength Rank"] = df["TE Strength"].rank(ascending=False, method='min').astype(int)
df["K Strength Rank"] = df["K Strength"].rank(ascending=False, method='min').astype(int)
df["Bench Strength Rank"] = df["Bench Strength"].rank(ascending=False, method='min').astype(int)

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

def add_badge(idx, icon, label, description, image_url=None):
    badge = {"icon": icon, "label": label, "description": description}
    if image_url:
        badge["image_url"] = image_url
    badges_list[idx].append(badge)

# 1) The Hospital - meiste verletzte Spieler (Out/IR/Questionable/Doubtful)
if injury_counts and max(injury_counts) > 0:
    idx = injury_counts.index(max(injury_counts))
    add_badge(
        idx, "hospital", "The Hospital",
        f"{injury_counts[idx]} verletzte Spieler im Kader (Out/IR/Questionable/Doubtful) - die größte Krankenstation der Liga."
    )

# 2) [NFL-Team]-Homer - auffällig viele Spieler von einem echten NFL-Team
# Ein Team kann hier mehrere Badges bekommen (z.B. Cowboys-Homer UND Bears-Homer)
for i, team_counts in enumerate(homer_team_counts_list):
    for nfl_team_label, count in team_counts.items():
        if count >= 3:
            add_badge(
                i, "homer", f"{nfl_team_label}-Homer",
                f"{count} Spieler von {nfl_team_label} im Kader - eindeutig ein Fan.",
                image_url=team_logo_url(nfl_team_label)
            )

# 2b) [NFL-Team]-Superfan - noch eine Stufe drüber (5+ Spieler von einem Team).
# Bekommt im Frontend einen goldenen Rand statt des normalen Rahmens (icon "superfan").
for i, team_counts in enumerate(homer_team_counts_list):
    for nfl_team_label, count in team_counts.items():
        if count >= 5:
            add_badge(
                i, "superfan", f"{nfl_team_label}-Superfan",
                f"{count} Spieler von {nfl_team_label} im Kader - das nennt man Hingabe.",
                image_url=team_logo_url(nfl_team_label)
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
            idx, "unlucky", "Pechvogel der Woche",
            f"{last_week_result_list[idx]['own_points']} Punkte - mehr als die halbe Liga - und trotzdem verloren."
        )

# 4) Rising Star - stärkster positiver Trend
if trend_percentages and max(trend_percentages) > 7:
    idx = trend_percentages.index(max(trend_percentages))
    add_badge(
        idx, "rising", "Rising Star",
        f"Trend von +{trend_percentages[idx]}% - aktuell das heißeste Team der Liga."
    )

# 5) Free Fall - stärkster negativer Trend
if trend_percentages and min(trend_percentages) < -7:
    idx = trend_percentages.index(min(trend_percentages))
    add_badge(
        idx, "falling", "Free Fall",
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
        idx, "giant_killer", "Giant Killer",
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
        idx, "clutch", "Nervenstark",
        f"Sieg mit nur {round(margin, 1)} Punkten Vorsprung - knapper geht's kaum."
    )

# 7b) Kantersieg - größter Punkteabstand bei einem Sieg
if win_margins:
    idx, margin = max(win_margins, key=lambda x: x[1])
    add_badge(
        idx, "hammer", "Kantersieg",
        f"Sieg mit {round(margin, 1)} Punkten Vorsprung - eine klare Machtdemonstration."
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
        add_badge(idx, "fire", "On Fire", f"{s} Siege in Folge - aktuell nicht zu stoppen.")

if loss_streaks:
    idx, s = max(loss_streaks, key=lambda x: x[1])
    if s >= 2:
        add_badge(idx, "cold", "Cold Streak", f"{s} Niederlagen in Folge - der Ofen ist aus.")

# 9) Rollercoaster / Mr. Consistent - Schwankung der Wochenpunkte
stdevs = [
    statistics.pstdev(pts) if len(pts) >= 3 else None
    for pts in team_weekly_points_list
]
valid_stdevs = [(i, s) for i, s in enumerate(stdevs) if s is not None]
if valid_stdevs:
    idx_high, s_high = max(valid_stdevs, key=lambda x: x[1])
    add_badge(idx_high, "rollercoaster", "Rollercoaster", f"Schwankung von ±{round(s_high, 1)} Punkten pro Woche - nie langweilig.")
    idx_low, s_low = min(valid_stdevs, key=lambda x: x[1])
    add_badge(idx_low, "consistent", "Mr. Consistent", f"Nur ±{round(s_low, 1)} Punkte Schwankung - der Fels in der Brandung.")

# 10) Bankdrücker - meiste Punkte auf der Bank liegen gelassen
bench_scores = [(i, b["points"]) for i, b in enumerate(benchwarmer_list) if b]
if bench_scores:
    idx, pts = max(bench_scores, key=lambda x: x[1])
    add_badge(idx, "bench", "Bankdrücker", f"{pts} Punkte auf der Bank liegen gelassen - autsch.")

# 11) Liga-Krösus - höchste Punktzahl der Woche ligaweit
scores_this_week = weekly_points.get(current_week, [])
if scores_this_week:
    idx = scores_this_week.index(max(scores_this_week))
    add_badge(idx, "crown", "Liga-Krösus", f"{scores_this_week[idx]} Punkte - Highscore der Liga in dieser Woche.")

# 12) Bank-Patzer - Bankspieler hätte den Starter derselben Position überboten
bench_blunder_candidates = []
for i, team in enumerate(rosters):
    match_entry = None
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None)
    if not match_entry:
        continue
    starters = [s for s in match_entry.get('starters', []) if s and s != '0']
    ppw = match_entry.get('players_points', {}) or {}
    # NEU: historisch korrekter Kader dieser Woche statt aktueller Stand
    week_roster_ids = match_entry.get('players') or team['players']
    bench_ids = [pid for pid in week_roster_ids if pid not in starters]

    best_diff = 0
    for starter_pid in starters:
        starter_pos = players.get(starter_pid, {}).get('position')
        if not starter_pos:
            continue
        starter_pts = ppw.get(starter_pid, 0)
        for bench_pid in bench_ids:
            if players.get(bench_pid, {}).get('position') == starter_pos:
                diff = ppw.get(bench_pid, 0) - starter_pts
                if diff > best_diff:
                    best_diff = diff
    if best_diff > 0:
        bench_blunder_candidates.append((i, best_diff))

if bench_blunder_candidates:
    idx, diff = max(bench_blunder_candidates, key=lambda x: x[1])
    add_badge(
        idx, "blunder", "Bank-Patzer",
        f"Ein Bankspieler hätte {round(diff, 1)} Punkte mehr gebracht als der Starter auf derselben Position."
    )

# 13) Perfektes Lineup - Aufstellung nahe der bestmöglichen aus dem Kader
# Vereinfachung: greedy statt exakter Optimierung (spezifische Slots zuerst,
# dann FLEX-Slots) - in seltenen Grenzfällen nicht zu 100% exakt optimal,
# aber eine sehr gute Annäherung.
# (roster_positions/starting_slots/FLEX_ELIGIBLE werden jetzt zentral ganz
# oben im Script geladen - werden dort auch für die flexible Positionsstärke
# gebraucht.)

def optimal_lineup_points(team, match_entry):
    if not match_entry or not starting_slots:
        return None
    ppw = match_entry.get('players_points', {}) or {}
    # NEU: historisch korrekter Kader dieser Woche statt aktueller Stand
    week_roster_ids = match_entry.get('players') or team['players']
    pool = [
        (pid, players.get(pid, {}).get('position'), ppw.get(pid, 0))
        for pid in week_roster_ids if pid in players
    ]
    used = set()
    total = 0
    specific_slots = [s for s in starting_slots if s not in FLEX_ELIGIBLE]
    flex_slots = [s for s in starting_slots if s in FLEX_ELIGIBLE]

    for slot in specific_slots:
        candidates = sorted(
            (p for p in pool if p[1] == slot and p[0] not in used),
            key=lambda p: p[2], reverse=True
        )
        if candidates:
            best = candidates[0]
            used.add(best[0])
            total += best[2]

    for slot in flex_slots:
        eligible_positions = FLEX_ELIGIBLE[slot]
        candidates = sorted(
            (p for p in pool if p[1] in eligible_positions and p[0] not in used),
            key=lambda p: p[2], reverse=True
        )
        if candidates:
            best = candidates[0]
            used.add(best[0])
            total += best[2]

    return total

lineup_efficiency_candidates = []
for i, team in enumerate(rosters):
    match_entry = None
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None)
    if not match_entry:
        continue
    starters = [s for s in match_entry.get('starters', []) if s and s != '0']
    ppw = match_entry.get('players_points', {}) or {}
    actual_points = sum(ppw.get(pid, 0) for pid in starters)
    optimal_points = optimal_lineup_points(team, match_entry)
    if optimal_points and optimal_points > 0:
        lineup_efficiency_candidates.append((i, actual_points / optimal_points))

if lineup_efficiency_candidates:
    idx, eff = max(lineup_efficiency_candidates, key=lambda x: x[1])
    # Die Greedy-Näherung für "optimal" ist in seltenen Grenzfällen nicht zu
    # 100% exakt - dadurch könnte die tatsächliche Aufstellung sie knapp
    # übertreffen (>100%). Das ist logisch nicht sinnvoll, daher deckeln.
    eff_capped = min(eff, 1.0)
    if eff_capped >= 0.97:
        add_badge(
            idx, "perfect", "Perfektes Lineup",
            f"{round(eff_capped * 100, 1)}% der bestmöglichen Aufstellung ausgeschöpft - kaum Verbesserungspotenzial."
        )

# 14) Big Bang / Totalausfall - stärkste/schwächste Einzelperformance ligaweit
all_starter_scores = []
for i, team in enumerate(rosters):
    match_entry = None
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None)
    if not match_entry:
        continue
    starters = [s for s in match_entry.get('starters', []) if s and s != '0']
    ppw = match_entry.get('players_points', {}) or {}
    for pid in starters:
        all_starter_scores.append((i, pid, ppw.get(pid, 0)))

if all_starter_scores:
    top_i, top_pid, top_pts = max(all_starter_scores, key=lambda x: x[2])
    top_name = f"{players.get(top_pid, {}).get('first_name', '')} {players.get(top_pid, {}).get('last_name', '')}".strip()
    add_badge(top_i, "bigbang", "Big Bang", f"{top_name} mit {top_pts} Punkten - die stärkste Einzelleistung der Liga diese Woche.")

    bottom_i, bottom_pid, bottom_pts = min(all_starter_scores, key=lambda x: x[2])
    bottom_name = f"{players.get(bottom_pid, {}).get('first_name', '')} {players.get(bottom_pid, {}).get('last_name', '')}".strip()
    add_badge(bottom_i, "bust", "Totalausfall", f"{bottom_name} mit nur {bottom_pts} Punkten - schwächste Starter-Leistung der Liga diese Woche.")

# 15) Angstgegner - höchster Punkteschnitt der Saison bisher
season_averages = [
    (i, sum(pts) / len(pts)) for i, pts in enumerate(team_weekly_points_list) if pts
]
if season_averages:
    idx, avg = max(season_averages, key=lambda x: x[1])
    add_badge(idx, "dragon", "Angstgegner", f"{round(avg, 1)} Punkte Schnitt pro Woche - das Team, das niemand gerne trifft.")

# 16) Punktgenau - Sieg als klar besser platziertes Team (Favoritensieg bestätigt)
favorite_win_candidates = []
for i in range(len(df)):
    res = last_week_result_list[i]
    if res and res["outcome"] == "Sieg":
        opp_idx = name_to_index.get(last_week_opponent_list[i])
        if opp_idx is not None:
            own_rank = df.loc[i, "POWER RANK"]
            opp_rank = df.loc[opp_idx, "POWER RANK"]
            if own_rank < opp_rank:  # besser platziert und trotzdem gewonnen - erwartungsgemäß
                favorite_win_candidates.append((i, opp_rank - own_rank))
if favorite_win_candidates:
    idx, gap = max(favorite_win_candidates, key=lambda x: x[1])
    add_badge(idx, "lock", "Punktgenau", f"Sieg gegen ein {gap} Plätze schlechter platziertes Team - der Favorit hat geliefert.")

# 17) Waiver-Wire-Wizard - meiste Waiver-/Free-Agent-Adds der Saison
transaction_counts = {r['roster_id']: 0 for r in rosters}
try:
    for wk in weeks:
        tx_response = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/transactions/{wk}")
        tx_data = tx_response.json() or []
        for tx in tx_data:
            if tx.get('type') in ('waiver', 'free_agent') and tx.get('status') == 'complete':
                adds = tx.get('adds') or {}
                for pid, roster_id in adds.items():
                    if roster_id in transaction_counts:
                        transaction_counts[roster_id] += 1
except Exception as e:
    print(f"Transaktionen konnten nicht geladen werden: {e}")

if transaction_counts and max(transaction_counts.values()) > 0:
    top_roster_id = max(transaction_counts, key=transaction_counts.get)
    idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == top_roster_id), None)
    if idx is not None:
        add_badge(
            idx, "wizard", "Waiver-Wire-Wizard",
            f"{transaction_counts[top_roster_id]} Waiver-Adds diese Saison - der fleißigste Kader-Bastler der Liga."
        )

# 18) Air Raid / Ground and Pound - welcher Positionsgruppe verdankt das Team
# den Großteil seiner Wochenpunkte? Basis: nur die Starter dieser Woche.
if current_week_matchups:
    for m in current_week_matchups:
        idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == m['roster_id']), None)
        if idx is None:
            continue
        starters = [s for s in m.get('starters', []) if s and s != '0']
        ppw = m.get('players_points', {}) or {}
        total_pts = sum(ppw.get(pid, 0) for pid in starters)
        if not total_pts:
            continue
        pos_pts = {}
        for pid in starters:
            pos = players.get(pid, {}).get('position')
            pos_pts[pos] = pos_pts.get(pos, 0) + ppw.get(pid, 0)
        wr_share = pos_pts.get('WR', 0) / total_pts
        rb_share = pos_pts.get('RB', 0) / total_pts
        if wr_share >= 0.4:
            add_badge(
                idx, "airraid", "Air Raid",
                f"{round(wr_share * 100, 1)}% der Punkte diese Woche kamen von den WRs - reine Luftshow."
            )
        if rb_share >= 0.4:
            add_badge(
                idx, "groundpound", "Ground and Pound",
                f"{round(rb_share * 100, 1)}% der Punkte diese Woche kamen von den RBs - volle Kontrolle am Boden."
            )

# 19) Touchdown Overflow - meiste Touchdowns (Starter) der vergangenen Woche
if current_week_matchups:
    td_counts = []
    for m in current_week_matchups:
        idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == m['roster_id']), None)
        if idx is None:
            continue
        starters = [s for s in m.get('starters', []) if s and s != '0']
        total_td = 0
        for pid in starters:
            stats = current_week_player_stats.get(pid, {})
            total_td += (
                (stats.get('pass_td', 0) or 0)
                + (stats.get('rush_td', 0) or 0)
                + (stats.get('rec_td', 0) or 0)
                + (stats.get('def_td', 0) or 0)
            )
        td_counts.append((idx, total_td))
    if td_counts:
        top_idx, top_td = max(td_counts, key=lambda x: x[1])
        if top_td > 0:
            add_badge(
                top_idx, "touchdown", "Touchdown Overflow",
                f"{int(top_td)} Touchdowns in der vergangenen Woche - der meiste Endzonen-Spaß der Liga."
            )

# 20) "Klingeling, hier kommt der Eiermann" - ein Starter mit 0 Punkten
if current_week_matchups:
    for m in current_week_matchups:
        idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == m['roster_id']), None)
        if idx is None:
            continue
        starters = [s for s in m.get('starters', []) if s and s != '0']
        ppw = m.get('players_points', {}) or {}
        zero_players = [pid for pid in starters if ppw.get(pid, 0) == 0]
        if zero_players:
            names = []
            for pid in zero_players:
                p = players.get(pid, {})
                name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
                names.append(name if name else pid)
            add_badge(
                idx, "egg", "Klingeling, hier kommt der Eiermann",
                f"{', '.join(names)} mit 0 Punkten in der Startaufstellung - ein Ei gelegt."
            )

# 21) "Das heißt nicht umsonst FOOTball" - Kicker war besser als der beste
# RB ODER der beste WR ODER der QB im eigenen Lineup diese Woche
if current_week_matchups:
    for m in current_week_matchups:
        idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == m['roster_id']), None)
        if idx is None:
            continue
        starters = [s for s in m.get('starters', []) if s and s != '0']
        ppw = m.get('players_points', {}) or {}
        kicker_pts, rb_pts, wr_pts, qb_pts = None, [], [], []
        for pid in starters:
            pos = players.get(pid, {}).get('position')
            pts = ppw.get(pid, 0)
            if pos == 'K':
                kicker_pts = pts if kicker_pts is None else max(kicker_pts, pts)
            elif pos == 'RB':
                rb_pts.append(pts)
            elif pos == 'WR':
                wr_pts.append(pts)
            elif pos == 'QB':
                qb_pts.append(pts)
        if kicker_pts is not None:
            beaten = []
            if rb_pts and kicker_pts > max(rb_pts):
                beaten.append(f"jeden Running Back ({max(rb_pts)} Pkt.)")
            if wr_pts and kicker_pts > max(wr_pts):
                beaten.append(f"jeden Wide Receiver ({max(wr_pts)} Pkt.)")
            if qb_pts and kicker_pts > max(qb_pts):
                beaten.append(f"den Quarterback ({max(qb_pts)} Pkt.)")
            if beaten:
                add_badge(
                    idx, "footboot", "Das heißt nicht umsonst FOOTball",
                    f"Der Kicker war mit {kicker_pts} Punkten besser als {' und '.join(beaten)}."
                )

# 21b) "Defense wins Championships" - DEF war besser als der beste RB ODER
# der beste WR ODER der QB im eigenen Lineup diese Woche
if current_week_matchups:
    for m in current_week_matchups:
        idx = next((i for i, r in enumerate(rosters) if r['roster_id'] == m['roster_id']), None)
        if idx is None:
            continue
        starters = [s for s in m.get('starters', []) if s and s != '0']
        ppw = m.get('players_points', {}) or {}
        def_pts, rb_pts_d, wr_pts_d, qb_pts_d = None, [], [], []
        for pid in starters:
            pos = players.get(pid, {}).get('position')
            pts = ppw.get(pid, 0)
            if pos == 'DEF':
                def_pts = pts if def_pts is None else max(def_pts, pts)
            elif pos == 'RB':
                rb_pts_d.append(pts)
            elif pos == 'WR':
                wr_pts_d.append(pts)
            elif pos == 'QB':
                qb_pts_d.append(pts)
        if def_pts is not None:
            beaten_d = []
            if rb_pts_d and def_pts > max(rb_pts_d):
                beaten_d.append(f"jeden Running Back ({max(rb_pts_d)} Pkt.)")
            if wr_pts_d and def_pts > max(wr_pts_d):
                beaten_d.append(f"jeden Wide Receiver ({max(wr_pts_d)} Pkt.)")
            if qb_pts_d and def_pts > max(qb_pts_d):
                beaten_d.append(f"den Quarterback ({max(qb_pts_d)} Pkt.)")
            if beaten_d:
                add_badge(
                    idx, "shield", "Defense wins Championships",
                    f"Die Defense war mit {def_pts} Punkten besser als {' und '.join(beaten_d)}."
                )

# 22) Reichstes/Ärmstes Team - FAAB-Restbudget
if faab_remaining_list:
    max_faab = max(faab_remaining_list)
    min_faab = min(faab_remaining_list)
    richest_indices = [i for i, v in enumerate(faab_remaining_list) if v == max_faab]
    poorest_indices = [i for i, v in enumerate(faab_remaining_list) if v == min_faab]

    # Bei Gleichstand bekommt KEIN Team das Reichstes-Team-Badge
    if len(richest_indices) == 1:
        add_badge(
            richest_indices[0], "money", "Reichstes Team",
            f"{int(max_faab)} FAAB übrig - der Wal der Liga."
        )

    # Ärmstes Team: bei Gleichstand bekommen alle betroffenen Teams das Badge
    for idx in poorest_indices:
        add_badge(
            idx, "ruin", "Ärmstes Team",
            f"Nur noch {int(min_faab)} FAAB übrig - Waiver-Wire-Bettler."
        )

# 23) Kindergarten - meiste Rookies im Kader (years_exp == 0 laut Sleeper)
# NEU: historisch korrekter Kader dieser Woche statt aktueller Stand
rookie_counts = []
for team in rosters:
    match_entry = None
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None)
    week_roster_ids = (match_entry.get('players') if match_entry else None) or team.get('players', [])
    count = sum(
        1 for pid in week_roster_ids
        if players.get(pid, {}).get('years_exp') == 0
    )
    rookie_counts.append(count)

if rookie_counts and max(rookie_counts) > 0:
    idx = rookie_counts.index(max(rookie_counts))
    add_badge(
        idx, "kindergarten", "Kindergarten",
        f"{rookie_counts[idx]} Rookies im Kader - die Zukunft der Liga (hoffentlich)."
    )

# 24) Altersheim - ältester Kader im Schnitt (Sleeper liefert 'age' pro Spieler,
# nicht bei jedem Spieler vorhanden - nur Spieler mit bekanntem Alter zählen)
# NEU: historisch korrekter Kader dieser Woche statt aktueller Stand
avg_ages = []
for team in rosters:
    match_entry = None
    if current_week_matchups:
        match_entry = next((m for m in current_week_matchups if m['roster_id'] == team['roster_id']), None)
    week_roster_ids = (match_entry.get('players') if match_entry else None) or team.get('players', [])
    ages = [
        players.get(pid, {}).get('age')
        for pid in week_roster_ids
        if players.get(pid, {}).get('age') is not None
    ]
    avg_ages.append(sum(ages) / len(ages) if ages else None)

valid_avg_ages = [(i, a) for i, a in enumerate(avg_ages) if a is not None]
if valid_avg_ages:
    idx, oldest_avg = max(valid_avg_ages, key=lambda x: x[1])
    add_badge(
        idx, "oldfolks", "Altersheim",
        f"Durchschnittsalter {round(oldest_avg, 1)} Jahre - der erfahrenste Kader der Liga."
    )

df["BADGES"] = badges_list

df['COMMENTS'] = ""
df['FAAB_REMAINING'] = faab_remaining_list
legacy_list = [get_legacy_stats(team['owner_id']) for team in rosters]

# NEU: Ligaweiter Rang für die Legacy-Stats (außer "Meistgehaltene Spieler",
# da eine Rangliste dort wenig Sinn ergibt).
def add_rank(key, ascending=False):
    indexed = [(i, ls[key]) for i, ls in enumerate(legacy_list) if ls.get(key) is not None]
    indexed.sort(key=lambda x: x[1], reverse=not ascending)
    for rank, (i, _) in enumerate(indexed, start=1):
        legacy_list[i][f"{key}_rank"] = rank

def add_nested_rank(key, subkey, out_key, ascending=False):
    indexed = [(i, ls[key][subkey]) for i, ls in enumerate(legacy_list) if ls.get(key)]
    indexed.sort(key=lambda x: x[1], reverse=not ascending)
    for rank, (i, _) in enumerate(indexed, start=1):
        legacy_list[i][out_key] = rank

add_rank("win_pct", ascending=False)
add_rank("waiver_moves", ascending=False)
add_rank("trades", ascending=False)
add_rank("all_time_points", ascending=False)
add_rank("avg_placement", ascending=True)  # niedrigere Zahl = bessere Platzierung
add_nested_rank("high_week", "points", "high_week_rank", ascending=False)
add_nested_rank("low_week", "points", "low_week_rank", ascending=True)
add_nested_rank("high_player_week", "points", "high_player_week_rank", ascending=False)

df['LEGACY_STATS'] = legacy_list

# --- NEU: Prediction-Quiz-Score einbinden ---
# Kombinierte Export-Tabelle aus dem Prediction-Quiz-Sheet (Tab "QuizExport":
# Sleeper User ID, Telegram Name, Score - dort schon per VLOOKUP aus Mapping +
# OVERVIEW zusammengebaut). Pro Team werden Owner UND Co-Owner berücksichtigt,
# da beim Quiz individuell abgestimmt wird - eine Karte kann also mehrere
# Scores zeigen.
quiz_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSMFN74Gpnh950sftetagsv9m8ZTEqKpUNpIi22VdM6Ogg9m9Tvs9YKn5Y1jhK2l5noY6HhwHeb7Ysz/pub?gid=1194237017&single=true&output=csv"
try:
    quiz_df = pd.read_csv(quiz_sheet_url)
    quiz_df['Sleeper User ID'] = quiz_df['Sleeper User ID'].astype(str)

    quiz_scores_by_team = []
    for team in rosters:
        owner_ids = [str(team['owner_id'])] + [str(c) for c in (team.get('co_owners') or [])]
        matches = quiz_df[quiz_df['Sleeper User ID'].isin(owner_ids)]
        entries = [
            {"name": row['Telegram Name'], "score": row['Score']}
            for _, row in matches.iterrows()
        ]
        quiz_scores_by_team.append(entries)

    df["QUIZ_SCORES"] = quiz_scores_by_team
except Exception as e:
    print(f"Quiz-Scores konnten nicht geladen werden: {e}")
    df["QUIZ_SCORES"] = [[] for _ in range(len(df))]

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

# --- NEU: Wochen-Snapshot archivieren (nur beim automatischen Zeitplan-Lauf) ---
if should_archive:
    week_label = "Vorsaison" if using_previous_season_chart_data else f"Woche {current_week}"
    history_filename = f"{season}-week-{current_week}.json"
    history_path = os.path.join(HISTORY_DIR, history_filename)
    df.to_json(history_path, orient="records", force_ascii=False, indent=2)

    history_index = [
        e for e in history_index if not (e["season"] == season and e["week"] == current_week)
    ]
    history_index.append({
        "season": season,
        "week": current_week,
        "file": history_filename,
        "label": f"{season} - {week_label}",
    })
    history_index.sort(key=lambda e: (e["season"], e["week"]))
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(history_index, f, indent=2)

    print(f"Woche archiviert: {history_path}")
else:
    reason = "Vorsaison-Fallback aktiv (noch keine echten Saison-Daten)" if using_previous_season_chart_data else "kein Zeitplan-Lauf"
    print(f"Kein Archiv-Lauf ({reason}) - Historie bleibt unverändert.")
