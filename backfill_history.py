import requests
import pandas as pd
import json
import os

# --- Hier die zu befüllenden Saisons/Ligen eintragen ---
SEASONS_TO_BACKFILL = [
    {"season": "2024", "league_id": "1091796858659381248"},
    {"season": "2025", "league_id": "1238466927777546240"},
]

HISTORY_DIR = "public/history"
INDEX_FILE = os.path.join(HISTORY_DIR, "index.json")
os.makedirs(HISTORY_DIR, exist_ok=True)

try:
    with open(INDEX_FILE, encoding="utf-8") as f:
        history_index = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    history_index = []


def team_display_name(team_name, display_name):
    return display_name if team_name == "No Team Name" else team_name


for season_info in SEASONS_TO_BACKFILL:
    season = season_info["season"]
    league_id = season_info["league_id"]

    print(f"--- Bearbeite Saison {season} (Liga {league_id}) ---")

    rosters = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/rosters").json()
    users = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/users").json()

    user_data_dict = {
        u['user_id']: {
            'team_name': u.get('metadata', {}).get('team_name', 'No Team Name'),
            'display_name': u.get('display_name', 'No Display Name')
        }
        for u in users
    }
    roster_owner = {r['roster_id']: r['owner_id'] for r in rosters}
    roster_ids = [r['roster_id'] for r in rosters]

    # Kumulative Zähler pro roster_id, werden Woche für Woche fortgeschrieben
    wins = {rid: 0 for rid in roster_ids}
    losses = {rid: 0 for rid in roster_ids}
    ties = {rid: 0 for rid in roster_ids}
    points_for = {rid: 0.0 for rid in roster_ids}
    points_against = {rid: 0.0 for rid in roster_ids}
    weekly_points_history = {rid: [] for rid in roster_ids}

    week = 1
    max_weeks = 18  # Sicherheitsgrenze, Abbruch erfolgt vorher automatisch
    while week <= max_weeks:
        resp = requests.get(f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}")
        matchups = resp.json() or []
        if not matchups:
            print(f"  Keine Daten mehr für Woche {week} - Saison {season} endet bei Woche {week - 1}.")
            break

        week_points = {m['roster_id']: m.get('points', 0) or 0 for m in matchups}
        for rid in roster_ids:
            weekly_points_history[rid].append(week_points.get(rid, 0))

        # Sieg/Niederlage/Unentschieden + Punkte je Matchup-Paar
        matchup_groups = {}
        for m in matchups:
            matchup_groups.setdefault(m['matchup_id'], []).append(m)

        for pair in matchup_groups.values():
            if len(pair) == 2:
                a, b = pair
                a_id, b_id = a['roster_id'], b['roster_id']
                a_pts, b_pts = a.get('points', 0) or 0, b.get('points', 0) or 0
                points_for[a_id] += a_pts
                points_for[b_id] += b_pts
                points_against[a_id] += b_pts
                points_against[b_id] += a_pts
                if a_pts > b_pts:
                    wins[a_id] += 1
                    losses[b_id] += 1
                elif b_pts > a_pts:
                    wins[b_id] += 1
                    losses[a_id] += 1
                else:
                    ties[a_id] += 1
                    ties[b_id] += 1

        # --- Adjusted Average & Trend pro Team, Stand nach dieser Woche ---
        adjusted_averages = {}
        trends = {}
        trend_percentages = {}

        for rid in roster_ids:
            played = [p for p in weekly_points_history[rid] if p > 0]

            if len(played) > 2:
                adjusted_points = sorted(played)[1:-1]
                adj_avg = sum(adjusted_points) / len(adjusted_points) if adjusted_points else 0
            else:
                adj_avg = 0
            adjusted_averages[rid] = round(adj_avg, 1)

            if len(played) > 2:
                baseline_weeks = played[:-2]
                own_baseline_avg = sum(baseline_weeks) / len(baseline_weeks) if baseline_weeks else 0
                last_two_avg = sum(played[-2:]) / 2
                trend_pct = ((last_two_avg - own_baseline_avg) / own_baseline_avg) * 100 if own_baseline_avg > 0 else 0
                if trend_pct > 7:
                    trend = "UP"
                elif trend_pct < -7:
                    trend = "DOWN"
                else:
                    trend = "NO TREND"
            else:
                trend = "NO TREND"
                trend_pct = 0
            trends[rid] = trend
            trend_percentages[rid] = round(trend_pct, 1)

        # --- Power Rank (gleiche Gewichtung wie im Live-Script) ---
        df_week = pd.DataFrame({
            "roster_id": roster_ids,
            "Wins": [wins[rid] for rid in roster_ids],
            "Points For": [points_for[rid] for rid in roster_ids],
            "Points Against": [points_against[rid] for rid in roster_ids],
            "Trend Percentage": [trend_percentages[rid] for rid in roster_ids],
            "Adjusted Average": [adjusted_averages[rid] for rid in roster_ids],
        })

        pr = pd.DataFrame()
        pr['Wins Rank'] = df_week['Wins'].rank(ascending=False)
        pr['Points For Rank'] = df_week['Points For'].rank(ascending=False)
        pr['Trend Percentage Rank'] = df_week['Trend Percentage'].rank(ascending=False)
        pr['Points Against Rank'] = df_week['Points Against'].rank(ascending=False)
        pr['Adjusted Average Rank'] = df_week['Adjusted Average'].rank(ascending=False)
        pr['Power Rank Score'] = (
            pr['Wins Rank'] * 0.25 +
            pr['Points For Rank'] * 0.25 +
            pr['Trend Percentage Rank'] * 0.25 +
            pr['Points Against Rank'] * 0.1 +
            pr['Adjusted Average Rank'] * 0.15
        )
        df_week['POWER RANK'] = pr['Power Rank Score'].rank(ascending=True).astype(int)
        df_week['Power Rank Score'] = pr['Power Rank Score'].round(2)

        power_rank_by_roster = {
            rid: int(v) for rid, v in zip(df_week['roster_id'], df_week['POWER RANK'])
        }
        power_score_by_roster = {
            rid: float(v) for rid, v in zip(df_week['roster_id'], df_week['Power Rank Score'])
        }

        # --- Rang-Bewegung ggü. der zuletzt gespeicherten Woche (auch aus diesem Lauf) ---
        previous_entries = [e for e in history_index if not (e["season"] == season and e["week"] == week)]
        previous_rank_by_user = {}
        if previous_entries:
            latest_previous = sorted(previous_entries, key=lambda e: (e["season"], e["week"]))[-1]
            try:
                with open(os.path.join(HISTORY_DIR, latest_previous["file"]), encoding="utf-8") as f:
                    previous_data = json.load(f)
                previous_rank_by_user = {rec["User ID"]: rec["POWER RANK"] for rec in previous_data}
            except Exception as e:
                print(f"  Vorwoche konnte nicht gelesen werden: {e}")

        records = []
        for rid in roster_ids:
            owner_id = roster_owner.get(rid)
            info = user_data_dict.get(owner_id, {"team_name": "No Team Name", "display_name": "No Display Name"})
            prev_rank = previous_rank_by_user.get(str(owner_id))
            current_rank = power_rank_by_roster[rid]
            delta = (prev_rank - current_rank) if prev_rank is not None else None

            record = {
                "User ID": str(owner_id),
                "Display Name": info['display_name'],
                "Team Name": info['team_name'],
                "Wins": wins[rid],
                "Losses": losses[rid],
                "Ties": ties[rid],
                "Points For": round(points_for[rid], 2),
                "Points Against": round(points_against[rid], 2),
                "Adjusted Average": adjusted_averages[rid],
                "TREND": trends[rid],
                "Trend Percentage": trend_percentages[rid],
                "POWER RANK": current_rank,
                "Power Rank Score": power_score_by_roster[rid],
                "LAST_WEEK_POWER_RANK": prev_rank,
                "POWER_RANK_DELTA": delta,
                "DISPLAY_WEEK_LABEL": f"Woche {week}",
            }
            for i, wk_pts in enumerate(weekly_points_history[rid], start=1):
                record[f"Week {i}"] = wk_pts

            records.append(record)

        history_filename = f"{season}-week-{week}.json"
        history_path = os.path.join(HISTORY_DIR, history_filename)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        history_index = [e for e in history_index if not (e["season"] == season and e["week"] == week)]
        history_index.append({
            "season": season,
            "week": week,
            "file": history_filename,
            "label": f"{season} - Woche {week}",
        })

        print(f"  Woche {week} gespeichert ({len(records)} Teams)")
        week += 1

print("Alle Saisons verarbeitet.")

history_index.sort(key=lambda e: (e["season"], e["week"]))
with open(INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(history_index, f, indent=2, ensure_ascii=False)

print("Backfill abgeschlossen - index.json aktualisiert.")
