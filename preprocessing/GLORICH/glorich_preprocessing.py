# Import the libraries
import datetime
import os
import sys

import geopandas as gpd
import pandas as pd
import numpy as np
import hashlib

# Function for stripping whitespace from string columns
def strip_whitespace(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.strip()
    return df

# Function for replacing semicolons and line breaks
def replace_chars(df):
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].str.replace(';', ',')
            df[col] = df[col].str.replace('\n', '')
            df[col] = df[col].str.replace('\r', ' ')
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
def get_file_info(file_path, row_count, file_desc, sheet_name=None):
    info_dict = {}
    info_dict['File name'] = os.path.basename(file_path)
    info_dict['Size (MB)'] = round(int(os.path.getsize(file_path)) / (1024 * 1024), 1)
    info_dict['Rows'] = row_count
    info_dict['Description'] = file_desc
    if sheet_name:
        info_dict['Sheet name'] = sheet_name
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
ds_name = 'GLORICH'

# Processed directory
proc_dir = sys.argv[1]

# Raw directory
raw_dir = sys.argv[2]

# Import the code map
cmap_file = sys.argv[3]
cmap_df = pd.read_csv(cmap_file, sep=';')
param_codes = cmap_df['source_param_code'].to_list()

# Import site point data
site_file = sys.argv[4]
site_df = gpd.read_file(site_file)
site_df = strip_whitespace(site_df)
site_df = replace_chars(site_df)
site_df.drop_duplicates(inplace=True)

# Get site file information and append to list
info_dicts = []
info_dicts.append(get_file_info(site_file, len(site_df), 'Site point data'))

# Get missing values and append to list
mv_dfs = []
mv_dfs.append(get_missing_values(site_df, site_file))

# Add latitude and longitude column
site_df['lat_wgs84'] = site_df['geometry'].y
site_df['lon_wgs84'] = site_df['geometry'].x

# Drop sites with missing or implausible location information
site_df.drop(site_df[(site_df['STAT_ID'].isnull())].index, inplace=True, errors='ignore')
site_df.drop(
    site_df[(site_df['lat_wgs84'].isnull()) & (site_df['lon_wgs84'].isnull())].index, inplace=True,
    errors='ignore'
)
site_df.drop(
    site_df[(site_df['lat_wgs84'] < -90) & (site_df['lat_wgs84'] > 90)].index, inplace=True, errors='ignore'
)
site_df.drop(
    site_df[(site_df['lon_wgs84'] < -180) & (site_df['lon_wgs84'] > 180)].index, inplace=True,
    errors='ignore'
)

# Get duplicate sites and export to CSV
dup_sites = site_df[site_df.duplicated(['STAT_ID'])]['STAT_ID'].to_list()
dup_df = site_df.loc[site_df['STAT_ID'].isin(dup_sites)].sort_values('STAT_ID')
dup_df.to_csv(os.path.join(proc_dir, 'meta', ds_name + '_dup_sites.csv'), sep=';', index=False, encoding='utf-8')

# Keep first instance of duplicate site ID
site_df.drop_duplicates(subset='STAT_ID', keep='first', inplace=True)

# Import site name data
sname_file = sys.argv[5]
sname_dtypes = {
    'STAT_ID': np.int64,
    'STATION_NAME': object,
    'Country': object,
    'Latitude': np.float64,
    'Longitude': np.float64
}
sname_df = pd.read_csv(
    sname_file, sep=',', usecols=sname_dtypes.keys(), dtype=sname_dtypes, skipinitialspace=True, quotechar='"',
    encoding='latin-1'
)
sname_df = strip_whitespace(sname_df)
sname_df = replace_chars(sname_df)
sname_df.drop_duplicates(inplace=True)
info_dicts.append(get_file_info(sname_file, len(sname_df), 'Site name data'))
mv_dfs.append(get_missing_values(sname_df, sname_file))

# Import catchment data
catchment_file = sys.argv[6]
catchment_dtypes = {
    'STAT_ID': np.int64,
    'Shape_Area': np.float64
}
catchment_df = pd.read_csv(catchment_file, sep=',', usecols=catchment_dtypes.keys(), dtype=catchment_dtypes, skipinitialspace=True, quotechar='"')
catchment_df = strip_whitespace(catchment_df)
catchment_df = replace_chars(catchment_df)
catchment_df.drop_duplicates(inplace=True)
info_dicts.append(get_file_info(catchment_file, len(catchment_df), 'Catchment data'))
mv_dfs.append(get_missing_values(catchment_df, catchment_file))

# Import remark data
remark_file = sys.argv[7]
remark_df = pd.read_csv(remark_file, sep=';')

# Import observation data
obs_file = sys.argv[8]
obs_dtypes = {
    'STAT_ID': np.int64,
    'RESULT_DATETIME': object
}
value_cols = param_codes
remark_cols = [code + '_vrc' for code in param_codes]
for value_col, remark_col in zip(value_cols, remark_cols):
    obs_dtypes[value_col] = np.float64
    obs_dtypes[remark_col] = object
obs_reader = pd.read_csv(
    obs_file,
    sep=',',
    usecols=obs_dtypes.keys(),
    dtype=obs_dtypes,
    chunksize=100000,
    skipinitialspace=True,
    quotechar='"',
    encoding='unicode_escape'
)

