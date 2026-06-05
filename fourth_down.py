import pandas as pd
from sqlalchemy import create_engine, text
import pickle
import numpy as np

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

# Load the win probability model we just trained
with open('win_probability_model.pkl', 'rb') as f:
    saved = pickle.load(f)
    model = saved['model']
    scaler = saved['scaler']

def get_win_prob(score_diff, seconds_remaining, posteam_to, defteam_to, yardline, down, ydstogo):
    features = pd.DataFrame([{
        'score_differential': score_diff,
        'game_seconds_remaining': seconds_remaining,
        'posteam_timeouts_remaining': posteam_to,
        'defteam_timeouts_remaining': defteam_to,
        'yardline_100': yardline,
        'down': down,
        'ydstogo': ydstogo
    }])
    scaled = scaler.transform(features)
    return model.predict_proba(scaled)[0][1]

print("Loading historical fourth down data...")
with engine.connect() as conn:
    # Get all actual fourth down plays to learn conversion rates
    fourth_downs = pd.read_sql(text("""
        SELECT 
            ydstogo,
            yardline_100,
            fourth_down_converted,
            fourth_down_failed,
            play_type,
            yards_gained,
            field_goal_result
        FROM plays
        WHERE down = 4
          AND play_type IN ('pass', 'run', 'field_goal', 'punt')
    """), conn)

print(f"Loaded {len(fourth_downs):,} fourth down plays")

# Calculate conversion rate by distance bucket
def get_conversion_rate(ydstogo):
    bucket = fourth_downs[
        (fourth_downs['play_type'].isin(['pass', 'run'])) &
        (fourth_downs['ydstogo'] >= max(1, ydstogo - 1)) &
        (fourth_downs['ydstogo'] <= ydstogo + 1)
    ]
    if len(bucket) == 0:
        return 0.3
    return bucket['fourth_down_converted'].mean()

# Calculate field goal make rate by distance
def get_fg_rate(yardline_100):
    # Rough historical NFL field goal percentages by distance
    kick_distance = yardline_100 + 17  # snap + endzone
    if kick_distance <= 30: return 0.95
    elif kick_distance <= 40: return 0.85
    elif kick_distance <= 50: return 0.72
    elif kick_distance <= 55: return 0.58
    else: return 0.40

def analyze_fourth_down(scenario):
    name = scenario['name']
    score_diff = scenario['score_differential']
    seconds = scenario['seconds_remaining']
    yardline = scenario['yardline_100']
    ydstogo = scenario['ydstogo']
    pos_to = scenario['posteam_timeouts']
    def_to = scenario['defteam_timeouts']

    conversion_rate = get_conversion_rate(ydstogo)
    fg_rate = get_fg_rate(yardline)
    kick_distance = yardline + 17

    # Win prob if you GO FOR IT
    wp_convert = get_win_prob(score_diff, seconds, pos_to, def_to, yardline, 1, 10)
    wp_fail = get_win_prob(-score_diff, seconds, def_to, pos_to, 100 - yardline, 1, 10)
    wp_go = (conversion_rate * wp_convert) + ((1 - conversion_rate) * (1 - wp_fail))

    # Win prob if you KICK FIELD GOAL
    wp_fg_make = get_win_prob(score_diff + 3, seconds, pos_to, def_to, 80, 1, 10)
    wp_fg_miss = get_win_prob(-score_diff, seconds, def_to, pos_to, 100 - yardline, 1, 10)
    wp_fg = (fg_rate * wp_fg_make) + ((1 - fg_rate) * (1 - wp_fg_miss))

    # Win prob if you PUNT (opponent gets ball at their ~15 yard line)
    wp_punt = get_win_prob(-score_diff, seconds, def_to, pos_to, 85, 1, 10)
    wp_punt = 1 - wp_punt  # flip since opponent now has ball

    options = {
        'Go for it': wp_go,
        'Field goal': wp_fg,
        'Punt': wp_punt
    }
    best = max(options, key=options.get)

    print(f"\n{'='*50}")
    print(f"{name}")
    if yardline <= 50:
        print(f"4th & {ydstogo} from opponent {yardline} yard line")
    else:
        print(f"4th & {ydstogo} from own {100 - yardline} yard line")
    print(f"Score: {'Tied' if score_diff == 0 else ('+' + str(score_diff) if score_diff > 0 else str(score_diff))}, {seconds//60}:{seconds%60:02d} remaining")
    print(f"Conversion rate historically: {conversion_rate:.1%}")
    if yardline <= 55:
        print(f"FG attempt ({kick_distance} yards): {fg_rate:.1%} make rate")
    print(f"\n  Go for it:  {wp_go:.1%} win probability")
    if yardline <= 55:
        print(f"  Field goal: {wp_fg:.1%} win probability")
    print(f"  Punt:       {wp_punt:.1%} win probability")
    print(f"\n  ✓ RECOMMENDATION: {best}")

# Test scenarios
scenarios = [
    {
        'name': 'Classic 4th and short, mid-field',
        'score_differential': 0,
        'seconds_remaining': 480,
        'yardline_100': 45,
        'ydstogo': 2,
        'posteam_timeouts': 2,
        'defteam_timeouts': 2
    },
    {
        'name': 'Late game desperation',
        'score_differential': -7,
        'seconds_remaining': 180,
        'yardline_100': 30,
        'ydstogo': 5,
        'posteam_timeouts': 1,
        'defteam_timeouts': 2
    },
    {
        'name': 'Conservative coach territory',
        'score_differential': 3,
        'seconds_remaining': 900,
        'yardline_100': 35,
        'ydstogo': 1,
        'posteam_timeouts': 2,
        'defteam_timeouts': 2
    },
]

for scenario in scenarios:
    analyze_fourth_down(scenario)