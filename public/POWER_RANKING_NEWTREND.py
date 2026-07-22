import requests
import pandas as pd
from datetime import datetime

# Set the current week (or determine it dynamically)
current_week = 11  # Replace this with the actual current week of the season

# Sleeper API for fetching rosters, players, etc.
league_id = "1238466927777546240"
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

# CSV URLs for player points by position
csv_urls = {
    'QB': 'https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players/2025/QB_season.csv',
    'RB': 'https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players/2025/RB_season.csv',
    'WR': 'https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players/2025/WR_season.csv',
    'TE': 'https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players/2025/TE_season.csv',
    'K': 'https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players/2025/K_season.csv',
}

# Fetch player points from CSVs
position_points = {}
for position, url in csv_urls.items():
    df = pd.read_csv(url)
    position_points[position] = dict(zip(df['PlayerName'], df['TotalPoints']))

# Helper function to calculate position strength based on total points
def calculate_strength(roster, position_dict, num_players):
    player_points = []
    for player_name in roster:
        if player_name in position_dict:
            total_points = position_dict[player_name]
            player_points.append(total_points)
    player_points.sort(reverse=True)
    return int(sum(player_points[:num_players]))  # Sum of the top 'num_players'

# Initialize lists for data collection
user_ids, team_names, display_names = [], [], []
wins, losses, ties, points_for, points_against = [], [], [], [], []
adjusted_averages, trends, trend_percentages = [], [], []
qb_list, rb_list, wr_list, te_list, k_list, def_list = [], [], [], [], [], []
qb_strength, rb_strength, wr_strength, te_strength, k_strength = [], [], [], [], []

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
for week in weeks:
    url_matchups = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"
    response_matchups = requests.get(url_matchups)
    matchups = response_matchups.json()

    week_points = {matchup['roster_id']: matchup['points'] for matchup in matchups}
    for team in rosters:
        roster_id = team['roster_id']
        weekly_points[week].append(week_points.get(roster_id, 0))

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

    # Collect player names for each position
    qb_roster, rb_roster, wr_roster, te_roster, k_roster, def_roster = [], [], [], [], [], []
    for player_id in team['players']:
        if player_id in players:
            player = players[player_id]
            player_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip()
            position = player.get('position', '')

            if position == 'QB':
                qb_roster.append(player_name)
            elif position == 'RB':
                rb_roster.append(player_name)
            elif position == 'WR':
                wr_roster.append(player_name)
            elif position == 'TE':
                te_roster.append(player_name)
            elif position == 'K':
                k_roster.append(player_name)
            elif position == 'DEF':
                def_roster.append(player_name)

    qb_list.append(", ".join(qb_roster))
    rb_list.append(", ".join(rb_roster))
    wr_list.append(", ".join(wr_roster))
    te_list.append(", ".join(te_roster))
    k_list.append(", ".join(k_roster))
    def_list.append(", ".join(def_roster))

    # Calculate strengths using the original logic
    qb_strength.append(calculate_strength(qb_roster, position_points['QB'], 1))
    rb_strength.append(calculate_strength(rb_roster, position_points['RB'], 3))
    wr_strength.append(calculate_strength(wr_roster, position_points['WR'], 4))
    te_strength.append(calculate_strength(te_roster, position_points['TE'], 1))
    k_strength.append(calculate_strength(k_roster, position_points['K'], 1))

    # Adjusted Average: remove highest and lowest scoring weeks
    team_weekly_points = [weekly_points[week][rosters.index(team)] for week in weeks if weekly_points[week][rosters.index(team)] > 0]
    if len(team_weekly_points) > 2:
        adjusted_points = sorted(team_weekly_points)[1:-1]
        adjusted_average = sum(adjusted_points) / len(adjusted_points) if adjusted_points else 0
    else:
        adjusted_average = 0

    adjusted_averages.append(round(adjusted_average, 1))

    # Calculate Trend and Trend Percentage using the updated logic
    if len(team_weekly_points) > 2:
        # Calculate the league's average for remaining weeks (excluding last two weeks)
        all_teams_scores = [
            weekly_points[week][i]
            for week in weeks[:-2]  # Exclude last two weeks
            for i in range(len(rosters))
        ]
        league_average = sum(all_teams_scores) / len(all_teams_scores) if all_teams_scores else 0
        last_two_weeks_average = sum(team_weekly_points[-2:]) / 2

        if league_average > 0:
            trend_percentage = ((last_two_weeks_average - league_average) / league_average) * 100
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

# Normalize the strengths using the original normalization logic
def normalize_strength(strengths):
    max_value = max(strengths) if max(strengths) > 0 else 1
    return [round((strength / max_value) * 100) for strength in strengths]

# Apply normalization
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
    "DEF": def_list
})

# Power Rank calculations
power_rankings = pd.DataFrame()
power_rankings['Wins Rank'] = df['Wins'].rank(ascending=False)
power_rankings['Points For Rank'] = df['Points For'].rank(ascending=False)
power_rankings['Trend Percentage Rank'] = df['Trend Percentage'].rank(ascending=False)
power_rankings['Points Against Rank'] = df['Points Against'].rank(ascending=False)
power_rankings['Adjusted Average Rank'] = df['Adjusted Average'].rank(ascending=False)

# Calculate Power Rank Score with the appropriate weight
power_rankings['Power Rank Score'] = (
    power_rankings['Wins Rank'] * 0.25 +
    power_rankings['Points For Rank'] * 0.25 +
    power_rankings['Trend Percentage Rank'] * 0.25 +
    power_rankings['Points Against Rank'] * 0.1 +
    power_rankings['Adjusted Average Rank'] * 0.15
)

# Calculate Power Rank based on Power Rank Score
df["POWER RANK"] = power_rankings['Power Rank Score'].rank(ascending=True).astype(int)
df["Power Rank Score"] = power_rankings['Power Rank Score'].round(2)

# Add empty 'COMMENTS' column
df['COMMENTS'] = ""

# Load the PowerRanking_Text.csv file
text_df = pd.read_csv('PowerRanking_Text.csv')

# Ensure 'User ID' in both dataframes are of the same type (convert to string for consistency)
df['User ID'] = df['User ID'].astype(str)
text_df['User ID'] = text_df['User ID'].astype(str)

# Merge the TEXT from PowerRanking_Text.csv with the main df based on 'User ID'
df = pd.merge(df, text_df[['User ID', 'TEXT']], on='User ID', how='left')

# Assign the TEXT column to the COMMENTS column
df['COMMENTS'] = df['TEXT']

# Drop the TEXT column after merging (optional)
df.drop(columns=['TEXT'], inplace=True)

# Convert the weekly points dictionary into a DataFrame
weekly_points_df = pd.DataFrame(weekly_points)
weekly_points_df.columns = [f'Week {week}' for week in weeks]

# Merge the weekly points with the main DataFrame
df = pd.concat([df, weekly_points_df], axis=1)

# Save to CSV
csv_file = "POWERRANK.csv"
df.to_csv(csv_file, index=False)

print(f"Standings data saved to {csv_file}")

