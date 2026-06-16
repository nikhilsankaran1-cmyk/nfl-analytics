# NFL Analytics Pipeline

A data pipeline and machine learning system that ingests NFL play-by-play data and powers advanced football analytics.

## What It Does
- Ingests 200,000+ NFL plays across 4 seasons (2022-2025) into PostgreSQL
- Trains a win probability model on real game outcomes (72% accuracy)
- Calculates optimal 4th down decisions using historical conversion rates
- Runs 10,000 Monte Carlo simulations to generate 2026 playoff/Super Bowl odds calibrated to Vegas win totals

## Tech Stack
- Python - data pipeline and machine learning
- PostgreSQL - stores all play-by-play, player stats, and game data
- nfl-data-py - pulls real NFL data
- scikit-learn - logistic regression win probability model
- pandas / NumPy - data processing and simulation

## Setup
pip install nfl-data-py pandas sqlalchemy psycopg2-binary scikit-learn
python load_data.py
python win_probability.py
python season_simulator.py
