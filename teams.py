import streamlit as st 
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
from data_loader import load_data, load_team_stats

def display_teams():
    st.write( '---')

    #download the data
    with st.spinner('Downloading Euroleague Data...'):

        #base data 
        df_team_list, _ = load_data(2026)

    #3 cols layout for the header
    header_col1, header_col2, header_col3 = st.columns([2,1,2])

    with header_col1:
        st.subheader(':orange[Team Analysis]')

        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_season = st.selectbox(
                'Select a season:',
                options=[2026,2025,2024,2023,2022],
                key='team_season_select' #to avoid conflict with the intro selection menu
            )
        #downloading real stats now that we have the seasons
        df_team_trad, df_team_adv = load_team_stats(selected_season)

        #merging the 2 dataset
        df_team_full = pd.merge(df_team_trad, df_team_adv, on=['team.code', 'team.name', 'team.imageUrl', 'gamesPlayed'])

        team_list = sorted(df_team_full['team.name'].dropna().unique().tolist())

        with col_sel2:
            selected_team = st.selectbox(
                'Select a team:',
                options = team_list,
                key='team_name_select'
            )

    #showing the team logo up right in ther page
    with header_col3:
        logo_url = df_team_full[df_team_full['team.name']== selected_team]['team.imageUrl'].values[0]

        #inserting space to aligne it
        st.write('')
        st.image(logo_url, width=120)

    st.write('---')

    #isolate team data for the next analysis
    team_data = df_team_full[df_team_full['team.name']== selected_team].iloc[0]

    # merge with standing data to get point against
    df_standings, _ = load_data(selected_season)
    df_standings = df_standings.rename(columns={'club.code': 'team.code'})
    df_team_full = pd.merge(df_team_full, df_standings[['team.code', 'pointsAgainst']], on='team.code')

    cols_to_num = ['twoPointersAttempted', 'threePointersAttempted', 'freeThrowsAttempted', 
                   'offensiveRebounds', 'turnovers', 'pointsScored', 'pointsAgainst', 
                   'steals', 'blocks', 'foulsDrawn', 'gamesPlayed']
    for col in cols_to_num:
        df_team_full[col] = pd.to_numeric(df_team_full[col], errors='coerce')

    # Creating Field goal atttempted columns
    df_team_full['FGA'] = df_team_full['twoPointersAttempted'] + df_team_full['threePointersAttempted']

    # Creating Possessions columns, the formula is the official one by FIBA
    df_team_full['Possessions'] = df_team_full.eval('FGA + (0.44* freeThrowsAttempted) - offensiveRebounds + turnovers')
    

    # creating offensive and defensive rating columns
    df_team_full['O_Rating'] = df_team_full.eval('(pointsScored / Possessions) * 100')
    df_team_full['D_Rating'] = df_team_full.eval('(pointsAgainst / Possessions) * 100')
    

    # Create a personal metric called hustle index, the teams who plays with the most intesity have an higher index
    # Formula: (steals + blocks + offensiveRebounds + foulsDrawn) / gamesPlayed
    
    df_team_full['Hustle_Index'] = df_team_full.eval('(steals + blocks + offensiveRebounds + foulsDrawn)/ gamesPlayed')
    

    #rank calc
    df_team_full['O_Rank'] = df_team_full['O_Rating'].rank(ascending=False).astype(int)
    df_team_full['D_Rank'] = df_team_full['D_Rating'].rank(ascending=True).astype(int)
    df_team_full['Hustle_Rank'] = df_team_full['Hustle_Index'].rank(ascending=False).astype(int)

   # KPI CARDS
    st.write("---")
    
    # isolate selected team row
    team_data = df_team_full[df_team_full['team.name'] == selected_team].iloc[0]

    # create 3 vertical columns
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    
    with kpi_col1:
        st.metric(
            label="O-Rating", 
            value=f"{team_data['O_Rating']:.1f}",       
            delta=f"{team_data['O_Rank']}° in the league",  
            delta_color="off"         
        )
        
    with kpi_col2:
        st.metric(
            label="D-Rating", 
            value=f"{team_data['D_Rating']:.1f}",       
            delta=f"{team_data['D_Rank']}° in the league",  
            delta_color="off"
        )
        
    with kpi_col3:
        st.metric(
            label="Hustle Index", 
            value=f"{team_data['Hustle_Index']:.1f}",      
            delta=f"{team_data['Hustle_Rank']}° in the league",  
            delta_color="off"
        )
    st.write('The hustle index is calculated with this formula: (steals + blocks + offensiveRebounds + foulsDrawn) / gamesPlayed')
    st.write("---")

    # radar chart 
    st.subheader(":orange[Tactical Profile vs League Average]")

    radar_metrics = [
        'effectiveFieldGoalPercentage', 
        'trueShootingPercentage', 
        'offensiveReboundsPercentage', 
        'defensiveReboundsPercentage', 
        'assistsRatio'
    ]

    #convert the metrics in number
    for col in radar_metrics:
        df_team_full[col] = df_team_full[col].astype(str).str.replace('%', '')
        df_team_full[col] = pd.to_numeric(df_team_full[col], errors='coerce')

    # calculating league average for the metrics
    league_avg = df_team_full[radar_metrics].mean()

    # raw team values
    team_values = team_data[radar_metrics].values

    # indices the graph
    fig_radar = go.Figure()

    # league average radar
    fig_radar.add_trace(go.Scatterpolar(
        # assign to r the league average values
        r = league_avg,
        # assign the name with the list of radar metrics
        theta = radar_metrics,
        fill = 'toself',
        name = 'League Average',
        line_color = 'gray',
        opacity = 0.5
    ))

    #Selected team radar
    fig_radar.add_trace(go.Scatterpolar(
        # assign team name and metrics name
        r = team_values,
        theta = radar_metrics,
        fill = 'toself',
        name = selected_team,
        line_color = 'orange'
    ))

    # laoyout and printing
    fig_radar.update_layout(
        polar = dict(
            radialaxis = dict(visible=True, range=[0, 65])
        ),
        showlegend = True,
        height = 500
    )

    st.plotly_chart(fig_radar, use_container_width=True)