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
        if 'saved_player' in st.session_state:
            saved_name = st.session_state['saved_player']
        else:
            saved_name = ''

        #default selecting first player on the list
        selected_default = player_list[0] if player_list else ''

        #if a player was saved search corrispondence
        if saved_name:
            search_word = saved_name.replace(',', '').split()[0].lower()
            for p in player_list:
                if search_word in p.lower():
                    selected_default = p
                    break
        st.session_state['saved_player'] = selected_default



        select_player = st.selectbox(
            'Select Player',
            options=player_list,
            key='saved_player'
        )

        

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
                hole = 0.35,
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
    row3_col1, row3_col2, row3_col3 = st.columns(3)

    with row1_col1:
        if select_mode == 'PerMinute':
            pts_help = 'Projected points per 40 minutes of play (full FIBA game). Allows a fair comparison between starters and bench players regardless of actual playing time.'
        elif select_mode == 'Per100Possesions':
            pts_help = 'It shows how many points a player scores, on average, for every 100 possessions they use. Points per 100 possessions = (player’s points / possessions played) × 100.'
        elif select_mode == 'PerGame':
            pts_help = 'Average points scored per game.'
        elif select_mode == 'Accumulated':
            pts_help = 'Total points scored throughout the season.'
        st.metric(label='Points',
                value = player_data['pointsScored'],
                help = pts_help
                )

    with row1_col2:
        if select_mode == 'PerGame':
            reb_help = 'Average total rebounds (offensive + defensive) per game.'
        elif select_mode=='Accumulated':
            reb_help= 'Total rebounds accumulated throughout the season'
        elif select_mode == 'PerMinute':
            reb_help = 'Projected total rebounds per 40 minutes of active play (full FIBA game)'
        elif select_mode == 'Per100Possesions':
            reb_help = 'Projected total rebounds per 100 team possessions.'
        st.metric(label='Rebounds', 
                  value = player_data['totalRebounds'],
                  help = reb_help
                  )

    with row1_col3:
        if select_mode == 'PerGame':
            ast_help = 'Average assists per game played'
        elif select_mode=='Accumulated':
            ast_help= 'Total assists accumulated throughout the season'
        elif select_mode == 'PerMinute':
            ast_help = 'Projected assists per 40 minutes of play (full FIBA game)'
        elif select_mode == 'Per100Possesions':
            ast_help = 'Projected total assist per 100 team possessions.'
        st.metric(label='Assists', 
                  value = player_data['assists'],
                  help=ast_help
                  )

    with row2_col1:
        if select_mode == 'PerGame':
            trv_help = 'Average balls lost per game played'
        elif select_mode=='Accumulated':
            trv_help= 'Total balls lost accumulated throughout the season'
        elif select_mode == 'PerMinute':
            trv_help = 'Projected balls lost per 40 minutes of play (full FIBA game)'
        elif select_mode == 'Per100Possesions':
            trv_help = 'Projected total balls lost per 100 team possessions.'
        st.metric(label='Turnovers',
                  value = player_data['turnovers'],
                  help= trv_help
                  )

    with row2_col2:
        st.metric(label='Effective Field Goal%', 
                value=player_data['effectiveFieldGoalPercentage'],
                help="Effective Field Goal Percentage: measures shooting efficiency adjusting for the fact that 3-pointers are worth 50% more than 2-pointers. Formula: (FGM + 0.5 * 3PM) / FGA"
                )

    with row2_col3:
        st.metric(label='Performance Index Rating', 
                value=player_data['pir'], 
                help="Performance Index Rating: (PTS + REB + AST + STL + BLK + Fouls Drawn) - (Missed Shots + TO + BLK Suffered + Fouls Committed)"
                )

    player_data['stocks'] = player_data['steals'] + player_data['blocks']
    with row3_col1:
        st.metric(label='Stocks',
                value = player_data['stocks'],
                help = 'Combined Steals plus Blocks'
                )

    
    with row3_col2:
        if select_mode == 'PerGame':
            mp_help = 'Average minutes played per game'
        elif select_mode=='Accumulated':
            mp_help= 'Total minutes played throughout the season'
        elif select_mode == 'PerMinute':
            mp_help = 'Standard reference scale (40 minutes active play per full FIBA game)'
        elif select_mode == 'Per100Possesions':
            mp_help = 'Average playing time per game, providing sample size context for 100-possession estimates.'
        st.metric(label = 'Minutes played',
                value = round(player_data['minutesPlayed'],1),
                help = mp_help
                )

    with row3_col3:
            if select_mode == 'PerGame':
                fd_help = 'Average fouls drawn per game.'
            elif select_mode=='Accumulated':
                fd_help= 'Total fouls drawn throughout the season.'
            elif select_mode == 'PerMinute':
                fd_help = 'Projected fouls drawn per 40 minutes of play (full FIBA game).'
            elif select_mode == 'Per100Possesions':
                fd_help = 'Projected fouls drawn per 100 team possessions.'
            st.metric(label = 'Fouls Drawn',
                    value = player_data['foulsDrawn'],
                    help = fd_help
                    )

    
    st.write('---')
    st.subheader(':orange[Player Comparison Scattter Plot]')

    #mapping 5 scatter presets

    preset_plots = {
        'Scorer Efficiency (Points vs eFG%)':{
            'x_col': 'pointsScored',
            'y_col': 'effectiveFieldGoalPercentage',
            'x_label' : 'Points',
            'y_label': 'Effective Field Goal %'
        },
        'Volume & Productivity (Minutes vs PIR)':{
            'x_col' : 'minutesPlayed',
            'y_col' : 'pir',
            'x_label' : 'Minutes Played',
            'y_label' : 'PIR'
        },
        'Minutes vs Points':{
            'x_col' : 'pointsScored',
            'y_col': 'minutesPlayed',
            'y_label': 'Minutes Played',
            'x_label': 'Points'
        },
        'Points vs Assists': {
            'x_col' : 'pointsScored',
            'y_col': 'assists',
            'x_label': 'Points',
            'y_label': 'Assists'
        },
        'Defensive Profile( Defensive Rebound vs Stocks)':{
            'x_col': 'defensiveRebounds',
            'y_col': 'stocks',
            'x_label': 'Defensive Rebounds',
            'y_label': 'Steals + Blocks'
        }
    }

    #Selctbox for the scatter
    selected_preset = st.selectbox(
        'Select Analytical Scatter Plot',
        options = list(preset_plots),
        key='player_scatter_preset'
    )

    #extract the picked graph fro the dict
    config = preset_plots[selected_preset]

    #Create dthe dataframe for plotly
    df_scatter = df_team_players.copy()

    #add stocks column
    df_scatter['stocks'] = df_scatter['steals']+ df_scatter['blocks']

    #revoering the selected player
    current_player = st.session_state['saved_player']

    #create the column to highlight the selected player in the graph
    df_scatter['highlight'] = df_scatter['player.name'].apply(
        lambda name: 'Selected Player' if name == current_player else 'Other Players'
    )

    #creation of the scatter plot

    fig_scatter = px.scatter(
        df_scatter,
        x=config['x_col'],
        y=config['y_col'],
        color = 'highlight',
        color_discrete_map= {
            'Selected Player': 'tomato',
            'Other Players': 'dimgray'
        },
        hover_name = 'player.name',
        labels = {
            config[ 'x_col']: config['x_label'],
            config['y_col']: config['y_label']
        },
        title = f'{selected_preset} ({select_mode})'
    )

    fig_scatter.update_traces(marker=dict(size=12, opacity=0.8))

    st.plotly_chart(fig_scatter, use_container_width=True)


