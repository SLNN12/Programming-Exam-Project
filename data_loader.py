import streamlit as st
import pandas as pd
from euroleague_api.standings import Standings
from euroleague_api.player_stats import PlayerStats
import concurrent.futures 

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

#Support func to download 1 round each (for multithreading)
def fetch_single_round(season, r):
    try:
        standings_api = Standings('E')
        df_round = standings_api.get_standings(season=season, round_number=r)

        #if the round exist, add the round column
        if not df_round.empty:
            df_round['Round'] = r
            return df_round
    except Exception:
        pass #if there is an error, ignore

    return pd.DataFrame() #in case of problem return a dataframe

@st.cache_data
def load_standings_trend(season, total_teams):
    """
    Downloading Standings trend for the selected season.
    """

    #number of round per season 
    max_rounds = (total_teams - 1) * 2  
    rounds_list = []

    #create the func to do the api request all in once
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:

        #1. assign the work
        futures = []
        for r in range(1, max_rounds + 1):
            task = executor.submit(fetch_single_round, season, r)
            futures.append(task)

        #2. collect the results when the workers end their work
        for future in concurrent.futures.as_completed(futures):
            df_round = future.result()

            if not df_round.empty:
                rounds_list.append(df_round)

    # put it all together
    if len(rounds_list)>0:
        final_df = pd.concat(rounds_list, ignore_index=True)

        #sort by round and for standing position
        final_df = final_df.sort_values(by=['Round', 'position']).reset_index(drop=True)
        return final_df
    else: return pd.DataFrame()
