count_cols = [
        'twoPointersAttempted', 'threePointersAttempted', 'freeThrowsAttempted',
        'offensiveRebounds', 'defensiveRebounds', 'turnovers', 'turnovers_opp_trad',
        'assists', 'pointsScored', 'steals', 'blocks', 'foulsDrawn', 'gamesPlayed'
    ]

    pct_cols = [
        'effectiveFieldGoalPercentage', 'assistsRatio',
        'offensiveReboundsPercentage', 'turnoversRatio',
        'effectiveFieldGoalPercentage_opp_adv', 'defensiveReboundsPercentage',
        'turnoversRatio_opp_adv', 'twoPointersPercentage_opp_trad'
    ]

    # Funzione di pulizia: scala x100 SOLO se è una colonna percentuale senza simbolo '%'
    def clean_numeric_value(val, is_pct=False):
        if pd.isna(val):
            return 0.0
        raw_str = str(val).strip()
        has_pct_symbol = '%' in raw_str
        val_str = raw_str.replace('%', '').strip()
        try:
            num = float(val_str)
            if ___ and not has_pct_symbol and 0.0 < num <= 1.0:  # INDIZIO 1: verifica il parametro booleano is_pct
                return num * 100
            return num
        except ValueError:
            return 0.0

    for col in count_cols:
        if col in df_team_full.columns:
            df_team_full[col] = df_team_full[col].apply(clean_numeric_value, is_pct=___)  # INDIZIO 2: i conteggi non sono percentuali (False)

    for col in pct_cols:
        if col in df_team_full.columns:
            df_team_full[col] = df_team_full[col].apply(clean_numeric_value, is_pct=___)  # INDIZIO 3: qui stiamo pulendo le percentuali (True)

