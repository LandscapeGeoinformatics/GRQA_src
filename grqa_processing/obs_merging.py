# Import the libraries
import sys
import os
import glob

import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
from sklearn.cluster import DBSCAN
from sklearn.metrics import mean_squared_error
from math import sqrt

# Dataset names
ds_names = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']

# Project directory
proj_dir = sys.argv[1]

# Get parameter code
param_code = sys.argv[2]

# Metadata directory
meta_dir  = os.path.join(proj_dir, 'final', 'GRQA_meta')

# Data directory
data_dir  = os.path.join(proj_dir, 'final', 'GRQA_data')

# Create dictionary with observation files to be merged
file_dict = {}
for ds in ds_names:
    proc_dir = os.path.join(
        proj_dir, 'working', 'GRQA_source_data', ds, 'processed'
    )
    obs_files = os.listdir(proc_dir)
    obs_files = glob.glob(os.path.join(proc_dir, param_code + '_*.csv'))
    for obs_file in obs_files:
        param_code = os.path.basename(obs_file).split('_')[0]
        if param_code not in file_dict.keys():
            file_dict[param_code] = [obs_file]
        else:
            file_dict[param_code].append(obs_file)

# Merge and export observation files
for param_code in list(file_dict.keys()):
    obs_dfs = []
    obs_files = file_dict[param_code]
    for obs_file in obs_files:
        obs_df = pd.read_csv(obs_file, sep=';', dtype=object, encoding='utf-8', low_memory=False)
        obs_df['lat_wgs84'] = obs_df['lat_wgs84'].astype(np.float64)
        obs_df['lon_wgs84'] = obs_df['lon_wgs84'].astype(np.float64)
        obs_df['obs_value'] = obs_df['obs_value'].astype(np.float64)
        obs_dfs.append(obs_df)
    merged_df = pd.concat(obs_dfs)
    merged_df.drop_duplicates(inplace=True)
    merged_df.reset_index(drop=True, inplace=True)

    # Calculate percentile of observation value
    merged_df['obs_percentile'] = merged_df['obs_value'].rank(pct=True)

    # Flag outliers according to the IQR test
    q1 = merged_df['obs_value'].quantile(0.25)
    q3 = merged_df['obs_value'].quantile(0.75)
    iqr = q3 - q1
    lower_limit = q1 - (1.5 * iqr)
    upper_limit = q3 + (1.5 * iqr)
    merged_df['obs_iqr_outlier'] = 'no'
    merged_df.loc[merged_df['obs_value'] <= lower_limit, 'obs_iqr_outlier'] = 'yes'
    merged_df.loc[merged_df['obs_value'] >= upper_limit, 'obs_iqr_outlier'] = 'yes'

    # Convert date to datetime for availability and continuity calculation
    merged_df['obs_date'] = pd.to_datetime(merged_df['obs_date'], errors='coerce')

    # Calculate the monthly availability of as the ratio between number of months with at least one observation and
    # the total number of months a particular site had any observations
    avail_df = merged_df[['site_id', 'obs_date', 'obs_value']]
    avail_df['obs_ym'] = pd.to_datetime(avail_df['obs_date'], errors='coerce').dt.strftime('%Y-%m')
    group_df = avail_df.groupby('site_id')['obs_ym'].nunique().reset_index() \
        .rename(columns={'obs_ym': 'months_with_obs'})
    avail_df = avail_df.groupby('site_id').agg(min_date=('obs_date', 'min'),
                                                 max_date=('obs_date', 'max')).reset_index()
    avail_df['ts_len_months'] = avail_df.apply(
        lambda row: (
            relativedelta(row['max_date'], row['min_date']).years * 12 + 
            relativedelta(row['max_date'], row['min_date']).months
        ),
        axis=1
    )
    avail_df = avail_df.merge(group_df, on='site_id')
    avail_df['site_ts_availability'] = np.round(avail_df['months_with_obs'] / avail_df['ts_len_months'], 2)
    avail_df.loc[avail_df['site_ts_availability'] > 1, 'site_ts_availability'] = 1
    avail_df.drop(columns=['min_date', 'max_date', 'ts_len_months', 'months_with_obs'], inplace=True)

    # Calculate the monthly continuity as the ratio between the longest period of consecutive months with any
    # measurements and the length of time series in months
    cont_df = merged_df[['site_id', 'obs_date', 'obs_value']]
    cont_df = (
        cont_df.set_index('obs_date')
        .groupby('site_id')
        .resample('ME')
        .count()
        .drop('site_id', axis=1)
        .reset_index()
    )
    cont_df['month_has_obs'] = np.where(cont_df['obs_value'] > 0, True, False)
    group_ids = cont_df['month_has_obs'].diff().ne(0).cumsum()
    cont_df['count'] = cont_df['month_has_obs'].groupby([cont_df['site_id'], group_ids]).cumsum()
    cont_df = cont_df.groupby('site_id').agg(max=('count', 'max'), total=('count', 'count')).reset_index()
    cont_df['site_ts_continuity'] = round(cont_df['max'] / cont_df['total'], 2)
    cont_df.loc[cont_df['site_ts_continuity'] > 1, 'site_ts_continuity'] = 1
    cont_df.drop(columns=['max', 'total'], inplace=True)

    # Merge availability and continuity DFs with merged_df
    merged_df = merged_df.merge(avail_df, how='left', on='site_id')
    merged_df = merged_df.merge(cont_df, how='left', on='site_id')

    # Duplicate treatment

    # Create clusters of site IDs that are within 1 km of each other
    site_df = merged_df[['site_id', 'lat_wgs84', 'lon_wgs84']]
    site_df.drop_duplicates(inplace=True)
    site_ids = site_df[['site_id']].values
    coords = site_df[['lat_wgs84', 'lon_wgs84']].values
    kms_per_radian = 6371.0088
    epsilon = 1 / kms_per_radian
    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine', n_jobs=-1).fit(np.radians(coords))
    cluster_labels = db.labels_.tolist()

    # List of all possible site ID pairs in clusters
    site_ids = [id for id_list in site_ids.tolist() for id in id_list]
    cluster_df = pd.DataFrame(list(zip(site_ids, cluster_labels)), columns=['site_id', 'cluster_label'])
    cluster_df = cluster_df.groupby('cluster_label')['site_id'].apply(list).reset_index()
    id_pairs = []
    for id_pair in cluster_df['site_id'].tolist():
        if len(id_pair) > 1:
            id_pairs.append(id_pair)

    # Set of unique site ID pairs
    id_set = set()
    for id_pair in id_pairs:
        for id1 in id_pair:
            for id2 in id_pair:
                if id1 != id2:
                    id_tuple = (id1, id2)
                    id_tuple = tuple(sorted(id_tuple))
                    id_set.add(id_tuple)

    # Calculate root mean square error of pairs where IDs are from different sources
    rms_dfs = []
    for id_tup in id_set:
        id1 = id_tup[0]
        id2 = id_tup[1]
        source1 = merged_df.loc[merged_df['site_id'] == id1, 'source'].iloc[0]
        source2 = merged_df.loc[merged_df['site_id'] == id2, 'source'].iloc[0]
        if source1 != source2:
            df1 = merged_df[merged_df['site_id'] == id1]
            df2 = merged_df[merged_df['site_id'] == id2]
            rms_df = pd.merge(df1, df2, how='inner', on='obs_date', suffixes=['_1', '_2'])
            rms_df = rms_df.dropna(subset=['obs_value_1'])
            rms_df = rms_df.dropna(subset=['obs_value_2'])
            if len(rms_df) > 0:
                rms_df['obs_value_1'] = rms_df['obs_value_1'].astype(np.float64)
                rms_df['obs_value_2'] = rms_df['obs_value_2'].astype(np.float64)
                rms = sqrt(mean_squared_error(rms_df['obs_value_1'], rms_df['obs_value_2']))
                # Calculate number of matching dates for each pair and append DF to list
                if rms == 0:
                    rms_df['date_match_count'] = len(rms_df)
                    rms_df = rms_df[
                        ['obs_id_1', 'lat_wgs84_1', 'lon_wgs84_1', 'site_id_1', 'site_name_1', 'obs_value_1',
                         'source_1', 'site_ts_availability_1', 'site_ts_continuity_1', 'obs_date',
                         'obs_id_2', 'lat_wgs84_2', 'lon_wgs84_2', 'site_id_2', 'site_name_2', 'obs_value_2',
                         'source_2', 'site_ts_availability_2', 'site_ts_continuity_2', 'date_match_count']
                    ]
                    rms_dfs.append(rms_df)
    # Export DFs to CSV
    if len(rms_dfs) > 0:
        rms_df = pd.concat(rms_dfs)
        rms_df.reset_index(drop=True, inplace=True)
        rms_df['param_code'] = param_code
        rms_df.to_csv(
            os.path.join(meta_dir, param_code + '_' + 'GRQA' + '_dup_obs.csv'),
            sep=';', index=False, encoding='utf-8'
        )
    cols = []
    meta_cols = []
    for col in merged_df.columns:
        if 'meta' not in col:
            cols.append(col)
        else:
            meta_cols.append(col)
    cols.extend(meta_cols)
    merged_df = merged_df.reindex(columns=cols)
    merged_df.to_csv(
        os.path.join(data_dir, param_code + '_' + 'GRQA.csv'), sep=';', index=False,
        encoding='utf-8'
    )
