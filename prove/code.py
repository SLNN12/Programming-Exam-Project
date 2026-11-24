def cluster_player_archetype(df_pca, df_ml, n_clusters=4):
    kmeans = KMeans(n_clusters=n_clusters, random_state=12)
    df_ml['Cluster_ID'] = kmeans.fit_predict(df_pca)

    # Aggiungiamo 'assists' anche alle medie dei centroidi
    numeric_features = [
        'pointsScored', 'assists', 'assistsRatio', 'reboundsPercentage',
        'blocks', 'steals', 'turnoversRatio',
        'pointsFromThreePointersPercentage', 'freeThrowsRate'
    ]
    cluster_means = df_ml.groupby('Cluster_ID')[numeric_features].mean()

    # Standardizzazione Z-score blindata contro eventuali divisioni per zero
    means_norm = ((cluster_means - cluster_means.mean()) / cluster_means.std()).fillna(0)
    all_clusters = list(range(n_clusters))

    # 1. Rim Protector: rimbalzi + stoppate
    rim_score = means_norm['reboundsPercentage'] + means_norm['blocks']
    rim_protector_cluster = rim_score.idxmax()

    # 2. Playmaker: volume assist + assistsRatio, penalizzando leggermente i rimbalzi per escludere le ali
    remain_cl = [c for c in all_clusters if c != rim_protector_cluster]
    pm_scores = (
        means_norm.loc[remain_cl, ___] +                  # INDIZIO 2: usa 'assists' (il volume a partita)
        means_norm.loc[remain_cl, 'assistsRatio'] -
        (0.3 * means_norm.loc[remain_cl, 'reboundsPercentage'])
    )
    pm_cluster = pm_scores.idxmax()

    # 3. Scorer: punti segnati + capacità di guadagnare tiri liberi
    remain_cl = [c for c in ___ if c != pm_cluster]       # INDIZIO 3: filtra da remain_cl (non da all_clusters)
    scorer = means_norm.loc[remain_cl, 'pointsScored'] + (0.5 * means_norm.loc[remain_cl, 'freeThrowsRate'])
    scorer_cluster = scorer.idxmax()

    # 4. 3 and D: l'unico cluster rimasto (tiratori perimetrali + difesa + basso utilizzo)
    three_and_D_cluster = [c for c in ___ if c != scorer_cluster][0]  # INDIZIO 4: prendi l'ultimo da remain_cl

    archetype_dict = {
        pm_cluster: 'Playmaker',
        rim_protector_cluster: 'Rim protector',
        scorer_cluster: 'Scorer',
        three_and_D_cluster: '3 and D'
    }

    df_ml['archetype'] = df_ml['Cluster_ID'].map(archetype_dict)

    return df_ml