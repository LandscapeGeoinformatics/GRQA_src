# Import the libraries
import sys
import os
import glob

import pandas as pd

# Name of the dataset
ds_name = 'GEMSTAT'

# Raw directory
raw_dir = sys.argv[1]

# List of observation files
obs_files = glob.glob(os.path.join(raw_dir, 'GFQA_v2/*.csv'))

# Import observation data and create DF of units
obs_dtypes = {
    'Parameter.Code': object,
    'Unit': object
}
unit_dfs = []
for file in obs_files:
    # Skip reading metadata files
    if 'GEMStat' not in file:
        obs_df = pd.read_csv(
            file,
            sep=';',
            usecols=obs_dtypes.keys(),
            dtype=obs_dtypes,
            encoding='latin-1'
        )
        unit_df = (
            obs_df.groupby(['Parameter.Code'])['Unit'].value_counts()
            .reset_index(name='count')
        )
        unit_dfs.append(unit_df)
unit_df = pd.concat(unit_dfs)

# Import parameter metadata
meta_file = os.path.join(raw_dir, 'GFQA_v2/GEMStat_parameter_metadata.csv')
param_dtypes = {
    'Parameter Code': object,
    'Parameter Long Name': object
}
param_df = pd.read_csv(
    meta_file,
    sep=';',
    usecols=param_dtypes.keys(),
    dtype=param_dtypes,
    encoding='latin-1'
)

# Merge the DFs and export to CSV
unit_df = unit_df.merge(
    param_df, left_on='Parameter.Code', right_on='Parameter Code'
)
unit_df = unit_df.drop('Parameter Code', axis=1)
unit_df.to_csv(
    os.path.join(raw_dir, 'meta', ds_name + '_units.csv'),
    sep=';',
    index=False,
    encoding='utf-8'
)
