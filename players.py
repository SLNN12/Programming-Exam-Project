import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_player_stats 

def display_players():
    st.write('---')
    header_col1, header_col2, header_col3 = st.columns([2, 1.5, 1.5])

    with header_col1:
        st.subheader(':orange[Selected player]')

        #select season
        season = st.selectbox(
            'Select Season',
            options=[2026, 2025, 2024, 2023,2022],
            key='player_season_select'
        )

        #Select statistic mode
        mode_options = ['PerGame', 'Accumulated', 'PerMinute', 'Per100Possesions']
        select_mode = st.selectbox(
            'Select Statistic Mode',
            options=mode_options,
            key='player_stat_mode_select'
        )

        with st.spinner('Loading Player Stats...'):
            df_players = load_player_stats(season, select_mode)

        team_list = ['All Teams'] + sorted(df_players['player.team.name'].dropna().unique().tolist())

        #create a selectbox for team selection
        select_team = st.selectbox(
            'Select Team',
            options=team_list,
            key='player_team_select'
        )

        #filter the dataframe based on the selected team
        if select_team == 'All Teams':
            df_team_players = df_players.copy()
        else:
            df_team_players = df_players[df_players['player.team.name'] == select_team].copy()

        player_list = sorted(df_team_players['player.name'].dropna().unique().tolist())

        #selectbox for player selection with memory on the player selected
        #use session state as the only method for streamlit
        #first check
        if 'saved_player' not in st.session_state:
            st.session_state['saved_player'] = player_list[0]

        #
        if st.session_state['saved_player'] in player_list:
            position = player_list.index(st.session_state['saved_player'])
        else:
            position = 0

        select_player = st.selectbox(
            'Select Player',
            options=player_list,
            index = position
        )

        st.session_state['saved_player'] = select_player
        

    #isolate player data
    player_data = df_team_players[df_team_players['player.name'] == select_player].iloc[0]

    with header_col2:
        st.write('')
        st.write('')
        #player image
        player_img = player_data['player.imageUrl']
        st.image(player_img, width=280)

    with header_col3:
        st.write('')
        st.write('')
        #player age
        player_age = player_data['player.age']
        team_logo = player_data['player.team.imageUrl']

        #debug to extract team name correctly
        actual_team = player_data['player.team.name']
        st.header(f'{select_player}')
        st.write(f'#### **Age:** {player_age} years old')
        st.write(f'#### **Team:** {actual_team}')
        st.image(team_logo, width=130)

    st.write('---')

    #dinmaic kpi cards

    st.subheader(f':orange[{select_mode} Stats]')

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row1_col1:
        st.metric(label='Points', value = f'{round(player_data["pointsScored"], 1)}')

    with row1_col2:
        st.metric(label='Rebounds', value = f'{round(player_data["totalRebounds"], 1)}')

    with row1_col3:
        st.metric(label='Assists', value = f'{round(player_data["assists"], 1)}')

    with row2_col1:
        st.metric(label='Turnovers', value = f'{round(player_data["turnovers"], 1)}')

    with row2_col2:
        st.metric(label='Effective Field Goal%', value=f'{player_data["effectiveFieldGoalPercentage"]}')

    with row2_col3:
        st.metric(label='Performance Index Rating', value=f'{round(player_data["pir"], 1)}')

    st.write('---')