# Import the libraries
import os
import pandas as pd
import numpy as np
import glob

# Name of the dataset
ds_name = 'GRQA'

# Directory paths
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
data_dir = os.path.join(proj_dir, 'data', ds_name, 'data')
meta_dir = os.path.join(proj_dir, 'data', ds_name, 'meta')

# Read observation data and collect statistics
obs_dtypes = {
    'obs_id': object,
    'site_id': object,
    'lat_wgs84': np.float64,
    'lon_wgs84': np.float64,
    'obs_date': object,
    'obs_value': np.float64,
    'param_name': object,
    'unit': object,
    'obs_iqr_outlier': object,
    'site_ts_availability': np.float64,
    'site_ts_continuity': np.float64,
    'source': object
}
obs_files = glob.glob(os.path.join(data_dir, '*.csv'))
rows = []
for obs_file in obs_files:
    obs_count = 0
    site_ids = set()
    param_code = os.path.basename(obs_file).rpartition('_')[0]
    param_name = None
    unit = None
    medians = []
    min_years = []
    max_years = []
    outlier_count = 0
    obs_reader = pd.read_csv(obs_file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, encoding='utf-8', chunksize=10000)
    for obs_chunk in obs_reader:
        id_set = set(obs_chunk['site_id'])
        site_ids.update(id_set)
        obs_count += obs_chunk['obs_id'].nunique()
        if param_name is None:
            param_name = obs_chunk['param_name'].mode()[0]
            unit = obs_chunk['unit'].mode()[0]
        chunk_median = obs_chunk['obs_value'].median()
        medians.append(chunk_median)
        obs_chunk['year'] = pd.to_datetime(obs_chunk['obs_date'], errors='coerce').dt.year
        min_years.append(obs_chunk['year'].min())
        max_years.append(obs_chunk['year'].max())
        outlier_count += len(obs_chunk[obs_chunk['obs_iqr_outlier'] == 'yes'])
    site_count = len(site_ids)
    median = np.round(np.mean(medians), 3)
    min_year = np.min(min_years)
    max_year = np.max(max_years)
    outlier_perc = np.round(outlier_count / obs_count * 100, 1)
    row = (param_code, param_name, site_count, obs_count, median, unit, min_year, max_year, outlier_perc)
    rows.append(row)

# Create and export DF with statistics
stats_df = pd.DataFrame(
    rows, columns=['Parameter code', 'Parameter name', 'Sites', 'Observations', 'Median value', 'Unit', 'Start year', 'End year', 'Outlier %']
)
stats_df.sort_values(by=['Parameter code'], key=lambda col: col.str.lower(), ascending=True, inplace=True)
stats_df.to_csv(os.path.join(meta_dir, ds_name + '_param_stats.csv'), sep=';', index=False, encoding='utf-8')
