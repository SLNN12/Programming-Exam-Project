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
        if 'saved_player' not in st.session_state:
            st.session_state['saved_player'] = player_list[0]

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
        #team name
        actual_team_name = player_data['player.team.name']

        st.header(f'{select_player}')
        st.write(f'#### **Age** {player_age} years old')
        st.write(f'#### **Team** {actual_team_name}')

        #plotly donut graph
        #turn the raw str in to float value
        raw_2p = player_data[ 'pointsFromTwoPointersPercentage']
        raw_3p = player_data['pointsFromThreePointersPercentage']
        raw_ft = player_data['pointsFromFreeThrowsPercentage']

        val_2p = float(str(raw_2p).replace('%', '') if pd.notna(raw_2p) else 0.0)
        val_3p = float(str(raw_3p).replace('%', '') if pd.notna(raw_2p) else 0.0)
        val_ft = float(str(raw_ft).replace('%', '') if pd.notna(raw_2p) else 0.0)

        col_logo, col_donut = st.columns(2)

        with col_logo:
            team_logo = player_data['player.team.imageUrl']
            st.image(team_logo, width = 150)

        with col_donut:
            labelz = ['2-Pointers', '3-Pointers', 'Free Throws']
            vals = [val_2p, val_3p, val_ft]

            #ai generated euroleague color palette
            euroleague_palette = ['#FF5500', '#0C2340', '#8A99A8']

            fig_scoring = px.pie(
                names= labelz,
                values = vals,
                hole = 0.6,
                color_discrete_sequence= euroleague_palette,

            )

            fig_scoring.update_traces(textposition='inside', textinfo='percent+label')

            #.update_traces(textinfo='none')

            fig_scoring.update_layout(
                showlegend=False,
                height=150,
                #put the margin = 0 to optimize the space
                margin =dict(t=0, b=0, l=0, r=0)
            )

            st.plotly_chart(fig_scoring, use_container_width= True)


    st.write('---')

    #dinmaic kpi cards

    st.subheader(f':orange[{select_mode} Stats]')

    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row1_col1:
        if select_mode == 'PerMinute':
            pts_help = 'Projected points per 40 minutes of play (full FIBA game). Allows a fair comparison between starters and bench players regardless of actual playing time.'
        else:
            pts_help= None
        st.metric(label='Points',
                value = f'{round(player_data["pointsScored"], 1)}',
                help = pts_help
                )

    with row1_col2:
        st.metric(label='Rebounds', value = f'{round(player_data["totalRebounds"], 1)}')

    with row1_col3:
        st.metric(label='Assists', value = f'{round(player_data["assists"], 1)}')

    with row2_col1:
        st.metric(label='Turnovers', value = f'{round(player_data["turnovers"], 1)}')

    with row2_col2:
        st.metric(label='Effective Field Goal%', 
                value=f'{player_data["effectiveFieldGoalPercentage"]}',
                help="Effective Field Goal Percentage: measures shooting efficiency adjusting for the fact that 3-pointers are worth 50% more than 2-pointers. Formula: (FGM + 0.5 * 3PM) / FGA"
                )

    with row2_col3:
        st.metric(label='Performance Index Rating', 
                value=f'{round(player_data["pir"], 1)}', 
                help="Performance Index Rating: (PTS + REB + AST + STL + BLK + Fouls Drawn) - (Missed Shots + TO + BLK Suffered + Fouls Committed)"
                )

    st.write('---')