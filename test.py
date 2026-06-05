import nfl_data_py as nfl

print("Loading NFL data...")
plays = nfl.import_pbp_data([2023])
print(f"Loaded {len(plays)} plays")
print(plays.columns.tolist())