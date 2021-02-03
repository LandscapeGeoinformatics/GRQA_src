# Import the libraries
import datetime
import os
import pandas as pd
import numpy as np
import pyproj
import hashlib

# Function for stripping whitespace from string columns
def strip_whitespace(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    return df

# Function to check if the date is valid
def check_date(row, date_col):
    correct_date = False
    date_strings = str(row[date_col]).split('-')
    if len(date_strings) >= 3:
        year, month, day = int(date_strings[0]), int(date_strings[1]), int(date_strings[2])
        datetime.datetime(year, month, day)
        correct_date = True
    else:
        print(f'Date error at row {row.name}')
        print(row)
        print('\n')
    return correct_date

# Function for creating dictionary containing file information
def get_file_info(file_path, row_count, file_desc):
    info_dict = {}
    info_dict['File name'] = os.path.basename(file_path)
    info_dict['Size (MB)'] = round(int(os.path.getsize(file_path)) / (1024 * 1024), 1)
    info_dict['Rows'] = row_count
    info_dict['Description'] = file_desc
    return info_dict

# Function for creating DF of missing values
def get_missing_values(df, file_name, sheet_name=None):
    mv_df = df.isnull().sum(axis=0).reset_index()
    mv_df.columns = ['Column name', 'Missing values']
    mv_df['File name'] = os.path.basename(file_name)
    mv_df = mv_df[['File name', 'Column name', 'Missing values']]
    if sheet_name:
        mv_df['Sheet name'] = sheet_name
        mv_df = mv_df[['File name', 'Sheet name', 'Column name', 'Missing values']]
    return mv_df

# Function for getting statistics of water quality parameter time series
def get_param_stats(value_col, date_col):
    stats_dict = {}
    stats_dict['count'] = value_col.count()
    stats_dict['min'] = value_col.min()
    stats_dict['max'] = value_col.max()
    stats_dict['mean'] = value_col.mean()
    stats_dict['median'] = value_col.median()
    stats_dict['std'] = value_col.std()
    year_col = date_col.str.split('-').str[0]
    year_col = year_col.astype(int)
    stats_dict['min_year'] = year_col.min()
    stats_dict['max_year'] = year_col.max()
    stats_dict['ts_length'] = stats_dict['max_year'] - stats_dict['min_year']
    return pd.Series(
        stats_dict, index=['count', 'min', 'max', 'mean', 'median', 'std', 'min_year', 'max_year', 'ts_length']
    )

# Function for getting a DF with parameter statistics
def get_stats_df(df, groupby_cols, value_col, date_col):
    stats_df = df.groupby(groupby_cols)\
        .apply(lambda group: get_param_stats(group[value_col], group[date_col]))\
        .reset_index()
    for col in ['count', 'min_year', 'max_year', 'ts_length']:
        stats_df[col] = stats_df[col].astype(np.int32)
    return stats_df

# Name of the dataset
ds_name = 'CESI'

# Directory paths
proj_dir = '/gpfs/space/home/holgerv/gis_holgerv/river_quality'
raw_dir = os.path.join(proj_dir, 'data', ds_name, 'raw')
proc_dir = os.path.join(proj_dir, 'data', ds_name, 'processed')

# Download directory
dl_dir = os.path.join(raw_dir, 'download_2020-11-16')

# Import the code map
cmap_file = os.path.join(os.path.dirname(dl_dir), 'meta', ds_name + '_code_map.csv')
cmap_df = pd.read_csv(cmap_file, sep=';')
param_codes = cmap_df['source_param_code'].to_list()

# Import observation data
obs_file = os.path.join(dl_dir, 'wqi-federal-raw-data-2020-iqe-donnees-brutes-fed.csv')
obs_dtypes = {
    'SITE_NO': object,
    'SITE_NAME_NOM': object,
    'DATE': object,
    'VARIABLE_NAME': object,
    'FORM_NAME': object,
    'FLAG_MARQUEUR': object,
    'VALUE_VALEUR': np.float64,
    'UNIT_UNITE': object,
    'LATITUDE': np.float64,
    'LONGITUDE': np.float64,
    'DRAINAGE_REGION': object
}
obs_reader = pd.read_csv(
    obs_file, sep=',', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000, quotechar='"',
    encoding='latin-1'
)

# Process observation data in chunks
obs_row_count = 0
obs_chunks = []
for obs_chunk in obs_reader:
    obs_row_count += len(obs_chunk)
    obs_chunk = strip_whitespace(obs_chunk)
    obs_chunk.drop_duplicates(inplace=True)
    # Drop sites with missing or implausible location information
    obs_chunk.drop(obs_chunk[(obs_chunk['SITE_NO'].isnull())].index, inplace=True, errors='ignore')
    obs_chunk.drop(
        obs_chunk[(obs_chunk['LATITUDE'].isnull()) & (obs_chunk['LONGITUDE'].isnull())].index, inplace=True,
        errors='ignore'
    )
    obs_chunk.drop(
        obs_chunk[(obs_chunk['LATITUDE'] < -90) & (obs_chunk['LATITUDE'] > 90)].index, inplace=True, errors='ignore'
    )
    obs_chunk.drop(
        obs_chunk[(obs_chunk['LONGITUDE'] < -180) & (obs_chunk['LONGITUDE'] > 180)].index, inplace=True,
        errors='ignore'
    )
    # Keep only necessary parameters
    obs_chunk.drop(obs_chunk[~obs_chunk['VARIABLE_NAME'].isin(param_codes)].index, inplace=True, errors='ignore')
    # Drop values that are below detection limit, missing or negative
    obs_chunk.drop(obs_chunk[obs_chunk['FLAG_MARQUEUR'] != '='].index, inplace=True, errors='ignore')
    obs_chunk.drop(
        obs_chunk[(obs_chunk['VALUE_VALEUR'].isnull()) | (obs_chunk['VALUE_VALEUR'] <= 0)].index, inplace=True,
        errors='ignore'
    )
    obs_chunks.append(obs_chunk)

# DF of observations
obs_df = pd.concat(obs_chunks)
obs_df.drop_duplicates(inplace=True)
obs_df.reset_index(drop=True, inplace=True)

# Get file information and export to CSV
info_dict = get_file_info(obs_file, obs_row_count, 'Water chemistry observations')
info_df = pd.DataFrame([info_dict])
info_df.to_csv(os.path.join(proc_dir, 'meta', ds_name + '_file_info.csv'), sep=';', index=False, encoding='utf-8')

# Get missing values and export to CSV
mv_df = get_missing_values(obs_df, obs_file)
mv_df.to_csv(
    os.path.join(proc_dir, 'meta', ds_name + '_missing_values.csv'), sep=';', index=False, encoding='utf-8'
)

# Create observation identifier column by hashing
df_string = obs_df.to_string(header=False, index=False, index_names=False).split('\n')
obs_strings = ['\t'.join(string.split()) for string in df_string]
hash_ids = [hashlib.sha256(string.encode()).hexdigest() for string in obs_strings]
obs_df['obs_id'] = hash_ids

# Convert date to correct format and add time column
obs_df['obs_date'] = pd.to_datetime(obs_df['DATE'], format='%d/%m/%Y').dt.strftime('%Y-%m-%d')
obs_df['obs_time'] = '00:00:00'

# Check the validity of the dates and drop invalid dates
obs_df['valid_date'] = obs_df.apply(check_date, date_col='obs_date', axis=1)
obs_df = obs_df[obs_df['valid_date'] == True]

# Convert coordinates from NAD83 to WGS84
transformer = pyproj.Transformer.from_crs('epsg:4269', 'epsg:4326')
points = list(zip(obs_df['LONGITUDE'], obs_df['LATITUDE']))
coords_wgs = np.array(list(transformer.itransform(points)))
obs_df['lon_wgs84'] = coords_wgs[:, 0]
obs_df['lat_wgs84'] = coords_wgs[:, 1]
obs_df.drop(
    obs_df[(obs_df['lat_wgs84'].isnull()) & (obs_df['lon_wgs84'].isnull())].index, inplace=True, errors='ignore'
)
obs_df.drop(obs_df[(obs_df['lat_wgs84'] < -90) & (obs_df['lat_wgs84'] > 90)].index, inplace=True, errors='ignore')
obs_df.drop(obs_df[(obs_df['lon_wgs84'] < -180) & (obs_df['lon_wgs84'] > 180)].index, inplace=True, errors='ignore')

# Merge the DFs
merged_df = obs_df\
    .merge(
        cmap_df, how='left', left_on=['VARIABLE_NAME', 'FORM_NAME'],
        right_on=['source_param_code', 'source_param_code_meta']
)
merged_df.drop(merged_df[(merged_df['param_code'].isnull())].index, inplace=True, errors='ignore')

# Convert observation values
merged_df['obs_value'] = merged_df['VALUE_VALEUR'] * merged_df['conversion_constant']

# Add filtration column
merged_df.loc[merged_df['FORM_NAME'] == 'Unfiltered', 'filtration'] = 'unfiltered'

# Get statistics about raw and processed observation values and export to CSV
value_dict = {'raw': 'VALUE_VALEUR', 'processed': 'obs_value'}
for value_type, value_col in value_dict.items():
    stats_df = get_stats_df(
        merged_df,
        ['source_param_code', 'param_code', 'param_name', 'source_param_form', 'param_form', 'source_unit', 'unit'],
        value_col, 'obs_date'
    )
    agg_stats_df = get_stats_df(merged_df, ['SITE_NO', 'source_param_code'], value_col, 'obs_date')
    agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
        .agg(
            site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'),
            mean_ts_length_per_site=('ts_length', 'mean')
        ).reset_index()
    stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
    fname = '_'.join([ds_name, value_type, 'stats.csv'])
    stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Export processed data to CSV
output_codes = merged_df['param_code'].unique()
for code in output_codes:
    code_df = merged_df[merged_df['param_code'] == code]
    # Dictionary with output columns
    code_dict = {
        'obs_id': code_df['obs_id'],
        'lat_wgs84': code_df['lat_wgs84'],
        'lon_wgs84': code_df['lon_wgs84'],
        'obs_date': code_df['obs_date'],
        'obs_time': code_df['obs_time'],
        'obs_time_zone': np.nan,
        'site_id': code_df['SITE_NO'],
        'site_name': code_df['SITE_NAME_NOM'],
        'site_country': 'Canada',
        'upstream_basin_area': np.nan,
        'upstream_basin_area_unit': np.nan,
        'drainage_region_name': code_df['DRAINAGE_REGION'],
        'param_code': code_df['param_code'],
        'source_param_code': code_df['source_param_code'],
        'param_name': code_df['param_name'],
        'source_param_name': code_df['source_param_name'],
        'obs_value': code_df['obs_value'],
        'source_obs_value': code_df['VALUE_VALEUR'],
        'param_form': code_df['param_form'],
        'source_param_form': code_df['source_param_form'],
        'unit': code_df['unit'],
        'source_unit': code_df['UNIT_UNITE'],
        'filtration': code_df['filtration'],
        'source': ds_name
    }
    output_df = pd.DataFrame(code_dict)
    output_df.to_csv(os.path.join(proc_dir, code + '_' + ds_name + '.csv'), sep=';', index=False, encoding='utf-8')
