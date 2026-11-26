# Riga 2: Punti fatti, Punti subiti, Triple segnate per partita
    row2_col1, row2_col2, row2_col3 = st.columns(3)

    with row2_col1:
        st.metric(
            label="Points Scored (PPG)",
            value=f"{team_data['pointsScored_pg']:.1f}",
            delta=f"{team_data['PTS_Rank']}° in the league",
            delta_color="off",
            help="Average points scored per game."
        )

    with row2_col2:
        st.metric(
            label="Points Allowed (OPP PPG)",
            value=f"{team_data['___']:.1f}",  # INDIZIO 6: colonna 'pointsScored_opp_trad_pg'
            delta=f"{team_data['OPP_PTS_Rank']}° in the league",
            delta_color="off",
            help="Average points allowed per game (lower is better)."
        )

    with row2_col3:
        st.metric(
            label="3-Pointers Made (3PM)",
            value=f"{team_data['threePointersMade_pg']:.1f}",
            delta=f"{team_data['threePM_Rank']}° in the league",
            delta_color="off",
            help="Average three-pointers made per game."
        )

    # Riga 3: Percentuale da 3, Rimbalzi offensivi, Rimbalzi difensivi
    row3_col1, row3_col2, row3_col3 = st.columns(3)

    with row3_col1:
        st.metric(
            label="3-Point % (3P%)",
            value=f"{team_data['threePointersPercentage']:.1f}%",
            delta=f"{team_data['threeP_Pct_Rank']}° in the league",
            delta_color="off",
            help="Three-point field goal percentage."
        )

    with row3_col2:
        st.metric(
            label="Off. Rebounds (ORB)",
            value=f"{team_data['___']:.1f}",  # INDIZIO 7: colonna 'offensiveRebounds_pg'
            delta=f"{team_data['ORB_Rank']}° in the league",
            delta_color="off",
            help="Average offensive rebounds per game."
        )

    with row3_col3:
        st.metric(
            label="Def. Rebounds (DRB)",
            value=f"{team_data['___']:.1f}",  # INDIZIO 8: colonna 'defensiveRebounds_pg'
            delta=f"{team_data['DRB_Rank']}° in the league",
            delta_color="off",
            help="Average defensive rebounds per game."
        )