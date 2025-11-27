import pandas as pd
import numpy as np

def process_football_data(file_path):
    # 1. Wczytanie danych
    df = pd.read_csv(file_path)
    
    # 2. Formatowanie daty i czasu
    # Łączymy Datę i Czas, żeby mieć dokładny moment rozpoczęcia
    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True)
    
    # 3. Wybór tylko potrzebnych kolumn na start
    cols_to_keep = [
        'DateTime', 'HomeTeam', 'AwayTeam', 
        'FTHG', 'FTAG', 'FTR',
        'HS', 'AS', 'HST', 'AST',
        'B365H', 'B365D', 'B365A'
    ]
    
    # Zabezpieczenie: wybieramy tylko te kolumny, które faktycznie są w pliku
    existing_cols = [c for c in cols_to_keep if c in df.columns]
    df = df[existing_cols]

    # 4. ENCODING WYNIKU (Target)
    # Model musi przewidywać liczbę.
    # Konwencja: 0 = Goście (Away), 1 = Remis (Draw), 2 = Gospodarze (Home)
    target_mapping = {'A': 0, 'D': 1, 'H': 2}
    df['Target'] = df['FTR'].map(target_mapping)
    
    # 5. czyszczenie
    df.dropna(inplace=True)
    df = df.sort_values('DateTime')
    
    return df

file_path = 'C:\studia\prediction_app\data\PL2025.csv' # Upewnij się, że masz ten plik
data = process_football_data(file_path)

print("Podgląd danych gotowych do analizy:")
print(data[['DateTime', 'HomeTeam', 'AwayTeam', 'FTR', 'Target', 'B365H']].head())

print("\nRozkład wyników (ile było wygranych gospodarzy - 2, remisów - 1, gości - 0):")
print(data['Target'].value_counts())