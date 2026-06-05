from sqlalchemy import create_engine, text

engine = create_engine('postgresql://nfl_user:password123@localhost:5432/nfl_analytics')

with engine.connect() as conn:
    # Count rows in each table
    plays_count = conn.execute(text("SELECT COUNT(*) FROM plays")).scalar()
    stats_count = conn.execute(text("SELECT COUNT(*) FROM player_stats")).scalar()
    games_count = conn.execute(text("SELECT COUNT(*) FROM games")).scalar()

    print(f"Plays table:        {plays_count:,} rows")
    print(f"Player stats table: {stats_count:,} rows")
    print(f"Games table:        {games_count:,} rows")

    # Check seasons loaded
    seasons = conn.execute(text("SELECT DISTINCT season FROM plays ORDER BY season")).fetchall()
    print(f"\nSeasons loaded: {[row[0] for row in seasons]}")

    # Sample play to make sure data looks right
    print("\nSample play:")
    sample = conn.execute(text("""
        SELECT game_id, home_team, away_team, qtr, down, 
               ydstogo, play_type, yards_gained, epa
        FROM plays 
        WHERE play_type IN ('pass', 'run') 
        LIMIT 1
    """)).fetchone()
    print(sample)

    # Top 5 passers by total EPA in 2024
    print("\nTop 5 QBs by EPA in 2024:")
    top_qbs = conn.execute(text("""
        SELECT passer_player_name, 
               ROUND(SUM(epa)::numeric, 2) as total_epa,
               COUNT(*) as attempts
        FROM plays
        WHERE season = 2024 
          AND play_type = 'pass'
          AND passer_player_name IS NOT NULL
        GROUP BY passer_player_name
        ORDER BY total_epa DESC
        LIMIT 5
    """)).fetchall()
    for row in top_qbs:
        print(f"  {row[0]}: EPA={row[1]}, Attempts={row[2]}")