import sys
import json
import pickle
import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

with open('/Users/nikhilsankaran/PycharmProjects/nfl-analytics/win_probability_model.pkl', 'rb') as f:
    saved = pickle.load(f)
    model = saved['model']
    scaler = saved['scaler']

def get_win_prob(score_diff, seconds, pos_to, def_to, yardline, down, ydstogo):
    features = pd.DataFrame([{
        'score_differential': score_diff,
        'game_seconds_remaining': seconds,
        'posteam_timeouts_remaining': pos_to,
        'defteam_timeouts_remaining': def_to,
        'yardline_100': yardline,
        'down': down,
        'ydstogo': ydstogo
    }])
    scaled = scaler.transform(features)
    return model.predict_proba(scaled)[0][1]

def get_conversion_rate(ydstogo):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT AVG(fourth_down_converted) as rate
            FROM plays
            WHERE down = 4
              AND play_type IN ('pass', 'run')
              AND ydstogo >= :low
              AND ydstogo <= :high
        """), {'low': max(1, ydstogo - 1), 'high': ydstogo + 1})
        row = result.fetchone()
        return float(row[0]) if row and row[0] else 0.35

def get_fg_rate(yardline_100):
    kick_distance = yardline_100 + 17
    if kick_distance <= 30: return 0.95
    elif kick_distance <= 40: return 0.85
    elif kick_distance <= 50: return 0.72
    elif kick_distance <= 55: return 0.58
    else: return 0.40

# Read inputs
score_diff   = float(sys.argv[1])
seconds      = float(sys.argv[2])
yardline     = float(sys.argv[3])
ydstogo      = float(sys.argv[4])
pos_to       = float(sys.argv[5])
def_to       = float(sys.argv[6])

conversion_rate = get_conversion_rate(ydstogo)
fg_rate = get_fg_rate(yardline)
kick_distance = int(yardline + 17)

# Go for it
wp_convert = get_win_prob(score_diff, seconds, pos_to, def_to, yardline, 1, 10)
wp_fail    = get_win_prob(-score_diff, seconds, def_to, pos_to, 100 - yardline, 1, 10)
wp_go      = (conversion_rate * wp_convert) + ((1 - conversion_rate) * (1 - wp_fail))

# Field goal
wp_fg_make = get_win_prob(score_diff + 3, seconds, pos_to, def_to, 80, 1, 10)
wp_fg_miss = get_win_prob(-score_diff, seconds, def_to, pos_to, 100 - yardline, 1, 10)
wp_fg      = (fg_rate * wp_fg_make) + ((1 - fg_rate) * (1 - wp_fg_miss))

# Punt
wp_punt = 1 - get_win_prob(-score_diff, seconds, def_to, pos_to, 85, 1, 10)

fg_applicable = yardline <= 55

options = {'go_for_it': wp_go, 'punt': wp_punt}
if fg_applicable:
    options['field_goal'] = wp_fg
recommendation = max(options, key=options.get)

print(json.dumps({
    'go_for_it':        round(wp_go, 4),
    'field_goal':       round(wp_fg, 4) if fg_applicable else None,
    'punt':             round(wp_punt, 4),
    'recommendation':   recommendation,
    'conversion_rate':  round(conversion_rate, 4),
    'fg_rate':          round(fg_rate, 4) if fg_applicable else None,
    'kick_distance':    kick_distance if fg_applicable else None,
    'fg_applicable':    fg_applicable
}))