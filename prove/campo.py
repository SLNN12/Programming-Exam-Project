import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# ==========================================
# CONFIGURAZIONE PAGINA (Deve essere la prima istruzione)
# ==========================================
st.set_page_config(page_title="Euroleague ML Analytics", page_icon="🏀", layout="wide")

# ==========================================
# FUNZIONI DI SUPPORTO & DATI (Simulazione API)
# ==========================================
@st.cache_data
def get_mock_data():
    """Genera dati fittizi che simulano l'output di euroleague_api per far funzionare l'app out-of-the-box."""
    # 🎯 TODO ESAME: Sostituisci questo con euroleague_api.get_team_stats(...)
    teams_data = pd.DataFrame({
        'Team': ['Olimpia Milano', 'Virtus Bologna', 'Real Madrid', 'Barcelona', 'Fenerbahce'],
        'Logo': [
            'https://upload.wikimedia.org/wikipedia/it/thumb/2/2c/Olimpia_Milano_logo.svg/200px-Olimpia_Milano_logo.svg.png',
            'https://upload.wikimedia.org/wikipedia/it/thumb/a/ab/Virtus_Pallacanestro_Bologna_logo.svg/200px-Virtus_Pallacanestro_Bologna_logo.svg.png',
            'https://upload.wikimedia.org/wikipedia/it/thumb/5/5e/Real_Madrid_Club_de_F%C3%BAtbol.svg/200px-Real_Madrid_Club_de_F%C3%BAtbol.svg.png',
            'https://upload.wikimedia.org/wikipedia/it/thumb/1/1c/FC_Barcelona.svg/200px-FC_Barcelona.svg.png',
            'https://upload.wikimedia.org/wikipedia/it/thumb/c/cd/Fenerbahce_Spor_Kulubu.svg/200px-Fenerbahce_Spor_Kulubu.svg.png'
        ],
        'Pace': [70.5, 72.1, 74.5, 71.8, 73.0],
        'Off_Reb': [10.2, 9.8, 12.5, 11.0, 10.5],
        'Turnovers': [12.5, 13.8, 11.5, 12.0, 11.8],
        'True_Shooting': [0.55, 0.53, 0.59, 0.57, 0.56]
    })
    
    # 🎯 TODO ESAME: Sostituisci con euroleague_api.get_game_shot_data(...)
    # Generiamo coordinate fittizie che abbiano senso nel campo FIBA corretto.
    # x da -7 a +7, y da 0 a 10 (maggior densità vicino al canestro)
    n_shots = 100
    shots_data = pd.DataFrame({
        'loc_x': np.random.normal(0, 3, n_shots).clip(-7, 7), 
        'loc_y': np.random.gamma(2, 2.5, n_shots).clip(0, 10),
        'shot_made': np.random.choice([True, False], n_shots, p=[0.45, 0.55])
    })
    
    return teams_data, shots_data

@st.cache_resource
def train_mock_predictor():
    """Addestra un modello di regressione al volo sui dati di base per il What-If."""
    X_train = np.random.rand(100, 4) * [80, 15, 20, 0.7] # Pace, Off_Reb, TOV, TS%
    y_train = X_train[:, 3] * 100 + X_train[:, 1] * 2 - X_train[:, 2] * 1.5 + np.random.randn(100)*5 
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)
    return model

