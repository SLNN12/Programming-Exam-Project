import streamlit as st
import intro
#import teams
#import players

#Page configuration
st.set_page_config(
    page_title='Euroleague Analytics',
    page_icon='🏀',
    layout='wide',
)

#Sidebar navigation menu
st.sidebar.title('Navigation Menu')

picked_section = st.sidebar.radio(
    'Go to section:',
    [
        '1. Project Overview',
        '2. Team Analysis',
        '3. Player Analysis',
    ]
)

#Text of the sections
if picked_section == '1. Project Overview':
    st.title(':orange[Project Overview]')
    st.write(
        """
        Welcome to the **Euroleague Analytics Dashboard**! 
        
        This project is designed to provide deep, data-driven insights into the performance of both teams and players across the Euroleague. By navigating through the sidebar, you can explore aggregated team statistics, dive into individual player profiles, and visualize key metrics.
        
        *Why this project?* I built this dashboard to bridge the gap between my biggest passion—basketball—and my academic journey in Data Science. It’s a way to enjoy both worlds simultaneously while building something practical. I hope you enjoy exploring the data as much as I enjoyed putting it together. Let's dive in!
        """
    )
    intro.display_overview()

elif picked_section == '2. Team Analysis':
    st.title('Team Analysis')
    st.write(
        """
        In this section, we zoom in on collective performance. 
        
        Here you will be able to explore various statistics and metrics for Euroleague franchises. From win-loss records to offensive efficiency and overall team contributions, use the sidebar filters to select a team and uncover what drives their success on the court.
        """
    )

elif picked_section == '3. Player Analysis':
    st.title('Player Analysis')
    st.write(
        """
        This section is all about individual talent. 
        
        Here you can explore specific player profiles and their historical statistics. Select a player to view detailed information, analyze their shooting accuracy, review their performance metrics, and see exactly how they impact the game.
        """
    )