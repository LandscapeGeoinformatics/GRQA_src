# Import the libraries
import os
import glob
import pandas as pd

# Name of the dataset
ds_name = 'GEMSTAT'

# Raw directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
raw_dir = os.path.join(proj_dir, 'data', ds_name, 'raw')

# List of observation files
obs_files = glob.glob(os.path.join(raw_dir, '*.csv'))

# Import observation data and create DF of units
obs_dtypes = {
    'Parameter Code': object,
    'Unit': object
}
unit_dfs = []
for file in obs_files:
    obs_df = pd.read_csv(file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, encoding='latin-1')
    unit_df = obs_df.groupby(['Parameter Code'])['Unit'].value_counts().reset_index(name='count')
    unit_dfs.append(unit_df)
unit_df = pd.concat(unit_dfs)

# Import parameter metadata
meta_file = os.path.join(raw_dir, 'data_request.xls')
param_dtypes = {
    'Parameter Code': object,
    'Parameter Long Name': object
}
param_df = pd.read_excel(meta_file, sheet_name='Parameter_Metadata', usecols=param_dtypes.keys(), dtype=param_dtypes)

# Merge the DFs and export to CSV
unit_df = unit_df.merge(param_df, on='Parameter Code')
unit_df.to_csv(os.path.join(raw_dir, 'meta', ds_name + '_units.csv'), sep=';', index=False, encoding='utf-8')
