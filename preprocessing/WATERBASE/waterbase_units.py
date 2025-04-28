# Import the libraries
import sys
import os

import pandas as pd

# Name of the dataset
ds_name = 'WATERBASE'

# Raw directory
raw_dir = sys.argv[1]

# Import observation data
obs_file = sys.argv[2]
obs_dtypes = {
    'observedPropertyDeterminandCode': object,
    'resultUom': object
}
obs_df = pd.read_csv(obs_file, sep=',', usecols=obs_dtypes.keys(), dtype=obs_dtypes)

# Create DF of units
unit_df = obs_df.groupby(['observedPropertyDeterminandCode'])['resultUom'].value_counts().reset_index(name='count')

# Import parameter metadata
param_file = sys.argv[3]
param_dtypes = {
  'Label': object,
  'Notation': object
}
param_df = pd.read_csv(param_file, sep=',', usecols=param_dtypes.keys(), dtype=param_dtypes)

# Merge the DFs and export to CSV
unit_df = unit_df.merge(param_df, how='left', left_on='observedPropertyDeterminandCode', right_on='Notation')
unit_df.drop(columns='Notation', inplace=True)
unit_df.to_csv(os.path.join(raw_dir, 'meta', ds_name + '_units.csv'), sep=';', index=False, encoding='utf-8')