# Process observation data in chunks
obs_row_count = 0
obs_chunks = []
for obs_chunk in obs_reader:
    obs_row_count += len(obs_chunk)
    obs_chunk = strip_whitespace(obs_chunk)
    obs_chunk = replace_chars(obs_chunk)
    obs_chunk.drop_duplicates(inplace=True)
    value_chunk = pd.melt(
        obs_chunk, id_vars='STAT_ID', value_vars=value_cols, var_name='source_param_code',
        value_name='source_obs_value'
    )
    remark_chunk = pd.melt(
        obs_chunk, id_vars='RESULT_DATETIME', value_vars=remark_cols, var_name='remark_code', value_name='remark'
    )
    obs_chunk = pd.concat([value_chunk, remark_chunk], axis=1)
    # Drop missing or negative values
    obs_chunk.drop(
        obs_chunk[(obs_chunk['source_obs_value'].isnull()) | (obs_chunk['source_obs_value'] <= 0)].index,
        inplace=True, errors='ignore'
    )
    obs_chunks.append(obs_chunk)

# DF of observations
obs_df = pd.concat(obs_chunks)
obs_df.drop_duplicates(inplace=True)
obs_df.reset_index(drop=True, inplace=True)
info_dicts.append(get_file_info(obs_file, obs_row_count, 'Water chemistry observations'))
mv_dfs.append(get_missing_values(obs_df, obs_file))

# Create observation identifier column by hashing
df_string = obs_df.to_string(header=False, index=False, index_names=False).split('\n')
obs_strings = ['\t'.join(string.split()) for string in df_string]
hash_ids = [hashlib.sha256(string.encode()).hexdigest() for string in obs_strings]
obs_df['obs_id'] = hash_ids

# Convert date to correct format and add time column
obs_df['obs_date'] = pd.to_datetime(obs_df['RESULT_DATETIME'], format='%d/%m/%Y %H:%M:%S').dt.strftime('%Y-%m-%d')
obs_df['obs_time'] = pd.to_datetime(obs_df['RESULT_DATETIME'], format='%d/%m/%Y %H:%M:%S').dt.strftime('%H:%M:%S')
obs_df.drop(obs_df[(obs_df['obs_date'].isnull())].index, inplace=True, errors='ignore')

# Check the validity of the dates and drop invalid dates
obs_df['valid_date'] = obs_df.apply(check_date, date_col='obs_date', axis=1)
obs_df = obs_df[obs_df['valid_date']]

# Export file information to CSV
info_df = pd.DataFrame(info_dicts)
info_df.to_csv(os.path.join(proc_dir, 'meta', ds_name + '_file_info.csv'), sep=';', index=False, encoding='utf-8')

# Export missing values to CSV
mv_df = pd.concat(mv_dfs)
mv_df.to_csv(
    os.path.join(proc_dir, 'meta', ds_name + '_missing_values.csv'), sep=';', index=False, encoding='utf-8'
)

# Flag values that are marked as below and above detection limit in source data
obs_df.loc[obs_df['remark'] == '<', 'detection_limit_flag'] = '<'
obs_df.loc[obs_df['remark'] == '>', 'detection_limit_flag'] = '>'

# Merge the DFs
merged_df = site_df\
    .merge(sname_df, how='left', on='STAT_ID')\
    .merge(catchment_df, how='left', on='STAT_ID')\
    .merge(obs_df, how='left', on='STAT_ID')\
    .merge(cmap_df, how='left', on='source_param_code')\
    .merge(remark_df, how='left', left_on='remark', right_on='Value remark code')
merged_df.drop_duplicates(inplace=True)
merged_df.reset_index(drop=True, inplace=True)
merged_df.drop(merged_df[(merged_df['param_code'].isnull())].index, inplace=True, errors='ignore')
merged_df.drop(merged_df[(merged_df['obs_date'].isnull())].index, inplace=True, errors='ignore')

# Convert observation values
merged_df['obs_value'] = merged_df['source_obs_value'] * merged_df['conversion_constant']

# Add filtration column
merged_df.loc[merged_df['remark'] == 'U', 'filtration'] = 'unfiltered'

# Get statistics about raw and processed observation values and export to CSV
value_dict = {'raw': 'source_obs_value', 'processed': 'obs_value'}
for value_type, value_col in value_dict.items():
    stats_df = get_stats_df(
        merged_df,
        ['source_param_code', 'param_code', 'param_name', 'source_param_form', 'param_form', 'source_unit', 'unit'],
        value_col, 'obs_date'
    )
    agg_stats_df = get_stats_df(merged_df, ['STAT_ID', 'source_param_code'], value_col, 'obs_date')
    agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
        .agg(
            site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'),
            mean_ts_length_per_site=('ts_length', 'mean')
        ).reset_index()
    stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
    fname = '_'.join([ds_name, value_type, 'stats.csv'])
    stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Export processed data to CSV
meta_cols = ['Value remark code', 'Meaning']
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
        'site_id': code_df['STAT_ID'],
        'site_name': code_df['STATION_NAME'],
        'site_country': code_df['Country'],
        'upstream_basin_area': code_df['Shape_Area'],
        'upstream_basin_area_unit': np.nan,
        'drainage_region_name': np.nan,
        'param_code': code_df['param_code'],
        'source_param_code': code_df['source_param_code'],
        'param_name': code_df['param_name'],
        'source_param_name': code_df['source_param_name'],
        'detection_limit_flag': code_df['detection_limit_flag'],
        'obs_value': code_df['obs_value'],
        'source_obs_value': code_df['source_obs_value'],
        'param_form': code_df['param_form'],
        'source_param_form': code_df['source_param_form'],
        'unit': code_df['unit'],
        'source_unit': code_df['source_unit'],
        'filtration': code_df['filtration'],
        'source': ds_name
    }
    # Add metadata columns to the dictionary
    for col in meta_cols:
        col_name = '_'.join([ds_name, 'meta', col])
        col_name = col_name.replace(' ', '_')
        code_dict[col_name] = code_df[col]
    output_df = pd.DataFrame(code_dict)
    output_df.to_csv(os.path.join(proc_dir, code + '_' + ds_name + '.csv'), sep=';', index=False, encoding='utf-8')
