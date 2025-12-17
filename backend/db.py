import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "sports.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM football_matches;")
    conn.commit()
    conn.close()


def parse_date_safe(x: str):
    x = str(x).strip()

    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(x, fmt).date().isoformat()
        except Exception:
            pass

    return None


def import_football_csv(csv_path: Path, league_name: str):
    df = pd.read_csv(csv_path)

    # Mapowanie nazw kolumn z różnych wersji plików
    rename_map = {
        "HomeTeam": "home_team",
        "AwayTeam": "away_team",
        "Home": "home_team",
        "Away": "away_team",
        "FTHG": "home_goals",
        "FTAG": "away_goals",
        "HG": "home_goals",
        "AG": "away_goals",
        "Date": "match_date",
    }

    df = df.rename(columns=rename_map)

    required_cols = ["home_team", "away_team", "match_date"]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Brakuje kolumny '{col}' w pliku: {csv_path.name}")

    # Jeśli nie ma goli, dodaj puste
    if "home_goals" not in df.columns:
        df["home_goals"] = None
    if "away_goals" not in df.columns:
        df["away_goals"] = None

    # Usuń wiersze bez drużyn
    df = df.dropna(subset=["home_team", "away_team"])

    # Liga
    df["league"] = league_name

    # Data
    df["match_date"] = df["match_date"].apply(parse_date_safe)
    df = df.dropna(subset=["match_date"])

    # Docelowe kolumny
    df_final = df[["league", "home_team", "away_team", "match_date", "home_goals", "away_goals"]]

    # Zapis do bazy
    conn = get_connection()
    df_final.to_sql("football_matches", conn, if_exists="append", index=False)
    conn.close()

    print(f"Imported {len(df_final)} rows from {csv_path.name} ({league_name})")


def detect_league_from_filename(filename_upper: str):
    """
    Wykrywanie ligi po nazwie pliku.
    Obsługuje zarówno Twoje nazwy (PL/LALIGA/...) jak i kody Football-Data (E0/SP1/...).
    """
    league_map = {
        #tagi
        "PL": "Premier League",
        "LALIGA": "La Liga",
        "SA": "Serie A",
        "BUNDES": "Bundesliga",
        "LEAGUE": "Ligue 1",

        # Kody z csv
        "E0": "Premier League",
        "SP1": "La Liga",
        "I1": "Serie A",
        "D1": "Bundesliga",
        "F1": "Ligue 1",
    }

    for key, full_name in league_map.items():
        if key in filename_upper:
            return full_name

    return None


def import_all_csv():
    folder_path = BASE_DIR / "data" / "football_csv"
    csv_files = sorted(folder_path.glob("*.csv"))

    print("Szukam CSV w folderze:", folder_path)
    print("Znalezione pliki:", [p.name for p in csv_files])

    if not csv_files:
        print("XXX Nie znaleziono żadnych plików .csv w data/football_csv/")
        return

    for file_path in csv_files:
        filename_upper = file_path.name.upper()
        league = detect_league_from_filename(filename_upper)

        print("➡️  Plik:", file_path.name, "| wykryta liga:", league)

        if league is None:
            print("!Pomijam plik (nieznana liga):", file_path.name)
            continue

        import_football_csv(file_path, league)


if __name__ == "__main__":
    init_db()
    clear_football_matches()

    import_all_csv()

    # test ile weszło
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM football_matches;")
    total = cur.fetchone()[0]
    conn.close()

    print("Done. Rows in football_matches:", total)
    print("DB_PATH:", DB_PATH)