def draw_fiba_half_court(fig):
    """
    Disegna metà campo FIBA orientato con il canestro in basso (y=0 in fondo al campo).
    Coordinate in metri. Il centro del campo (sotto il canestro) è x=0, y=0.
    """
    line_color = "black"
    line_width = 2
    
    # Costanti campo FIBA
    width = 15.0
    length = 14.0 # metà campo
    basket_y = 1.575 # Il centro del canestro dista 1.575m dalla linea di fondo
    
    shapes = [
        # Perimetro metà campo (dal fondo fino alla linea di metà campo)
        dict(type="rect", x0=-width/2, y0=0, x1=width/2, y1=length, 
             line=dict(color=line_color, width=line_width)),
        
        # Pitturato (Largo 4.9m, Lungo 5.8m partendo dalla linea di fondo)
        dict(type="rect", x0=-2.45, y0=0, x1=2.45, y1=5.8, 
             line=dict(color=line_color, width=line_width)),
        
        # Semicerchio superiore del tiro libero (raggio 1.8m, centro a y=5.8)
        dict(type="path", path="M -1.8 5.8 A 1.8 1.8 0 0 1 1.8 5.8", 
             line=dict(color=line_color, width=line_width)),
        
        # Semicerchio tratteggiato inferiore del tiro libero (opzionale)
        dict(type="path", path="M 1.8 5.8 A 1.8 1.8 0 0 1 -1.8 5.8", 
             line=dict(color=line_color, width=line_width, dash="dash")),

        # Tabellone (Largo 1.8m, distante 1.2m dalla linea di fondo)
        dict(type="line", x0=-0.9, y0=1.2, x1=0.9, y1=1.2, 
             line=dict(color=line_color, width=3)),
        
        # Canestro (Raggio 0.225m, centro a y=1.575, x=0)
        dict(type="circle", x0=-0.225, y0=basket_y - 0.225, x1=0.225, y1=basket_y + 0.225, 
             line=dict(color="orange", width=2)),
        
        # Semicerchio del No-Charge (raggio 1.25m dal centro del canestro)
        dict(type="path", 
             path=f"M -1.25 {basket_y} A 1.25 1.25 0 0 1 1.25 {basket_y}", 
             line=dict(color=line_color, width=line_width)),
        
        # Linea dei 3 punti FIBA (6.75m dal centro del canestro)
        # La linea dritta laterale inizia dalla linea di fondo (y=0) a x = ±6.60
        # e finisce a y=2.99. Da lì inizia l'arco di raggio 6.75m centrato sul canestro.
        dict(
            type="path",
            path=f"M -6.60 0 L -6.60 2.99 A 6.75 6.75 0 0 1 6.60 2.99 L 6.60 0",
            line=dict(color=line_color, width=line_width)
        )
    ]
    
    fig.update_layout(shapes=shapes)
    return fig

# ==========================================
# PAGINE DELL'APP
# ==========================================

def page_intro(teams_data):
    st.title("📊 Euroleague Data Science Project")
    st.markdown("""
    Benvenuti nel progetto di analisi avanzata dell'Eurolega. Questa pipeline estrae dati, li analizza e utilizza il Machine Learning per scoprire pattern nascosti.
    """)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Partite Analizzate", "342", "+12 questa settimana")
    col2.metric("Modelli Addestrati", "2", "Random Forest & K-Means")
    col3.metric("Tiri Mappati", "15.420")
    
    st.divider()
    st.subheader("Pipeline Dati")
    st.markdown("`Euroleague API` ➡️ `Pandas Cleaning` ➡️ `Scikit-Learn ML` ➡️ `Streamlit UI`")
    
    with st.expander("Visualizza un campione del Dataset Squadre (Team Stats)"):
        st.dataframe(teams_data, use_container_width=True)

def page_predictor(teams_data, model):
    st.title("🔮 Match Predictor (What-If Analysis)")
    st.markdown("Simula una partita e modifica le statistiche in tempo reale per vedere come cambia l'esito previsto dal modello di Machine Learning.")
    
    col1, col_vs, col2 = st.columns([2, 1, 2])
    
    with col1:
        team_home = st.selectbox("Squadra in Casa", teams_data['Team'], index=0)
        home_stats = teams_data[teams_data['Team'] == team_home].iloc[0]
        st.image(home_stats['Logo'], width=100)
        
        st.markdown("**Modifica Statistiche:**")
        home_reb = st.slider("Rimbalzi Offensivi", 5.0, 20.0, float(home_stats['Off_Reb']), key="h_reb")
        home_tov = st.slider("Palle Perse", 5.0, 25.0, float(home_stats['Turnovers']), key="h_tov")

    with col2:
        team_away = st.selectbox("Squadra in Trasferta", teams_data['Team'], index=1)
        away_stats = teams_data[teams_data['Team'] == team_away].iloc[0]
        st.image(away_stats['Logo'], width=100)
        
        st.markdown("**Modifica Statistiche:**")
        away_reb = st.slider("Rimbalzi Offensivi", 5.0, 20.0, float(away_stats['Off_Reb']), key="a_reb")
        away_tov = st.slider("Palle Perse", 5.0, 25.0, float(away_stats['Turnovers']), key="a_tov")

    with col_vs:
        st.markdown("<h2 style='text-align: center; margin-top: 50px;'>VS</h2>", unsafe_allow_html=True)
        
        features_home = np.array([[70.0, home_reb, home_tov, 0.55]])
        features_away = np.array([[70.0, away_reb, away_tov, 0.55]])
        
        score_home = model.predict(features_home)[0]
        score_away = model.predict(features_away)[0]
        
        st.markdown(f"<h3 style='text-align: center; color: {'green' if score_home > score_away else 'red'};'>{int(score_home)} - {int(score_away)}</h3>", unsafe_allow_html=True)
        
        if score_home > score_away:
            st.success(f"Vittoria {team_home}")
        else:
            st.error(f"Vittoria {team_away}")

