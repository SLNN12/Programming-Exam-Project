import streamlit as st
import pandas as pd
import plotly.express as px
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
        return pd.DataFrame()  # Return an empty DataFrame if no data is available
    
    

def display_overview():
    """ Called by app.py, displays the overview section of the app. """
    st.write('---')
    st.subheader(':orange[Season Overview]')

    #creating the selection menus
    col_sel1, col_sel2 = st.columns(2)

    with col_sel1:
        selected_season = st.selectbox(
            'Select a season:',
            options=[2026, 2025, 2024, 2023, 2022]
            )

    #recalling the cached data
    with st.spinner("Downloading EuroLeague Data..."):
        df_teams, df_player_all = load_data(selected_season)
    
    #creating dynamic list
    team_list = ['All Teams'] + sorted(df_teams['club.name'].dropna().unique().tolist())

    with col_sel2:
        selected_team = st.selectbox(
            'Select a Team:',
            options = team_list
        )


    #KPI

    total_teams_league = len(df_teams) #obtaining the teams total number

    if selected_team == 'All Teams':
        display_teams = total_teams_league
        display_games = int(total_teams_league * (total_teams_league - 1))
        df_player_active = df_player_all.copy()
    else:
        display_teams = 1
        display_games= (total_teams_league -1) *2 #games played by 1 team

        #gain the team code from standing dataset
        team_code = df_teams[df_teams['club.name']== selected_team]['club.code'].values[0]

        #filter players using team code
        df_player_active = df_player_all[df_player_all['player.team.code']== team_code].copy()


        

    total_players = len(df_player_active)

  
    col_3pm_list = [ col for col in df_player_active.columns if 'threepointersmade' in col.lower()]

    if len(col_3pm_list):
        col_3pm = col_3pm_list[0]
        total_threes = int (pd.to_numeric(df_player_active[col_3pm], errors='coerce').sum())
    else: 
        total_threes = 'N/A'

    #displaying KPIs
    st.divider() #separation line
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Teams", value= display_teams)

    with col2:
        st.metric(label="Total Games", value=display_games)

    with col3:
        st.metric(label="Total Players", value=total_players)

    with col4:
        st.metric(label="Total 3-Pointers Made", value=total_threes)

    st.divider() #separation line

    #displaying standings graph

    st.subheader(':orange[Standings Evolution Over the Season]')

    with st.spinner("Downloading EuroLeague Standings Trend Data..."): 
        df_trend = load_standings_trend(selected_season, total_teams_league)

    if not df_trend.empty:
        #graph filter
        if selected_team == 'All Teams':
            df_trend_active = df_trend.copy()
        else:
            df_trend_active = df_trend[df_trend['club.name']==selected_team].copy()
        team_col = 'club.name'
        rank_col = 'position'

        #Creating etting for the graphm only at the last round
        max_round_played = df_trend['Round'].max()

        #Columns cointaining the team name
        df_trend_active['Line_Label'] = df_trend_active.apply(
            lambda x: str(x[ 'club.abbreviatedName']) if x['Round'] == max_round_played else None, axis=1   
        )

        #creating the graph

        #deciding the color by the filter
        if selected_team == 'All Teams':
            chart_colors = px.colors.qualitative.Plotly
        else:
            chart_colors = ['orange']
        fig = px.line(
            df_trend_active, 
            x='Round',
            y=rank_col,
            color=team_col,
            text = 'Line_Label',
            markers=True,
            color_discrete_sequence = chart_colors
        )

        #moving it to the right to be readable
        fig.update_traces(textposition= 'middle right', textfont_size = 12)

        #Formatting the axes
        fig.update_layout(
            yaxis=dict(
                range=[total_teams_league +0.5, 0.5], #block the standings number
                title='Position in standings',
                dtick=1
            ),
            xaxis=dict(
                range= [0.8, max_round_played + 2.0],
                title='Round',
                dtick=1
            ),
            showlegend=False,
            height=700
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write('No standings trend data available')


    #team logos 
    st.subheader(":orange[──────────────────────────── **Euroleague Teams** ──────────────────────────]")
    

    #searching the column that contains the logo URLs
    logo_col = None
    for col in df_teams.columns:
        if 'image' in col.lower():
            logo_col = col
            break

    if logo_col is not None:
        #creating horiz row with logos
        cols = st.columns(len(df_teams))

        for index, row in df_teams.iterrows():
            with cols[index]:
                st.image(row[logo_col], use_container_width=True)
    else:
        st.write('Logo URLs not found in the dataset.')