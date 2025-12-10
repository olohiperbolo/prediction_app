import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime
import glob
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sports.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # żeby móc odczytywać po nazwach kolumn
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # prosta tabela dla meczów piłkarskich (na początek)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS football_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            league TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            match_date TEXT NOT NULL,
            home_goals INTEGER,
            away_goals INTEGER
        );
    """)

    conn.commit()
    conn.close()


def clear_football_matches():
    """Opcjonalnie czyści tabelę przed ponownym importem."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM football_matches")
    conn.commit()
    conn.close()


def import_football_csv(csv_path, league_name):
    df = pd.read_csv(csv_path)

    # Normalizacja nazw kolumn, bo Football-Data zmienia je między sezonami
    rename_map = {
        "HomeTeam": "home_team",
        "AwayTeam": "away_team",
        "Home": "home_team",
        "Away": "away_team",
        "FTHG": "home_goals",
        "FTAG": "away_goals",
        "HG": "home_goals",
        "AG": "away_goals",
        "Date": "match_date"
    }

    df = df.rename(columns=rename_map)

    df = df.dropna(subset=["home_team", "away_team"])

    df["league"] = league_name

    # Konwersja daty
    def parse_date(x):
        try:
            return datetime.strptime(x, "%d/%m/%Y").date().isoformat()
        except Exception:
            try:
                return datetime.strptime(x, "%Y-%m-%d").date().isoformat()
            except Exception:
                return None

    df["match_date"] = df["match_date"].astype(str).apply(parse_date)

    # Wywalamy mecze bez daty
    df = df.dropna(subset=["match_date"])

    # Wybieramy tylko potrzebne kolumny
    df_final = df[["league", "home_team", "away_team", "match_date", "home_goals", "away_goals"]]

    # Zapis do bazy
    conn = get_connection()
    df_final.to_sql("football_matches", conn, if_exists="append", index=False)
    conn.close()

    print(f"Imported {len(df_final)} rows from {csv_path}")


def import_all_csv():
    folder_path = BASE_DIR / "data" / "football_csv"
    csv_files = folder_path.glob("*.csv")

    league_map = {
        "PL": "Premier League",
        "LALIGA": "La Liga",
        "SERIEA": "Serie A",
        "BUNDES": "Bundesliga",
        "LIGUE1": "Ligue 1"
    }

    for file_path in csv_files:
        filename = os.path.basename(str(file_path)).upper()

        league = None
        for key, full_name in league_map.items():
            if key in filename:
                league = full_name
                break

        if league is None:
            print("Skipping file (unknown league):", file_path)
            continue

        import_football_csv(file_path, league)


def insert_dummy_data():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO football_matches (league, home_team, away_team, match_date, home_goals, away_goals)
        VALUES
        ('Premier League', 'Liverpool', 'Arsenal', '2025-12-20', NULL, NULL),
        ('La Liga', 'Real Madrid', 'Barcelona', '2025-12-21', NULL, NULL);
    """)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    clear_football_matches()

    # insert_dummy_data()

    import_all_csv()
    print("Database initialized and CSV data imported at:", DB_PATH)