def page_player(shots_data):
    st.title("🎯 Player Analytics & Shot Quality")
    
    giocatore_img = "https://media.npr.org/assets/img/2020/06/10/gettyimages-200199027-1-43d930263f03bba3f07a21f7ed0df9dc7e366e66-s1100-c50.jpg"
    
    col_profilo, col_mappa = st.columns([1, 2])
    
    with col_profilo:
        st.selectbox("Seleziona Giocatore", ["Mike James", "Nikola Mirotic", "Shavon Shields"])
        st.image(giocatore_img, width=150)
        st.markdown("### Archetipo: **Primary Scorer**")
        st.caption("Classificazione K-Means su 5 cluster")
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=[20, 5, 8, 4, 15], theta=['Punti', 'Assist', 'Rimbalzi', 'Palle Perse', 'Tiri Tentati'],
            fill='toself', name='Giocatore'
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[15, 4, 6, 3, 10], theta=['Punti', 'Assist', 'Rimbalzi', 'Palle Perse', 'Tiri Tentati'],
            fill='toself', name='Media Archetipo'
        ))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 25])), showlegend=True)
        st.plotly_chart(fig_radar, use_container_width=True, theme=None)

    with col_mappa:
        st.subheader("Shot Map (Tiri Effettuati)")
        
        df_made = shots_data[shots_data['shot_made'] == True]
        df_miss = shots_data[shots_data['shot_made'] == False]

        fig_court = go.Figure()
        
        # Punto invisibile per stabilizzare gli assi
        fig_court.add_trace(go.Scatter(x=[0], y=[0], mode="markers", marker=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="none"))
        
        # Aggiungo i tiri segnati (Cerchi verdi)
        fig_court.add_trace(go.Scatter(
            x=df_made['loc_x'], y=df_made['loc_y'], mode='markers', name='Segnato',
            marker=dict(color='green', size=8, symbol='circle', opacity=0.8)
        ))
        
        # Aggiungo i tiri sbagliati (X rosse)
        fig_court.add_trace(go.Scatter(
            x=df_miss['loc_x'], y=df_miss['loc_y'], mode='markers', name='Sbagliato',
            marker=dict(color='red', size=8, symbol='x', opacity=0.8)
        ))

        # Disegno il campo
        fig_court = draw_fiba_half_court(fig_court)
        
        # Aggiorno i range per adattarli perfettamente al campo da -7.5 a +7.5 (asse X) e da 0 a 14 (asse Y)
        # Lascio un margine (es: X da -8 a 8, Y da -0.5 a 14.5) per non tagliare le linee esterne
        fig_court.update_layout(
            xaxis=dict(range=[-8, 8], showgrid=False, zeroline=False, visible=False),
            yaxis=dict(range=[-0.5, 14.5], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
            width=600, height=550, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        # st.plotly_chart con theme=None impedisce a Streamlit di scurire il background
        st.plotly_chart(fig_court, use_container_width=True, theme=None)

# ==========================================
# GESTIONE NAVIGAZIONE (Main)
# ==========================================
def main():
    teams_data, shots_data = get_mock_data()
    model = train_mock_predictor()
    
    st.sidebar.title("Navigazione")
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/f/f1/EuroLeague_logo.svg/320px-EuroLeague_logo.svg.png", width=150)
    pagina = st.sidebar.radio("Vai a:", ["1. Introduzione", "2. Match Predictor", "3. Player Analytics"])
    
    if pagina == "1. Introduzione":
        page_intro(teams_data)
    elif pagina == "2. Match Predictor":
        page_predictor(teams_data, model)
    elif pagina == "3. Player Analytics":
        page_player(shots_data)
        
if __name__ == "__main__":
    main()