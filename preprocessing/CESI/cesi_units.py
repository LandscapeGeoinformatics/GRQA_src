# Import the libraries
import os
import pandas as pd

# Name of the dataset
ds_name = 'CESI'

# Raw directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
raw_dir = os.path.join(proj_dir, 'data', ds_name, 'raw')

# Download directory
dl_dir = os.path.join(raw_dir, 'download_2020-11-16')

# Import parameters and units from observation data
obs_file = os.path.join(raw_dir, dl_dir, 'wqi-federal-raw-data-2020-iqe-donnees-brutes-fed.csv')
obs_dtypes = {
    'VARIABLE_NAME': object,
    'FORM_NAME': object,
    'UNIT_UNITE': object
}
obs_df = pd.read_csv(obs_file, sep=',', usecols=obs_dtypes.keys(), dtype=obs_dtypes, encoding='latin-1')

# Create DF of units
unit_df = obs_df.groupby(['VARIABLE_NAME', 'FORM_NAME'])['UNIT_UNITE'].value_counts().reset_index(name='count')

# Export to CSV
unit_df.to_csv(os.path.join(raw_dir, 'meta', ds_name + '_units.csv'), sep=';', index=False, encoding='utf-8')
