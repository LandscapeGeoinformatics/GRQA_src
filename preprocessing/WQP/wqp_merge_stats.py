# Import the libraries
import os
import pandas as pd
import glob

# Name of the dataset
ds_name = 'WQP'

# Directory paths
# proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
# meta_dir = os.path.join(proj_dir, 'data', ds_name, 'processed', 'meta')
proj_dir = '/gpfs/terra/export/samba/gis/holgerv'
meta_dir = os.path.join(proj_dir, 'GRQA_v1.3', 'GRQA_source_data', ds_name, 'processed', 'meta')

# Merge and export WQP statistics
fname_strings = ['missing_values.csv', 'file_info.csv', 'raw_stats.csv', 'processed_stats.csv']
for string in fname_strings:
    stats_files = glob.glob(os.path.join(meta_dir, ds_name + '_*_' + string))
    stats_df = pd.concat([pd.read_csv(file, sep=';', low_memory=False, encoding='utf-8') for file in stats_files])
    stats_df.to_csv(os.path.join(meta_dir, ds_name + '_' + string), sep=';', index=False)
    # Remove old files
    for file in stats_files:
        os.remove(file)