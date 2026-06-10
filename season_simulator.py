import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import json

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

# 2026 Vegas win totals from DraftKings (May 18, 2026)
VEGAS_WIN_TOTALS = {
    'ARI': 4.5,  'ATL': 6.5,  'BAL': 11.5, 'BUF': 10.5,
    'CAR': 7.5,  'CHI': 9.5,  'CIN': 9.5,  'CLE': 6.5,
    'DAL': 9.5,  'DEN': 9.5,  'DET': 10.5, 'GB':  10.5,
    'HOU': 9.5,  'IND': 7.5,  'JAX': 8.5,  'KC':  10.5,
    'LA':  11.5, 'LAC': 10.5, 'LV':  5.5,  'MIA': 4.5,
    'MIN': 10.5, 'NE':  10.5, 'NO':  8.5,  'NYG': 7.5,
    'NYJ': 5.5,  'PHI': 10.5, 'PIT': 9.5,  'SEA': 10.5,
    'SF':  10.5, 'TB':  9.5,  'TEN': 7.5,  'WAS': 9.5,
}

# NFL divisions
DIVISIONS = {
    'AFC East':  ['BUF', 'MIA', 'NE',  'NYJ'],
    'AFC North': ['BAL', 'CIN', 'CLE', 'PIT'],
    'AFC South': ['HOU', 'IND', 'JAX', 'TEN'],
    'AFC West':  ['DEN', 'KC',  'LV',  'LAC'],
    'NFC East':  ['DAL', 'NYG', 'PHI', 'WAS'],
    'NFC North': ['CHI', 'DET', 'GB',  'MIN'],
    'NFC South': ['ATL', 'CAR', 'NO',  'TB'],
    'NFC West':  ['ARI', 'LA',  'SF',  'SEA'],
}

TEAM_TO_CONF = {}
TEAM_TO_DIV = {}
for div, teams in DIVISIONS.items():
    conf = div.split()[0]
    for t in teams:
        TEAM_TO_CONF[t] = conf
        TEAM_TO_DIV[t] = div

# Convert Vegas win totals to strength rating
# League average is 8.5 wins, normalize around 0
avg_wins = 8.5
TEAM_STRENGTH = {
    team: (wins - avg_wins) / 17
    for team, wins in VEGAS_WIN_TOTALS.items()
}

print("2026 Team Strengths (from Vegas win totals):")
for team, strength in sorted(TEAM_STRENGTH.items(), key=lambda x: x[1], reverse=True):
    print(f"  {team}: {strength:+.3f} (projected {VEGAS_WIN_TOTALS[team]} wins)")

def simulate_game(home_team, away_team):
    home_strength = TEAM_STRENGTH.get(home_team, 0)
    away_strength = TEAM_STRENGTH.get(away_team, 0)
    # Home field advantage worth ~0.03 strength points
    home_edge = (home_strength - away_strength) + 0.03
    win_prob = 1 / (1 + np.exp(-home_edge * 8))
    win_prob = np.clip(win_prob, 0.1, 0.9)
    return np.random.random() < win_prob

def generate_schedule():
    # Generate a simplified round-robin schedule
    # Each team plays 17 games: division rivals twice, others once
    games = []
    all_teams = list(VEGAS_WIN_TOTALS.keys())

    for div, teams in DIVISIONS.items():
        # Division games (each pair plays twice)
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                games.append((teams[i], teams[j]))
                games.append((teams[j], teams[i]))

    # Inter-division games (simplified)
    divs = list(DIVISIONS.values())
    for i in range(len(divs)):
        for j in range(i + 1, len(divs)):
            for k in range(min(len(divs[i]), len(divs[j]))):
                games.append((divs[i][k], divs[j][k % len(divs[j])]))

    return games

def simulate_season(games):
    wins = {t: 0 for t in VEGAS_WIN_TOTALS}
    for home, away in games:
        if simulate_game(home, away):
            wins[home] += 1
        else:
            wins[away] += 1
    return wins

