def _load_single_mode_team_stats(team_api, season, mode):
    """
    Scarica e unisce i 4 endpoint (traditional, advanced, opponentsTraditional, opponentsAdvanced)
    per una singola statistic_mode ('Accumulated' o 'PerGame').
    """
    df_trad = team_api.get_team_stats_single_season(
        endpoint='traditional', season=season, statistic_mode=mode
    )
    df_adv = team_api.get_team_stats_single_season(
        endpoint='advanced', season=season, statistic_mode=mode
    )
    df_opp_trad = team_api.get_team_stats_single_season(
        endpoint='opponentsTraditional', season=season, statistic_mode=mode
    )
    df_opp_adv = team_api.get_team_stats_single_season(
        endpoint='opponentsAdvanced', season=season, statistic_mode=mode
    )

    cols_to_drop = ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']

    df_adv_clean = df_adv.drop(columns=[c for c in cols_to_drop if c in df_adv.columns])
    df_opp_trad_clean = df_opp_trad.drop(columns=[c for c in cols_to_drop if c in df_opp_trad.columns])
    df_opp_adv_clean = df_opp_adv.drop(columns=[c for c in cols_to_drop if c in df_opp_adv.columns])

    df_merged = pd.merge(df_trad, df_adv_clean, on='team.code')
    df_merged = pd.merge(df_merged, df_opp_trad_clean, on='team.code', suffixes=('', '_opp_trad'))
    df_merged = pd.merge(df_merged, df_opp_adv_clean, on='team.code', suffixes=('', '_opp_adv'))

    return df_merged


@st.cache_data
def load_team_stats(season):
    """
    Restituisce un unico DataFrame con tutte le metriche Accumulated e PerGame (_pg)
    per traditional, advanced, opponentsTraditional e opponentsAdvanced.
    """
    team_api = TeamStats('E')

    # 1. Scarichiamo e uniamo i 4 endpoint per entrambe le modalità
    df_acc = _load_single_mode_team_stats(team_api, season, ___)  # INDIZIO 1: modalità 'Accumulated'
    df_pg = _load_single_mode_team_stats(team_api, season, ___)   # INDIZIO 2: modalità 'PerGame'

    # 2. Rimuoviamo i metadati duplicati da df_pg prima del merge finale
    meta_cols = ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']
    df_pg_clean = df_pg.drop(columns=[c for c in meta_cols if c in df_pg.columns])

    # 3. Uniamo Accumulated e PerGame su 'team.code' aggiungendo il suffisso '_pg'
    df_team_full = pd.merge(
        df_acc,
        df_pg_clean,
        on='team.code',
        suffixes=('', ___)  # INDIZIO 3: usa '_pg' per distinguere le colonne PerGame
    )

    return df_team_full