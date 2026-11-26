import pandas as pd
from sklearn.preprocessing import RobustScaler #using it to avoid outlier from the top players
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

def prepare_player_features(df_players):
    
    #preparing players data, clean the noise, select the metrics and robust scaling against outlier
    df_ml = df_players.copy()

    #anti noise filter, only players with a significant amount of minutes or games played
    df_ml = df_ml[df_ml['gamesPlayed'] > 4]

    df_ml = df_ml.set_index(['player.code', 'season'])

    #features selection, key metricsßßßßß
    features = [
        'assists',
        'turnoversRatio',
        'assistsRatio',                                
        'reboundsPercentage',                
        'blocks',                            
        'steals',                                               
        'pointsFromThreePointersPercentage', 
        'freeThrowsRate',
        'pointsScored' 
    ]

    pct_cols= ['pointsFromThreePointersPercentage', 'freeThrowsRate', 'assistsRatio', 'turnoversRatio', 'reboundsPercentage']

    for col in pct_cols:
        df_ml[col] = pd.to_numeric(
            df_ml[col].astype(str).str.replace('%', ''),
            errors='coerce').fillna(0)

    df_ml[features] = df_ml[features].fillna(0)

    #applciation of the scaler
    scaler = RobustScaler()

    scaled_array = scaler.fit_transform(df_ml[features])

    df_scaled = pd.DataFrame(scaled_array, columns = features, index = df_ml.index)
    #adding weight to the points scored to separate 3 and d or playmaker from scorer
    df_scaled['pointsScored'] = df_scaled['pointsScored']  * 1.3                                                                                                                                                                                                                                                                           

    return df_ml, df_scaled

def apply_pca(df_scaled, n_components = 3):
    #PCA to reduce feature dimensionality mantaining max variance as possible

    #initialize pca object with the desired number of componentns
    pca = PCA(n_components = n_components)

    #using fit transforem on the scaled df
    pca_array = pca.fit_transform(df_scaled)

    #columns names 
    pca_columns = ['PC1', 'PC2', 'PC3']

    df_pca = pd.DataFrame(pca_array, columns = pca_columns, index=df_scaled.index)

    total_variance = pca.explained_variance_ratio_.sum()*100

    print(f'Total variance explained by PCA model: {total_variance:.2f}%')

    return df_pca

def cluster_player_archetype(df_pca, df_ml, n_clusters=4):

    #initialize kmeans model owith fixed random state to not re-initialize the clusters everytime

    kmeans = KMeans(n_clusters=n_clusters, random_state=12, n_init=20)

    #usning filter predict to find the groups with the PCA coord
    clusters = kmeans.fit_predict(df_pca)

    #add the numerical cluster ID to the cleaned df
    df_ml['Cluster_ID'] = clusters

    #profilign by centroids
    numeric_features = [
        'pointsScored', 'assistsRatio', 'reboundsPercentage',
        'blocks', 'steals', 'turnoversRatio',
        'pointsFromThreePointersPercentage', 'freeThrowsRate', 'assists'
    ]

    #finding the clusters ID based on the mean
    cluster_means = df_ml.groupby('Cluster_ID')[numeric_features].mean()

    #normalize the cluster mean
    means_norm = (cluster_means -cluster_means.mean())/ cluster_means.std()
    all_clusters = list(range(n_clusters))

    #rim protector cluster identification (reboubnds + pblocks)
    rim_score = means_norm['reboundsPercentage'] + means_norm['blocks']
    rim_protector_cluster = rim_score.idxmax()

    #playmaker identification (lot of assit and risk of turnovers)
    remain_cl = [c for c in all_clusters if c!=rim_protector_cluster]
    pm_scores = (
        means_norm.loc[remain_cl, 'assists']+ 
        means_norm.loc[remain_cl, 'assistsRatio'] -
        (0.3* means_norm.loc[remain_cl, 'reboundsPercentage'])
    )
    pm_cluster = pm_scores.idxmax()

    #scorer identification (points scored and free throw rate high)
    remain_cl = [c for c in remain_cl if c != pm_cluster]
    scorer = means_norm.loc[remain_cl, 'pointsScored'] + (0.25*means_norm.loc[remain_cl, 'freeThrowsRate'])
    scorer_cluster = scorer.idxmax()

    #last the 3 and D cluster
    three_and_D_cluster = [c for c in remain_cl if c!=scorer_cluster][0]

    archetype_dict = {
        pm_cluster: 'Playmaker',
        rim_protector_cluster: 'Rim protector',
        scorer_cluster: 'Scorer',
        three_and_D_cluster: '3 and D'
    }

    df_ml['archetype'] = df_ml['Cluster_ID'].map(archetype_dict)

    return df_ml

def get_player_arctype(df_players_raw,target_season, n_clusters=4):
    """"
    master func, execute in sequence, scaling, pca and k means with profiling
    """

    #clean, filter and scale 
    df_ml, df_scaled = prepare_player_features(df_players_raw)

    #pca 
    df_pca = apply_pca(df_scaled, n_components=3)

    #K means cluster
    df_final = cluster_player_archetype(df_pca, df_ml, n_clusters=n_clusters)

    #extract the selected season and put back player.code as single index
    df_season = df_final.reset_index()
    df_season = df_season[df_season['season']== target_season].set_index('player.code')

    return df_season