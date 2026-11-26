import streamlit as st
import pandas as pd
from euroleague_api.standings import Standings
from euroleague_api.player_stats import PlayerStats
import concurrent.futures 
from euroleague_api.team_stats import TeamStats


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


#Loading team data
def load_single_mode_team_stats(team_api, season, mode): #download and merge the 4 endpoint per statistic mode
    df_trad = team_api.get_team_stats_single_season(
        endpoint='traditional', season=season, statistic_mode=mode)

    df_adv = team_api.get_team_stats_single_season(
            endpoint='advanced', season=season, statistic_mode=mode)

    df_opp_adv = team_api.get_team_stats_single_season(
            endpoint='opponentsAdvanced', season=season, statistic_mode=mode)

    df_opp_trad = team_api.get_team_stats_single_season(
            endpoint='opponentsTraditional', season=season, statistic_mode=mode)

    #CLANING FROM REDUNDANT COLUMSN
    cols_to_drop = ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']

    df_adv_clean = df_adv.drop(columns=[c for c in cols_to_drop if c in df_adv.columns])
    df_opp_adv_clean = df_opp_adv.drop(columns=[c for c in cols_to_drop if c in df_opp_adv.columns])
    df_opp_trad_clean = df_opp_trad.drop(columns=[c for c in cols_to_drop if c in df_opp_trad.columns])

    df_merged = pd.merge(df_trad, df_adv_clean, on='team.code')
    df_merged = pd.merge(df_merged, df_opp_adv_clean, on='team.code', suffixes=('','_opp_adv'))
    df_merged = pd.merge(df_merged, df_opp_trad_clean, on='team.code', suffixes=('','_opp_trad'))

    return df_merged

@st.cache_data
def load_team_stats(season):
    #RETURN A UNIFIED DF WITH BOTH PERGAME AND ACCUMULATED STATS OF THE EUROLEAGUE TEAMS
    team_api = TeamStats('E')

    #download and merge the 4 endpoint for both the modalities
    df_acc = load_single_mode_team_stats(team_api, season, mode='Accumulated')
    df_pg = load_single_mode_team_stats(team_api, season, mode='PerGame')

    #remove duplicate metadata from the pg dataframe before the final merge
    meta_cols = ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']
    df_pg_clean = df_pg.drop(columns=[c for c in meta_cols if c in df_pg.columns])

    #merging accumulated and per game with suffixes for the per game stats
    df_team_full = pd.merge(
        df_acc,
        df_pg_clean,
        on='team.code',
        suffixes=('', '_pg')
    )

    return df_team_full


@st.cache_data
def load_round_standings(season, round_num):
    """
    Downloading Standings for the selected season and round.
    """
    standings_api = Standings("E")
    df_round = standings_api.get_standings(season=season, round_number=round_num)
    return df_round


@st.cache_data
def load_player_stats(season, statistic_mode):
    """
    Downloading Player stats for the selected season.
    """
    player_api = PlayerStats("E")
    df_trad = player_api.get_player_stats_single_season('traditional', season=season, statistic_mode=statistic_mode)
    df_adv = player_api.get_player_stats_single_season('advanced', season=season, statistic_mode=statistic_mode)
    df_scoring = player_api.get_player_stats_single_season('scoring', season=season, statistic_mode='Accumulated')

    #variable with the duplicated columns to drop from the advanced and scoring dataframes
    cols_to_drop = ['playerRanking', 'gamesPlayed', 'gamesStarted', 'minutesPlayed', 
                    'player.name', 'player.age', 'player.imageUrl', 
                    'player.team.code', 'player.team.tvCodes', 'player.team.name', 'player.team.imageUrl']

    #cleaning the dataframes
    df_adv_cleaned = df_adv.drop(columns=[c for c in cols_to_drop if c in df_adv.columns])
    df_scoring_cleaned = df_scoring.drop(columns=[c for c in cols_to_drop if c in df_scoring.columns])

    #merging the dataframes
    df_full = pd.merge(df_trad, df_adv_cleaned, on='player.code')
    df_full = pd.merge(df_full, df_scoring_cleaned, on='player.code')

    return df_full

@st.cache_data
#creating a more precise df for the player type ML model
def load_all_season_player_stats(season=(2022,2023,2024,2025,2026)):

    dfs = []
    for s in season:
        df_s = load_player_stats(s, 'PerGame')
        df_s['season'] = s
        dfs.append(df_s)
    return pd.concat(dfs, ignore_index=True)