def get_playoff_teams(wins):
    afc_div_winners = []
    nfc_div_winners = []
    afc_wildcards = []
    nfc_wildcards = []

    for div, teams in DIVISIONS.items():
        conf = div.split()[0]
        div_teams = [(t, wins.get(t, 0)) for t in teams]
        winner = max(div_teams, key=lambda x: x[1])[0]
        non_winners = [t for t, _ in div_teams if t != winner]
        if conf == 'AFC':
            afc_div_winners.append((winner, wins[winner]))
            afc_wildcards.extend([(t, wins[t]) for t in non_winners])
        else:
            nfc_div_winners.append((winner, wins[winner]))
            nfc_wildcards.extend([(t, wins[t]) for t in non_winners])

    afc_wc = sorted(afc_wildcards, key=lambda x: x[1], reverse=True)[:3]
    nfc_wc = sorted(nfc_wildcards, key=lambda x: x[1], reverse=True)[:3]

    afc = [t for t, _ in sorted(afc_div_winners, key=lambda x: x[1], reverse=True)] + \
          [t for t, _ in afc_wc]
    nfc = [t for t, _ in sorted(nfc_div_winners, key=lambda x: x[1], reverse=True)] + \
          [t for t, _ in nfc_wc]

    return afc, nfc

def simulate_playoffs(afc, nfc):
    def play_round(teams):
        # Top seed gets bye if odd number
        if len(teams) <= 1:
            return teams
        winners = []
        seeds = teams.copy()
        # Top seed plays lowest seed
        while len(seeds) >= 2:
            home = seeds[0]
            away = seeds[-1]
            seeds = seeds[1:-1]
            if simulate_game(home, away):
                winners.append(home)
            else:
                winners.append(away)
        if seeds:
            winners = seeds + winners
        return winners

    for _ in range(3):
        afc = play_round(afc)
        nfc = play_round(nfc)

    afc_champ = afc[0] if afc else None
    nfc_champ = nfc[0] if nfc else None

    if afc_champ and nfc_champ:
        return afc_champ if simulate_game(afc_champ, nfc_champ) else nfc_champ
    return afc_champ or nfc_champ

# Run simulations
N_SIMS = 10000
print(f"\nRunning {N_SIMS:,} simulations...")

games = generate_schedule()
playoff_counts  = {t: 0 for t in VEGAS_WIN_TOTALS}
superbowl_counts = {t: 0 for t in VEGAS_WIN_TOTALS}
win_totals = {t: [] for t in VEGAS_WIN_TOTALS}

for i in range(N_SIMS):
    if i % 2000 == 0:
        print(f"  Simulation {i:,}/{N_SIMS:,}...")

    wins = simulate_season(games)
    for t in wins:
        win_totals[t].append(wins[t])

    afc_playoff, nfc_playoff = get_playoff_teams(wins)
    for t in afc_playoff + nfc_playoff:
        playoff_counts[t] += 1

    sb_winner = simulate_playoffs(afc_playoff, nfc_playoff)
    if sb_winner:
        superbowl_counts[sb_winner] += 1

# Build results
results = []
for team in VEGAS_WIN_TOTALS:
    results.append({
        'team':           team,
        'conference':     TEAM_TO_CONF.get(team, 'Unknown'),
        'division':       TEAM_TO_DIV.get(team, 'Unknown'),
        'vegas_wins':     VEGAS_WIN_TOTALS[team],
        'avg_wins':       round(np.mean(win_totals[team]), 1),
        'playoff_pct':    round(playoff_counts[team] / N_SIMS * 100, 1),
        'superbowl_pct':  round(superbowl_counts[team] / N_SIMS * 100, 1),
    })

results = sorted(results, key=lambda x: x['superbowl_pct'], reverse=True)

print("\n=== 2026 Season Projections (Vegas-Calibrated) ===")
print(f"{'Team':<6} {'Vegas W':<9} {'Avg W':<7} {'Playoff%':<10} {'SB%'}")
print("-" * 45)
for r in results:
    print(f"{r['team']:<6} {r['vegas_wins']:<9} {r['avg_wins']:<7} {r['playoff_pct']:<10} {r['superbowl_pct']}")

# Save to database
results_df = pd.DataFrame(results)
results_df['season'] = 2026
with engine.connect() as conn:
    results_df.to_sql('season_projections', conn, if_exists='replace', index=False)
    conn.commit()

with open('season_projections_2026.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\nSaved to database and season_projections_2026.json!")