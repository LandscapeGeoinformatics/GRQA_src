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
    min_year = 2021
    max_year = 0
    obs_reader = pd.read_csv(obs_file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, encoding='utf-8', chunksize=100000)
    for obs_chunk in obs_reader:
        id_set = set(obs_chunk['site_id'])
        site_ids.update(id_set)
        obs_count += len(obs_chunk['obs_value'])
        if param_name is None:
            param_name = obs_chunk['param_name'].mode()[0]
            unit = obs_chunk['unit'].mode()[0]
        chunk_median = obs_chunk['obs_value'].median()
        medians.append(chunk_median)
        obs_chunk['year'] = pd.to_datetime(obs_df['obs_date'], errors='coerce').dt.year
        if obs_chunk['year'].min() < min_year:
			min_year = obs_chunk['year'].min()
		if obs_chunk['year'].max() > max_year:
			max_year = obs_chunk['year'].max()
    site_count = len(site_ids)
    median = np.round(np.mean(medians), 3)
    row = (param_code, param_name, unit, site_count, obs_count, median, '{} - {}'.format(min_year, max_year))
    rows.append(row)

# Create and export DF with statistics
stats_df = pd.DataFrame(
    rows, columns=['Parameter code', 'Parameter name', 'Unit', 'Sites', 'Observations', 'Median value', 'Timeframe']
)
stats_df.sort_values(by=['Parameter code'], key=lambda col: col.str.lower(), ascending=True, inplace=True)
stats_df.to_csv(os.path.join(meta_dir, ds_name + '_param_stats_time.csv'), sep=';', index=False, encoding='utf-8')
