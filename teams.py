import streamlit as st 
import pandas as pd
import plotly.express as px 
import plotly.graph_objects as go
from data_loader import load_data, load_team_stats, load_round_standings

def display_teams():
    st.write( '---')

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
            #download the data
    with st.spinner('Downloading Euroleague Data...'):
        df_team_trad, df_team_adv, df_team_opp_trad, df_team_opp_adv = load_team_stats(selected_season)

        #removing duplicates from the sets
        cols_to_drop= ['team.name', 'team.imageUrl', 'team.tvCodes', 'teamRanking', 'gamesPlayed']

        df_adv_clean = df_team_adv.drop(columns=[c for c in cols_to_drop if c in df_team_adv.columns])
        #merging the teams stats
        df_team_full = pd.merge(df_team_trad, df_adv_clean, on='team.code')

        
    
        df_opp_trad_clean = df_team_opp_trad.drop(columns=[c for c in cols_to_drop if c in df_team_opp_trad.columns])
        df_opp_adv_clean = df_team_opp_adv.drop(columns=[c for c in cols_to_drop if c in df_team_opp_adv.columns])
        
        df_team_full = pd.merge(df_team_full, df_opp_trad_clean, on='team.code', suffixes=('', '_opp_trad'))
        df_team_full = pd.merge(df_team_full, df_opp_adv_clean, on='team.code', suffixes=('', '_opp_adv'))

        team_list = sorted(df_team_full['team.name'].dropna().unique().tolist())
    

        with col_sel2:
            selected_team = st.selectbox(
                'Select a team:',
                options = team_list,
                key='team_name_select'
            )
    #st.write(df_team_full.columns) -- used to check the imported columns from the API, to check if they are present or not
    #showing the team logo up right in the page with the win/loss record
    with header_col3:
        #obtain team info for the selected team
        team_info = df_team_full[df_team_full['team.name'] == selected_team].iloc[0]
        logo_url = team_info['team.imageUrl']
        team_code = team_info['team.code']

        #get the latest round played by the team fixing the maximum number to the number of games in the regular season
        total_teams = len(df_team_full)
        max_games = (total_teams - 1) * 2
        latest_round = min(max(int(team_info['gamesPlayed']), 1), max_games)

        #load the standings for the latest round
        df_latest_standings = load_round_standings(selected_season, latest_round)
        df_latest_standings = df_latest_standings.rename(columns={'club.code': 'team.code'})

        #iso the team row for the selected team
        team_record = df_latest_standings[df_latest_standings['team.code'] == team_code].iloc[0]

        wins = team_record['gamesWon']
        losses = team_record['gamesLost']

        #layout for logo and record
        logo_col, record_col = st.columns([1.2, 1])

        with logo_col:
            st.write('')
            st.image(logo_url, width=110)

        with record_col:
            st.write('')
            st.write("")
            st.subheader(f":orange[{wins}W - {losses}L]")

    st.write('---')


    cols_to_num = [
            # Base metrics
            'twoPointersAttempted', 'threePointersAttempted', 'freeThrowsAttempted', 
            'offensiveRebounds', 'defensiveRebounds', 'turnovers', 'turnovers_opp_trad',
            'assists', 'pointsScored', 'steals', 'blocks', 'foulsDrawn', 'gamesPlayed',
            
            # Metric for the Offensive Radar
            'effectiveFieldGoalPercentage', 
            'assistsRatio', 
            'offensiveReboundsPercentage', 
            'turnoversRatio',
            
            # Metric for the Defensive Radar
            'effectiveFieldGoalPercentage_opp_adv', 
            'defensiveReboundsPercentage', 
            'turnoversRatio_opp_adv', 
            'twoPointersPercentage_opp_trad'
        ]

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

    #calcuating stats per game
    df_team_full['AST_per_game'] = df_team_full.eval('assists / gamesPlayed')
    df_team_full['ORB_per_game'] = df_team_full.eval('offensiveRebounds / gamesPlayed')
    df_team_full['DRB_per_game'] = df_team_full.eval('defensiveRebounds / gamesPlayed')
    df_team_full['TOV_per_game'] = df_team_full.eval('turnovers / gamesPlayed')
    df_team_full['opp_TOV_per_game'] = df_team_full.eval('turnovers_opp_trad / gamesPlayed')

    # creating offensive and defensive rating columns
    df_team_full['O_Rating'] = df_team_full.eval('(pointsScored / Possessions) * 100')
    df_team_full['D_Rating'] = df_team_full.eval('(pointsScored_opp_trad / Possessions) * 100')
    

    # Create a personal metric called hustle index, the teams who plays with the most intesity have an higher index
    # Formula: (steals + blocks + offensiveRebounds + foulsDrawn) / gamesPlayed
    
    df_team_full['Hustle_Index'] = df_team_full.eval('(steals + blocks + offensiveRebounds + foulsDrawn)/ gamesPlayed')
    

    #rank calc
    df_team_full['O_Rank'] = df_team_full['O_Rating'].rank(ascending=False).astype(int)
    df_team_full['D_Rank'] = df_team_full['D_Rating'].rank(ascending=True).astype(int)
    df_team_full['Hustle_Rank'] = df_team_full['Hustle_Index'].rank(ascending=False).astype(int)

   # KPI CARDS
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

    #create a copy of the df to use for the radar chart
    df_radar = df_team_full.copy()

    #Func to normalize the metrics to a scale of 0-100 with inversion logic 
    def normalize_metric(df, columns, invert=False, floor=15):
        min_val = df[columns].min()
        max_val = df[columns].max()

        norm = ((df[columns] - min_val) / (max_val - min_val)) * 100

        if invert:
            norm = 100 - norm
        norm = floor +(norm*(100-floor)/100) #flooring the values to avoid 0 in the radar chart
        return norm

    #use the function to normalize the metrics for the radar chart with new columns
    #offensive radar metrics
    df_radar['O_Rating_norm'] = normalize_metric(df_radar, 'O_Rating', invert=False)
    df_radar['eFG%_norm'] = normalize_metric(df_radar, 'effectiveFieldGoalPercentage', invert=False)
    df_radar['AST%_norm'] = normalize_metric(df_radar, 'assistsRatio', invert=False)
    df_radar['ORB%_norm'] = normalize_metric(df_radar, 'offensiveReboundsPercentage', invert=False)
    df_radar['TOV%_norm'] = normalize_metric(df_radar, 'turnoversRatio', invert=True)

    #defensive radar metrics
    df_radar['D_Rating_norm'] = normalize_metric(df_radar, 'D_Rating', invert=True)
    df_radar['opp_eFG%_norm'] = normalize_metric(df_radar, 'effectiveFieldGoalPercentage_opp_adv', invert=True)
    df_radar['DRB%_norm'] = normalize_metric(df_radar, 'defensiveReboundsPercentage', invert=False)
    df_radar['opp_TOV%_norm'] = normalize_metric(df_radar, 'turnoversRatio_opp_adv', invert=False)
    df_radar['opp_2P%_norm'] = normalize_metric(df_radar, 'twoPointersPercentage_opp_trad', invert=True)

    #prepare the data for the radar chart
    off_norm_cols = ['O_Rating_norm', 'eFG%_norm', 'AST%_norm', 'ORB%_norm', 'TOV%_norm']
    def_norm_cols = ['D_Rating_norm', 'opp_eFG%_norm', 'DRB%_norm', 'opp_TOV%_norm', 'opp_2P%_norm']

    off_labels = ['Offensive Rating', 'eFG%', 'Assists %', 'Off Rebound %', 'Ball Security']
    def_labels = ['Defensive Rating (Inverted)', 'Opp eFG% (Inverted)', 'Def Rebound %', 'Turnover Forced', 'Opp 2P%(Inverted)']

    team_idx = df_radar[df_radar['team.name'] == selected_team].index[0]
    team_values_off = df_radar.loc[team_idx, off_norm_cols].values
    team_values_def = df_radar.loc[team_idx, def_norm_cols].values

    #extract the real values for the selected team to show in the hover tooltip
    raw_off_cols = ['O_Rating', 'effectiveFieldGoalPercentage', 'assistsRatio', 'AST_per_game', 'offensiveReboundsPercentage', 'ORB_per_game', 'turnoversRatio', 'TOV_per_game']
    raw_off_vals = df_team_full.loc[team_idx, raw_off_cols].values

    off_hover_text = [
        f"Offensive rating: {round(raw_off_vals[0], 1)} pts/100 poss",
        f"eFG%: {round(raw_off_vals[1], 1)} %",
        f"Assists: {round(raw_off_vals[2], 1)}% ({round(raw_off_vals[3], 1)} per game)",
        f"Off Rebound %: {round(raw_off_vals[4], 1)}% ({round(raw_off_vals[5], 1)} per game)",
        f"Turnover %(Inverted): {round(raw_off_vals[6], 1)}% ( {round(raw_off_vals[7], 1)} per game)"    
    ]

    raw_def_cols = ['D_Rating', 'effectiveFieldGoalPercentage_opp_adv', 'defensiveReboundsPercentage', 'DRB_per_game', 'turnoversRatio_opp_adv', 'opp_TOV_per_game', 'twoPointersPercentage_opp_trad']
    raw_def_vals = df_team_full.loc[team_idx, raw_def_cols].values

    def_hover_text = [
        f"Defensive rating: {round(raw_def_vals[0], 1)} pts/100 poss",
        f"Opp eFG% (Inverted): {round(raw_def_vals[1], 1)} %",
        f"Def Rebound %: {round(raw_def_vals[2], 1)}% ({round(raw_def_vals[3], 1)} per game)",
        f"Opp Turnover %: {round(raw_def_vals[4], 1)}% ({round(raw_def_vals[5], 1)} per game)",
        f"Opp 2P%(Inverted): {round(raw_def_vals[6], 1)} %"    
    ]

    #create list for the select box to choose what to compare the selected team with
    comp_options = ['League Average'] + sorted(list(df_radar['team.name'].unique()))
    select_comp = st.selectbox('Compare against:', comp_options)

    if select_comp == 'League Average':
        #normalized values for the league average
        comp_val_off = df_radar[off_norm_cols].mean().values
        comp_val_def = df_radar[def_norm_cols].mean().values

        #raw values for the league average
        comp_raw_off = df_team_full[raw_off_cols].mean().values
        comp_raw_def = df_team_full[raw_def_cols].mean().values
        comp_name = 'League Average'
    else:
        comp_idx = df_radar[df_radar['team.name'] == select_comp].index[0]
        #normalized values for the selected comparison team
        comp_val_off = df_radar.loc[comp_idx, off_norm_cols].values
        comp_val_def = df_radar.loc[comp_idx, def_norm_cols].values
        #raw values for the selected comparison team
        comp_raw_off = df_team_full.loc[comp_idx, raw_off_cols].values
        comp_raw_def = df_team_full.loc[comp_idx, raw_def_cols].values

        comp_name = select_comp


    #comparison hover text for the radar chart
    comp_off_hover_text = [
        f"Offensive rating: {round(comp_raw_off[0], 1)} pts/100 poss",
        f"eFG%: {round(comp_raw_off[1], 1)} %",
        f"Assists: {round(comp_raw_off[2], 1)}% ({round(comp_raw_off[3], 1)} per game)",
        f"Off Rebound %: {round(comp_raw_off[4], 1)}% ({round(comp_raw_off[5], 1)} per game)",
        f"Turnover %(Inverted): {round(comp_raw_off[6], 1)}% ({round(comp_raw_off[7], 1)} per game)"    
    ]

    comp_def_hover_text = [
        f"Defensive rating: {round(comp_raw_def[0], 1)} pts/100 poss",
        f"Opp eFG% (Inverted): {round(comp_raw_def[1], 1)} %",
        f"Def Rebound %: {round(comp_raw_def[2], 1)}% ({round(comp_raw_def[3], 1)} per game)",
        f"Opp Turnover %: {round(comp_raw_def[4], 1)}% ({round(comp_raw_def[5], 1)} per game)",
        f"Opp 2P%(Inverted): {round(comp_raw_def[6], 1)} %"    
    ]

    #build the graphic
    col_radar1, col_radar2 = st.columns(2)

    with col_radar1:
        fig_off = go.Figure()
        fig_off.add_trace(go.Scatterpolar(r=comp_val_off, theta=off_labels, fill='toself', name=comp_name, line_color='darkgray', opacity=0.5, text=comp_off_hover_text, hoverinfo='text'))

        # Add the selected team trace
        fig_off.add_trace(go.Scatterpolar(r=team_values_off, theta=off_labels, fill='toself', name=selected_team, line_color='darkorange', text= off_hover_text, hoverinfo='text'))

        fig_off.update_layout(
            title='Offensive Radar', 
            height=430, 
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor='top',
                y=-0.25,
                xanchor="center",
                x=0.5
            )
        )
        fig_off.update_polars(radialaxis_range=[0, 100])
        st.plotly_chart(fig_off, use_container_width=True)

    with col_radar2:
        fig_def = go.Figure()
        fig_def.add_trace(go.Scatterpolar(r=comp_val_def, theta=def_labels, fill='toself', name=comp_name, line_color='gray', opacity=0.5, text=comp_def_hover_text, hoverinfo='text'))

        # Add the selected team trace
        fig_def.add_trace(go.Scatterpolar(r=team_values_def, theta=def_labels, fill='toself', name=selected_team, line_color='darkorange', text= def_hover_text, hoverinfo='text'))

        fig_def.update_layout(
            title='Defensive Radar',
            height=430,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor='top',
                y=-0.25,
                xanchor="center",
                x=0.5
            )
        )
        fig_def.update_polars(radialaxis_range=[0, 100])
        st.plotly_chart(fig_def, use_container_width=True)