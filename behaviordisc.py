"""
- changepoint detetction using sliding window and ks-test
- decomposition of univariate ts
- clustering of subsequences
"""
import matplotlib.pyplot as plt
import ruptures as rpt
import pandas as pd
import numpy as np


def cp_detection_binary_segmentation(points):
    # Changepoint detection with the Binary Segmentation search method
    model = "l2"
    algo = rpt.Binseg(model=model).fit(points)
    my_bkps = algo.predict(n_bkps=2)
    # show results
    rpt.show.display(points, my_bkps, figsize=(10, 6))
    plt.title('Change Point Detection: Binary Segmentation Search Method')
    plt.show()
    return my_bkps


def cp_detection_KSWIN(points, period=None, seperate_plot=False):
    # Kolmogorov-Smirnov test
    from skmultiflow.drift_detection import KSWIN
    window_size, stat_size = get_windows_size(period)
    kswin = KSWIN(alpha=0.01, window_size=window_size, stat_size=stat_size)
    # Store detection
    detections = []
    p_values = {}
    # Process stream via KSWIN and print detections
    for i in range(len(points)):
        batch = points[i]
        kswin.add_element(batch)
        if kswin.detected_change():
            print("\rIteration {}".format(i))
            print("\r KSWINReject Null Hyptheses")
            detections.append(i)
            p_values[i] = kswin.p_value
    print("Number of detections: " + str(len(detections)))
    if seperate_plot:
        rpt.show.display(points, detections, figsize=(10, 6))
        plt.title('Change Point Detection: Kolmogorov-Smirnov Windowing')
        plt.show()
    return detections


def cp_detection_ADWIN(points):
    from skmultiflow.drift_detection.adwin import ADWIN
    adwin = ADWIN()
    detections = []
    # Adding stream elements to ADWIN and verifying if drift occurred
    for i in range(len(points)):
        adwin.add_element(points[i])
        if adwin.detected_change():
            detections.append(i)
            print('Change detected in data: ' + str(points[i]) + ' - at index: ' + str(i))
    rpt.show.display(points, detections, figsize=(10, 6))
    plt.title('Change Point Detection: ADWIN')
    plt.show()


def decompostion_STL(series, period=None, title=''):
    from statsmodels.tsa.seasonal import STL

    stl = STL(series, period=period, robust=True)
    res_robust = stl.fit()
    fig = res_robust.plot()
    fig.text(0.1, 0.95, title, size=15, color='purple')
    plt.show()


def get_windows_size(period):
    # one of ['1H', '8H', '1D', '7D']
    # set windows size two two weeks depending on log, stat size one week
    if period == '1H':
        window_size = 2 * 168
        stat_size = 168
    elif period == '8H':
        window_size = 2 * 21
        stat_size = 21
    elif period == '1D':
        window_size = 2 * 7
        stat_size = 7
    elif period == '7D':
        window_size = 8
        stat_size = 4
    else:
        window_size = 100
        stat_size = 40

    return window_size, stat_size


def subseqeuence_clustering(sequence, changepoints, y_label='y', norm=False):
    """
    Clusters subsequences of time series indicated by the changepoints variable.
    Uses silhouette score to determine the number of clusters
    :param y_label: Name of y-label in plot
    :param norm: normlise data using MinMaxScaler
    :param sequence: np array of the time series
    :param changepoints: detected changepoints on which subseuqences are build
    :return:
    """
    from tslearn.clustering import TimeSeriesKMeans, silhouette_score
    from tslearn.utils import to_time_series_dataset
    from tslearn.preprocessing import TimeSeriesScalerMinMax

    sub_ids = []
    x_index = []
    X = []
    i = 0
    end_p = [len(sequence) - 1]
    for cp in changepoints + end_p:
        X.append(sequence[i:cp])
        index = 'sub_' + str(i) + '_' + str(cp)
        sub_ids.append(index)
        x_index.append([x_id for x_id in range(i, cp + 1)])
        i = cp

    # Normalize the data (y = (x - min) / (max - min))
    if norm:
        X = TimeSeriesScalerMinMax().fit_transform(X)
    X = to_time_series_dataset(X)
    #  Find optimal # clusters by
    #  looping through different configurations for # of clusters and store the respective values for silhouette:
    sil_scores = {}
    for n in range(2, len(changepoints)):
        model_tst = TimeSeriesKMeans(n_clusters=n, metric="dtw", n_init=10)
        model_tst.fit(X)
        sil_scores[n] = (silhouette_score(X, model_tst.predict(X), metric="dtw"))

    opt_k = max(sil_scores, key=sil_scores.get)
    print('Number of Clusters in subsequence clustering: ' + str(opt_k))
    model = TimeSeriesKMeans(n_clusters=opt_k, metric="dtw", n_init=10)
    labels = model.fit_predict(X)
    print(labels)

    # build helper df to map metrics to their cluster labels
    df_cluster = pd.DataFrame(list(zip(sub_ids, x_index, model.labels_)), columns=['metric', 'x_index', 'cluster'])
    cluster_metrics_dict = df_cluster.groupby(['cluster'])['metric'].apply(lambda x: [x for x in x]).to_dict()

    print('Plotting Clusters')
    #  plot changepoints as vertical lines
    for cp in changepoints:
        plt.axvline(x=cp, ls=':', lw=2, c='0.65')
    #  preprocessing for plotting cluster based
    x_scat = []
    y_scat = []
    cluster = []
    for index, row in df_cluster.iterrows():
        x_seq = row['x_index']
        x_scat.extend(x_seq)
        y_seq = sequence[x_seq[0]:x_seq[-1] + 1]
        y_scat.extend(y_seq)
        label_seq = [row['cluster']]
        cluster.extend(label_seq * len(x_seq))
        # plt.scatter(x_seq, y_seq, label=label_seq)
    # plotting cluster based
    x_scat = np.array(x_scat)
    y_scat = np.array(y_scat)
    for c in np.unique(cluster):
        i = np.where(cluster == c)
        plt.scatter(x_scat[i], y_scat[i], label=c)
    plt.legend()
    plt.title('Subsequence k-means Clustering')
    plt.xlabel('Time index')
    plt.ylabel(y_label)
    plt.show()

    return cluster_metrics_dict