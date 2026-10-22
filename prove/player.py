import streamlit as st
import pandas as pd
from euroleague_api.player_stats import PlayerStats

# 1. Configurazione della Pagina Streamlit
st.set_page_config(page_title="EuroLeague Player Profiles", layout="wide")
st.title("EuroLeague Player Profiles")

# 2. Funzione per scaricare i dati e metterli in cache
@st.cache_data
def load_player_data(season):
    """
    Scarica la classifica dei leader per Valutazione (PIR)
    dalla stagione selezionata.
    """
    player_api = PlayerStats("E")
    
    # "Valuation" è la dicitura per il PIR
    df = player_api.get_player_stats_leaders_single_season(
        season=season,
        stat_category="Score", 
        statistic_mode="PerGame"
    )
    return df

with st.spinner("Downloading EuroLeague Data..."):
    df_leaders = load_player_data(2026)

# ---------------------------------------------------------
# NORMALIZZAZIONE DINAMICA DELLE COLONNE
# Mappiamo i nomi esatti rivelati dal traceback precedente
# ---------------------------------------------------------

# Per il menu a tendina e i titoli usiamo il nome completo o abbreviato (non il codice)
if 'playerName' in df_leaders.columns:
    col_player = 'playerName'
elif 'playerAbbreviatedName' in df_leaders.columns:
    col_player = 'playerAbbreviatedName'
else:
    col_player = 'playerCode' # Fallback estremo

col_image = 'imageUrl' if 'imageUrl' in df_leaders.columns else None
col_valuation = 'averagePerGame' if 'averagePerGame' in df_leaders.columns else 'total'
col_games = 'gamesPlayed' if 'gamesPlayed' in df_leaders.columns else None

# Per le squadre, l'API restituisce solitamente 'clubCodes' o 'clubNames'
if 'clubNames' in df_leaders.columns:
    col_team = 'clubNames'
elif 'clubCodes' in df_leaders.columns:
    col_team = 'clubCodes'
else:
    col_team = None

# ==========================================
# ESEMPIO 1: Profilo Individuale con Foto
# ==========================================
st.subheader("1. Profilo Giocatore Singolo")

# Creiamo una tendina con i nomi formattati dei giocatori
selected_player = st.selectbox(
    "Cerca e seleziona un giocatore:", 
    df_leaders[col_player].unique()
)

# Filtriamo il dataframe per il giocatore selezionato
player_data = df_leaders[df_leaders[col_player] == selected_player].iloc[0]

# Prepariamo tre colonne per un layout pulito
col_img, col_stat1, col_stat2 = st.columns([1, 1, 1])

with col_img:
    if col_image and pd.notna(player_data[col_image]):
        st.image(player_data[col_image], width=200, caption=selected_player)
    else:
        st.warning("Foto non disponibile")

with col_stat1:
    st.metric(label="Media punti per partita", value=round(float(player_data[col_valuation]), 1))
    
    # Gestione delle squadre (nel caso siano liste o NaN)
    if col_team:
        team_val = player_data[col_team]
        if isinstance(team_val, list):
            team_val = team_val[0] if len(team_val) > 0 else "N/A"
        elif pd.isna(team_val):
            team_val = "N/A"
        st.metric(label="Squadra", value=team_val)

with col_stat2:
    if col_games:
        st.metric(label="Partite Giocate", value=int(player_data[col_games]))

st.markdown("---")

# ==========================================
# ESEMPIO 2: Tabella Classifica con Foto Integrate
# ==========================================
st.subheader("2. Classifica Top 10 Giocatori per Punti/Partita")

# Selezioniamo le colonne da mostrare
cols_to_show = [c for c in [col_image, col_player, col_team, col_valuation, col_games] if c is not None and c in df_leaders.columns]
df_top10 = df_leaders[cols_to_show].head(10).copy()

# Assicuriamoci che la colonna Valuation sia numerica e arrotondata a 2 decimali
df_top10[col_valuation] = pd.to_numeric(df_top10[col_valuation], errors='coerce').round(2)

# Se le squadre sono contenute in liste (es. ['RMB']), estraiamo il primo elemento
if col_team:
    df_top10[col_team] = df_top10[col_team].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)

# Convertiamo gli URL immagine in tag HTML per la visualizzazione tabellare
if col_image:
    df_top10['Foto'] = df_top10[col_image].apply(
        lambda url: f'<img src="{url}" width="50" style="border-radius: 5px;">' if pd.notna(url) else ''
    )
    # Riorganizziamo le colonne
    cols_order = ['Foto', col_player, col_team, col_valuation, col_games]
    df_top10 = df_top10[[c for c in cols_order if c in df_top10.columns]]

df_top10 = df_top10.rename(columns={
    col_player: "Giocatore",
    col_team: "Squadra",
    col_valuation: "Punti/Partita",
    col_games: "Partite Giocate"
})

# Mostriamo la tabella tramite st.write e l'HTML rendering abilitato
st.write(
    df_top10.to_html(escape=False, index=False), 
    unsafe_allow_html=True
)

st.markdown("---")

# ==========================================
# ESEMPIO 3: Griglia di Immagini (Grid Layout)
# ==========================================
st.subheader("3. Griglia dei Top 5 Giocatori")

top5 = df_leaders.head(5)
cols_grid = st.columns(5)

for index, (col, row) in enumerate(zip(cols_grid, top5.iterrows())):
    player_info = row[1]
    with col:
        if col_image and pd.notna(player_info[col_image]):
            st.image(player_info[col_image], use_container_width=True)
        st.markdown(f"**{index + 1}. {player_info[col_player]}**")
        st.write(f"PIR: **{round(float(player_info[col_valuation]), 1)}**")