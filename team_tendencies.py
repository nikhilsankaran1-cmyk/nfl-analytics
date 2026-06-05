import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

def get_team_tendencies(team, season=2024):
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                down, ydstogo, yardline_100,
                play_type, pass_attempt, rush_attempt,
                score_differential, qtr, epa
            FROM plays
            WHERE (posteam = :team)
              AND season = :season
              AND play_type IN ('pass', 'run')
              AND down IS NOT NULL
        """), conn, params={'team': team, 'season': season})

    if len(df) == 0:
        print(f"No data found for {team} in {season}")
        return

    total_plays = len(df)

    # Overall pass/run split
    pass_rate = df['pass_attempt'].mean()
    run_rate = df['rush_attempt'].mean()

    # By down
    by_down = df.groupby('down').agg(
        pass_rate=('pass_attempt', 'mean'),
        plays=('play_type', 'count'),
        avg_epa=('epa', 'mean')
    ).round(3)

    # Early downs (1st and 2nd)
    early = df[df['down'].isin([1, 2])]
    early_pass = early['pass_attempt'].mean()

    # Third down
    third = df[df['down'] == 3]
    third_pass = third['pass_attempt'].mean() if len(third) > 0 else 0

    # Red zone (inside opponent 20)
    redzone = df[df['yardline_100'] <= 20]
    rz_pass = redzone['pass_attempt'].mean() if len(redzone) > 0 else 0

    # Two minute drill (under 2 min, either half)
    two_min = df[df['ydstogo'] <= 120]
    two_min_pass = two_min['pass_attempt'].mean() if len(two_min) > 0 else 0

    # Average EPA per play
    avg_epa = df['epa'].mean()
    pass_epa = df[df['pass_attempt'] == 1]['epa'].mean()
    run_epa = df[df['rush_attempt'] == 1]['epa'].mean()

    # 3rd and short vs long
    third_short = df[(df['down'] == 3) & (df['ydstogo'] <= 3)]
    third_long = df[(df['down'] == 3) & (df['ydstogo'] >= 7)]
    third_short_pass = third_short['pass_attempt'].mean() if len(third_short) > 0 else 0
    third_long_pass = third_long['pass_attempt'].mean() if len(third_long) > 0 else 0

    print(f"\n{'='*45}")
    print(f"  {team} Offensive Tendencies — {season}")
    print(f"{'='*45}")
    print(f"  Total plays analyzed: {total_plays:,}")
    print(f"\n  OVERALL")
    print(f"    Pass rate:     {pass_rate:.1%}")
    print(f"    Run rate:      {run_rate:.1%}")
    print(f"    Avg EPA/play:  {avg_epa:+.3f}")
    print(f"\n  BY SITUATION")
    print(f"    1st & 2nd down pass rate:  {early_pass:.1%}")
    print(f"    3rd down pass rate:        {third_pass:.1%}")
    print(f"    Red zone pass rate:        {rz_pass:.1%}")
    print(f"\n  3RD DOWN TENDENCIES")
    print(f"    3rd & short (1-3): {third_short_pass:.1%} pass")
    print(f"    3rd & long  (7+):  {third_long_pass:.1%} pass")
    print(f"\n  EPA EFFICIENCY")
    print(f"    Pass EPA/play:  {pass_epa:+.3f}")
    print(f"    Run EPA/play:   {run_epa:+.3f}")
    print(f"\n  BY DOWN BREAKDOWN")
    for down, row in by_down.iterrows():
        print(f"    Down {int(down)}: {row['pass_rate']:.1%} pass, "
              f"{row['plays']} plays, {row['avg_epa']:+.3f} EPA")

# Analyze a few teams
for team in ['KC', 'SF', 'BAL', 'BUF']:
    get_team_tendencies(team, 2024)