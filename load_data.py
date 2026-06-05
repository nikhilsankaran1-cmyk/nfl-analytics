import nfl_data_py as nfl
import pandas as pd
from sqlalchemy import create_engine

# Connect to PostgreSQL
engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

print("Loading play-by-play data...")
plays = nfl.import_pbp_data([2022, 2023, 2024, 2025])

# Keep only the columns we actually need
columns = [
    'play_id', 'game_id', 'home_team', 'away_team', 'week', 'season',
    'posteam', 'defteam', 'qtr', 'down', 'ydstogo', 'yardline_100',
    'game_seconds_remaining', 'score_differential', 'posteam_score',
    'defteam_score', 'posteam_timeouts_remaining', 'defteam_timeouts_remaining',
    'play_type', 'yards_gained', 'epa', 'wp', 'wpa',
    'pass_attempt', 'rush_attempt', 'touchdown', 'interception',
    'fumble_lost', 'field_goal_attempt', 'field_goal_result',
    'punt_attempt', 'fourth_down_converted', 'fourth_down_failed',
    'passer_player_name', 'receiver_player_name', 'rusher_player_name',
    'spread_line', 'temp', 'wind', 'roof', 'surface',
    'result', 'home_score', 'away_score'
]

plays = plays[columns]

print(f"Saving {len(plays)} plays to database...")
plays.to_sql('plays', engine, if_exists='replace', index=False)
print("Done! Plays table created.")

print("Loading player stats...")
stats = nfl.import_weekly_data([2022, 2023, 2024])
stats.to_sql('player_stats', engine, if_exists='replace', index=False)
print("Done! Player stats table created.")

print("Loading game schedules...")
schedule = nfl.import_schedules([2022, 2023, 2024, 2025])
schedule.to_sql('games', engine, if_exists='replace', index=False)
print("Done! Games table created.")

print("\nAll data loaded successfully!")