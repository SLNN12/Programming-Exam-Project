import pandas as pd
from data_loader import load_player_stats
from player_type_ml import get_player_arctype

def run_clustering_test():
    print("⏳ Scaricamento dei dati Euroleague...")
    
    df_players_raw = load_player_stats(season=2026, statistic_mode='PerGame')
    print(f"📊 Dati scaricati con successo! Righe: {len(df_players_raw)}")
    
    # 2. Chiamiamo la nostra magica Funzione Master dal file separato
    print("\n⚙️ Avvio pipeline di Machine Learning (Scaling -> PCA -> K-Means)...")
    df_final = get_player_arctype(df_players_raw)
    
    # 3. Mostriamo il risultato finale (Nome del giocatore e il suo Archetipo)
    print("\n✅ CLUSTERING COMPLETATO! Ecco un'anteprima dei giocatori:\n")
    
    # Selezioniamo solo il nome del giocatore (es. colonna 'player.name') e l'Archetipo
    # Assicurati che 'player.name' esista nel tuo dataframe grezzo
    columns_to_show = ['player.name', 'pointsScored', 'assists', 'totalRebounds', 'twoPointersAttempted', 'threePointersAttempted','archetype']
    
    # Stampiamo i primi 15 giocatori per vedere come li ha categorizzati
    print(df_final[columns_to_show].tail(10).to_string())


if __name__ == "__main__":
    run_clustering_test()