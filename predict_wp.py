import sys
import json
import pickle
import pandas as pd

# Load the saved model
with open('/Users/nikhilsankaran/PycharmProjects/nfl-analytics/win_probability_model.pkl', 'rb') as f:
    saved = pickle.load(f)
    model = saved['model']
    scaler = saved['scaler']

# Read input from command line arguments
score_diff = float(sys.argv[1])
seconds = float(sys.argv[2])
pos_to = float(sys.argv[3])
def_to = float(sys.argv[4])
yardline = float(sys.argv[5])
down = float(sys.argv[6])
ydstogo = float(sys.argv[7])

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
prob = model.predict_proba(scaled)[0][1]

# Output as JSON so Java can parse it
print(json.dumps({'win_probability': round(prob, 4)}))