# Import the libraries
import os
import glob

# Dataset names
ds_names = ['CESI', 'GEMSTAT', 'GLORICH', 'WATERBASE', 'WQP']

# Project directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'

# Create list of all parameter codes
param_codes = []
for ds in ds_names:
    proc_dir = os.path.join(proj_dir, 'data', ds, 'processed')
    obs_files = os.listdir(proc_dir)
    obs_files = glob.glob(os.path.join(proc_dir, '*.csv'))
    for obs_file in obs_files:
        param_code = os.path.basename(obs_file).split('_')[0]
        if param_code not in param_codes:
            param_codes.append(param_code)
param_codes.sort(key=str.lower)

# Export list
fname = os.path.join(proj_dir, 'data', 'GRQA', 'GRQA_param_codes.txt')
with open(fname, 'w') as file:
    file.write('\n'.join(param_codes))
    file.close()
