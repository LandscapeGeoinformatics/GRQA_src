# Import the libraries
import os
from datetime import date
import shutil
import pandas as pd
import urllib.request
import glob

# Name of the dataset
ds_name = 'WQP'

# Download directory
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
dl_dir = os.path.join(proj_dir, 'data', ds_name, 'raw', f'download_{date.today()}')
if os.path.exists(dl_dir):
    shutil.rmtree(dl_dir)
os.mkdir(dl_dir)

# Import the code map
cmap_dtypes = {
    'source_param_code': object
}
cmap_file = os.path.join(os.path.dirname(dl_dir), 'meta', ds_name + '_code_map.txt')
cmap_df = pd.read_csv(cmap_file, sep='\t', usecols=cmap_dtypes.keys(), dtype=cmap_dtypes, encoding='utf8')
param_codes = cmap_df['source_param_code'].to_list()

# Import US state codes
state_code_dtypes = {
    'fips_code': object
}
state_code_file = os.path.join(os.path.dirname(dl_dir), 'meta', 'fips_state.csv')
state_code_df = pd.read_csv(state_code_file, sep=',', usecols=state_code_dtypes.keys(), dtype=state_code_dtypes)
state_codes = state_code_df['fips_code'].to_list()

# Download observation data
for param_code in param_codes:
    # Temperature (00010) data has to be downloaded per state to avoid the 504 Gateway Timeout error
    if param_code == '00010':
        for state_code in state_codes:
            url = 'https://www.waterqualitydata.us/data/Result/search?statecode=US%3A' + state_code \
                  + '&siteType=Stream&pCode=' + param_code + '&mimeType=csv&zip=no&dataProfile=narrowResult'
            fname = '_'.join([ds_name, param_code, state_code, 'obs.csv'])
            file_path = os.path.join(dl_dir, fname)
            if os.path.exists(file_path):
                os.remove(file_path)
            urllib.request.urlretrieve(url, file_path)
    else:
        url = 'https://www.waterqualitydata.us/data/Result/search?countrycode=US&siteType=Stream' \
              '&pCode=' + param_code + '&mimeType=csv&zip=no&dataProfile=narrowResult'
        fname = '_'.join([ds_name, param_code, 'obs.csv'])
        file_path = os.path.join(dl_dir, fname)
        if os.path.exists(file_path):
            os.remove(file_path)
        urllib.request.urlretrieve(url, file_path)

# Concatenate temperature observation data
temp_obs_files = glob.glob(os.path.join(dl_dir, ds_name + '_00010_*_obs.csv'))
temp_obs_df = pd.concat([pd.read_csv(file, dtype=object, low_memory=False) for file in temp_obs_files])
temp_obs_df.to_csv(os.path.join(dl_dir, ds_name + '_00010_obs.csv'), sep=',', index=False)

# Remove state temperature observation files
for file in temp_obs_files:
    os.remove(file)

# Download site data
for param_code in param_codes:
    url = 'https://www.waterqualitydata.us/data/Station/search?countrycode=US&siteType=Stream' \
          '&pCode=' + param_code + '&mimeType=csv&zip=no'
    fname = '_'.join([ds_name, param_code, 'sites.csv'])
    file_path = os.path.join(dl_dir, fname)
    if os.path.exists(file_path):
        os.remove(file_path)
    urllib.request.urlretrieve(url, file_path)
