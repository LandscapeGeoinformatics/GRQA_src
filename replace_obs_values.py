# Script for replacing NO3N, NO2N and NH4N concentrations of GLORICH sites in GRQA

# Import libraries
import sys
import os

import numpy as np
import pandas as pd


# Get new conversion constant
def get_new_constant(param: object) -> float:
    new_constants = {
        'NO3N': 0.014007,
        'NO2N': 0.014007,
        'NH4N': 0.014007
    }
    return new_constants.get(param)


# Parameter
param = sys.argv[1]

# New constant
new_constant = get_new_constant(param)

# Data type dictionary for observation files
obs_dtypes = {
    'obs_id': object,
    'lat_wgs84': np.float64,
    'lon_wgs84': np.float64,
    'obs_date': object,
    'obs_time': object,
    'obs_time_zone': object,
    'site_id': object,
    'site_name': object,
    'site_country': object,
    'param_code': object,
    'source_param_code': object,
    'param_name': object,
    'source_param_name': object,
    'obs_value': np.float64,
    'source_obs_value': np.float64,
    'param_form': object,
    'source_param_form': object,
    'unit': object,
    'source_unit': object,
    'filtration': object,
    'source': object
}

# Replace GLORICH observation values based on the new constant
in_file = f'D:/GRQA_v1.1/{param}_GRQA.csv'
obs_reader = pd.read_csv(in_file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000)

out_file = f'D:/GRQA_v1.2/GRQA_data_v1.2/{param}_GRQA.csv'
try:
    os.remove(out_file)
except OSError:
    pass

for obs_chunk in obs_reader:
    obs_chunk.loc[obs_chunk['source'] == 'GLORICH', 'obs_value'] = obs_chunk['source_obs_value'] * new_constant
    obs_chunk.to_csv(out_file, sep=';', index=False, header=not os.path.exists(out_file), mode='a')

# Check the number of rows and missing values
for file in [in_file, out_file]:
    rows = 0
    missing = 0
    obs_sum = 0
    obs_count = 0
    obs_reader = pd.read_csv(file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000)
    for obs_chunk in obs_reader:
        rows += len(obs_chunk)
        missing += obs_chunk['obs_value'].isna().sum()
        condition = (obs_chunk['source'] == 'GLORICH') & (obs_chunk['site_country'] == 'Germany')
        obs_sum += obs_chunk[condition]['obs_value'].sum()
        obs_count += obs_chunk[condition]['obs_value'].count()
    obs_mean = obs_sum / obs_count
    print(f'Rows in {file}: {rows}')
    print(f'Missing values in {file}: {missing}')
    print(f'Mean GLORICH concentration in {file}: {obs_mean}')
