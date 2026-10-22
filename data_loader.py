import streamlit as st
import pandas as pd
from euroleague_api.standings import Standings
from euroleague_api.player_stats import PlayerStats

#Loading data with caching
@st.cache_data
def load_data(season):
    """
    Downloading Team list and 3PM stats by all players for the selected season.
    """
    standings_api = Standings("E")
    player_api = PlayerStats("E")

    df_teams = standings_api.get_standings(season=season, round_number=1)
    df_player_all = player_api.get_player_stats_single_season(
        endpoint="traditional",
        season=season,
        statistic_mode="Accumulated"
    )

    return df_teams, df_player_all

@st.cache_data
def load_standings_trend(season, total_teams):
    """
    Downloading Standings trend for the selected season.
    """
    standings_api = Standings("E")
    rounds_list = []

    #number of round per season 
    max_rounds = (total_teams - 1) * 2  
    for r in range (1, max_rounds+1):
        try:
            df_round = standings_api.get_standings(season=season, round_number=r)
            if df_round.empty:
                break
            df_round['Round'] = r
            rounds_list.append(df_round)
        except Exception:
            break
    if len(rounds_list) > 0:
        return pd.concat(rounds_list, ignore_index=True)
    else:
        return pd.DataFrame() 