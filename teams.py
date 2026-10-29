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
        df_team_trad, df_team_adv, df_team_opp_trad, df_team_opp_adv = load_team_stats(selected_season)

        #removing duplicates from the sets
        cols_to_drop= ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']

        df_adv_clean = df_team_adv.drop(columns=[c for c in cols_to_drop if c in df_team_adv.columns])
        #merging the teams stats
        df_team_full = pd.merge(df_team_trad, df_team_adv, on='team.code')

        
    
        df_opp_trad_clean = df_team_opp_trad.drop(columns=[c for c in cols_to_drop if c in df_team_opp_trad.columns])
        df_opp_adv_clean = df_team_opp_adv.drop(columns=[c for c in cols_to_drop if c in df_team_opp_adv.columns])
        
        df_team_full = pd.merge(df_team_trad, df_opp_trad_clean, on='team.code', suffixes=('', '_opp_trad'))
        df_team_full = pd.merge(df_team_trad, df_opp_adv_clean, on='team.code', suffixes=('', '_opp_adv'))

        team_list = sorted(df_team_full['team.name'].dropna().unique().tolist())
    

        with col_sel2:
            selected_team = st.selectbox(
                'Select a team:',
                options = team_list,
                key='team_name_select'
            )
    st.write(df_team_full.columns)
    #showing the team logo up right in ther page
    with header_col3:
        logo_url = df_team_full[df_team_full['team.name']== selected_team]['team.imageUrl'].values[0]

        #inserting space to aligne it
        st.write('')
        st.image(logo_url, width=120)

    st.write('---')


    # merge with standing data to get point against
    df_standings, _ = load_data(selected_season)
    df_standings = df_standings.rename(columns={'club.code': 'team.code'})
    df_team_full = pd.merge(df_team_full, df_standings[['team.code', 'pointsAgainst']], on='team.code')

    cols_to_num = ['twoPointersAttempted', 'threePointersAttempted', 'freeThrowsAttempted', 
                   'offensiveRebounds', 'turnovers', 'pointsScored', 'pointsAgainst', 
                   'steals', 'blocks', 'foulsDrawn', 'gamesPlayed']

    #func to transform numeric metric in % metric
    def clean_numeric_value(val):
        if pd.isna(val):
            return 0.0
        val_str =str(val).replace('%', '').strip()
        try:
            num = float(val_str)
            #if the number is a decimal between 0 and 1, took it in scale 0-100
            if 0.0<=num <=1.0:
                return num*100
            return num
        except ValueError:
            return 0.0
    for col in cols_to_num:
        if col in df_team_full.columns:
            df_team_full[col] = df_team_full[col].apply(clean_numeric_value)

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
            label="Offensive Rating", 
            value=f"{team_data['O_Rating']:.1f}",       
            delta=f"{team_data['O_Rank']}° in the league",  
            delta_color="off"         
        )
        
    with kpi_col2:
        st.metric(
            label="Difensive Rating", 
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
