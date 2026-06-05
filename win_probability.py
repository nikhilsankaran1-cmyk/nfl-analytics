import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import pickle

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

print("Loading data...")
with engine.connect() as conn:
    df = pd.read_sql(text("""
        SELECT 
            score_differential,
            game_seconds_remaining,
            posteam_timeouts_remaining,
            defteam_timeouts_remaining,
            yardline_100,
            down,
            ydstogo,
            posteam_score,
            defteam_score,
            result,
            posteam,
            home_team
        FROM plays
        WHERE play_type IN ('pass', 'run')
          AND down IS NOT NULL
          AND game_seconds_remaining > 0
          AND result IS NOT NULL
    """), conn)

print(f"Loaded {len(df):,} plays for training")

# result is the final score margin from home team's perspective
# posteam_won = 1 if possession team actually won the game
df['posteam_won'] = (
    ((df['posteam'] == df['home_team']) & (df['result'] > 0)) |
    ((df['posteam'] != df['home_team']) & (df['result'] < 0))
).astype(int)

features = [
    'score_differential',
    'game_seconds_remaining',
    'posteam_timeouts_remaining',
    'defteam_timeouts_remaining',
    'yardline_100',
    'down',
    'ydstogo'
]

df = df.dropna(subset=features + ['posteam_won'])

X = df[features]
y = df['posteam_won']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Scale features so the model treats them more equally
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Training win probability model...")
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

predictions = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, predictions)
print(f"Model accuracy: {accuracy:.1%}")

# Save both model and scaler
with open('win_probability_model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'scaler': scaler}, f)
print("Model saved to win_probability_model.pkl")

# Test scenarios
print("\n--- Win Probability Examples ---")

scenarios = [
    {
        'name': 'Tied game, ball at midfield, 2 min left',
        'score_differential': 0,
        'game_seconds_remaining': 120,
        'posteam_timeouts_remaining': 2,
        'defteam_timeouts_remaining': 1,
        'yardline_100': 50,
        'down': 1,
        'ydstogo': 10
    },
    {
        'name': 'Down 7, own 20 yard line, 5 min left',
        'score_differential': -7,
        'game_seconds_remaining': 300,
        'posteam_timeouts_remaining': 1,
        'defteam_timeouts_remaining': 3,
        'yardline_100': 80,
        'down': 1,
        'ydstogo': 10
    },
    {
        'name': 'Up 10, opponent 30, 10 min left',
        'score_differential': 10,
        'game_seconds_remaining': 600,
        'posteam_timeouts_remaining': 2,
        'defteam_timeouts_remaining': 2,
        'yardline_100': 30,
        'down': 1,
        'ydstogo': 10
    },
    {
        'name': 'Down 3, 4th and 1 at opponent 35, 2 min left',
        'score_differential': -3,
        'game_seconds_remaining': 120,
        'posteam_timeouts_remaining': 1,
        'defteam_timeouts_remaining': 0,
        'yardline_100': 35,
        'down': 4,
        'ydstogo': 1
    }
]

for scenario in scenarios:
    name = scenario.pop('name')
    features_df = pd.DataFrame([scenario])
    features_scaled = scaler.transform(features_df)
    prob = model.predict_proba(features_scaled)[0][1]
    print(f"\n{name}")
    print(f"  Win probability: {prob:.1%}")