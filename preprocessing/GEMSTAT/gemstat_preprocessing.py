# Import the libraries
import datetime
import os
import sys

import pandas as pd
import numpy as np
import glob
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
ds_name = 'GEMSTAT'

# Processed directory
proc_dir = sys.argv[1]

# Raw directory
raw_dir = sys.argv[2]

# Import the code map
cmap_file = sys.argv[3]
cmap_df = pd.read_csv(cmap_file, sep=';')
param_codes = cmap_df['source_param_code'].to_list()

# Import site data
site_file = sys.argv[4]
site_dtypes = {
    'GEMS Station Number': object,
    'Water Type': object,
    'Country Name': object,
    'Station Identifier': object,
    'Station Narrative': object,
    'Main Basin': object,
    'Upstream Basin Area': np.float64,
    'Latitude': np.float64,
    'Longitude': np.float64
}
site_df = pd.read_csv(site_file, sep=';', usecols=site_dtypes.keys(), dtype=site_dtypes, encoding='latin-1', decimal=',')
site_df = strip_whitespace(site_df)
site_df = replace_chars(site_df)
site_df.drop_duplicates(inplace=True)

# Keep only river sites
site_df.drop(site_df[site_df['Water Type'] != 'River station'].index, inplace=True, errors='ignore')

# Get site file information and append to list
info_dicts = []
info_dicts.append(get_file_info(site_file, len(site_df), 'Sampling location data'))

# Get missing values and append to list
mv_dfs = []
mv_dfs.append(get_missing_values(site_df, site_file, 'Station_Metadata'))

# Drop sites with missing or implausible location information
site_df.drop(site_df[(site_df['GEMS Station Number'].isnull())].index, inplace=True, errors='ignore')
site_df.drop(
    site_df[(site_df['Latitude'].isnull()) & (site_df['Longitude'].isnull())].index, inplace=True,
    errors='ignore'
)
site_df.drop(
    site_df[(site_df['Latitude'] < -90) & (site_df['Latitude'] > 90)].index, inplace=True, errors='ignore'
)
site_df.drop(
    site_df[(site_df['Longitude'] < -180) & (site_df['Longitude'] > 180)].index, inplace=True,
    errors='ignore'
)

# Import parameter metadata
param_file = sys.argv[5]
param_dtypes = {
    'Parameter Code': object,
    'Parameter Long Name': object,
    'Parameter Description': object
}
param_df = pd.read_csv(
    param_file, sep=';', usecols=param_dtypes.keys(), dtype=param_dtypes, encoding='latin-1'
)
param_df = strip_whitespace(param_df)
param_df = replace_chars(param_df)
info_dicts.append(get_file_info(param_file, len(param_df), 'Parameter metadata'))
mv_dfs.append(get_missing_values(param_df, param_file))

# Import method metadata
method_file = sys.argv[6]
method_dtypes = {
    'Parameter Code': object,
    'Analysis Method Code': object,
    'Method Name': object,
    'Method Description': object
}
method_df = pd.read_csv(
    method_file, sep=';', usecols=method_dtypes.keys(), dtype=method_dtypes, encoding='latin-1'
)
method_df = strip_whitespace(method_df)
method_df = replace_chars(method_df)
info_dicts.append(get_file_info(method_file, len(method_df), 'Method metadata'))
mv_dfs.append(get_missing_values(method_df, method_file))

# List of observation files
obs_files = glob.glob(os.path.join(raw_dir, 'GFQA_v2/*.csv'))

# Import observation data
obs_dtypes = {
    'GEMS.Station.Number': object,
    'Sample.Date': object,
    'Sample.Time': object,
    'Parameter.Code': object,
    'Analysis.Method.Code': object,
    'Value.Flags': object,
    'Value': np.float64,
    'Unit': object,
    'Data.Quality': object
}
obs_dfs = []
for file in obs_files:
    # Skip reading metadata files
    if 'GEMStat' not in file:
        obs_df = pd.read_csv(file, sep=';', usecols=obs_dtypes.keys(), dtype=obs_dtypes, encoding='latin-1')
        obs_df = strip_whitespace(obs_df)
        obs_df = replace_chars(obs_df)
        obs_df.drop_duplicates(inplace=True)
        info_dicts.append(get_file_info(file, len(obs_df), 'Observation data'))
        mv_dfs.append(get_missing_values(obs_df, file))
        # Keep only necessary parameters
        obs_df.drop(obs_df[~obs_df['Parameter.Code'].isin(param_codes)].index, inplace=True, errors='ignore')
        # Drop missing or negative values
        obs_df.drop(
            obs_df[(obs_df['Value'].isnull()) | (obs_df['Value'] <= 0)].index, inplace=True, errors='ignore'
        )
        # Drop observations pending review, suspect or contaminated
        obs_df.drop(obs_df[obs_df['Data.Quality'].isin(['Pending review', 'Suspect', 'Contamination'])].index, inplace=True, errors='ignore')
        obs_dfs.append(obs_df)

# DF of observations
obs_df = pd.concat(obs_dfs)
obs_df.drop_duplicates(inplace=True)
obs_df.reset_index(drop=True, inplace=True)

# Create observation identifier column by hashing
df_string = obs_df.to_string(header=False, index=False, index_names=False).split('\n')
obs_strings = ['\t'.join(string.split()) for string in df_string]
hash_ids = [hashlib.sha256(string.encode()).hexdigest() for string in obs_strings]
obs_df['obs_id'] = hash_ids

# Convert date to correct format and add time column
obs_df['obs_date'] = pd.to_datetime(obs_df['Sample.Date'], format='%Y-%m-%d').dt.strftime('%Y-%m-%d')
obs_df['obs_time'] = pd.to_datetime(obs_df['Sample.Time'], format='%H:%M').dt.strftime('%H:%M:%S')

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
obs_df.loc[obs_df['Value.Flags'] == '<', 'detection_limit_flag'] = '<'
obs_df.loc[obs_df['Value.Flags'] == '>', 'detection_limit_flag'] = '>'

# Merge the DFs
merged_df = site_df\
    .merge(obs_df, how='left', left_on='GEMS Station Number', right_on='GEMS.Station.Number')\
    .merge(param_df, how='left', left_on='Parameter.Code', right_on='Parameter Code')\
    .merge(
        method_df, how='left',
        left_on=['Parameter.Code', 'Analysis.Method.Code'], right_on=['Parameter Code', 'Analysis Method Code']
    )\
    .merge(
        cmap_df, how='left', left_on=['Parameter.Code', 'Unit'],
        right_on=['source_param_code', 'source_unit']
    )
merged_df.drop_duplicates(inplace=True)
merged_df.reset_index(drop=True, inplace=True)
merged_df.drop(merged_df[(merged_df['param_code'].isnull())].index, inplace=True, errors='ignore')

# Convert observation values
merged_df['obs_value'] = merged_df['Value'] * merged_df['conversion_constant']

# Add filtration column
merged_df['filtration'] = np.nan

# Get statistics about raw and processed observation values and export to CSV
value_dict = {'raw': 'Value', 'processed': 'obs_value'}
for value_type, value_col in value_dict.items():
    stats_df = get_stats_df(
        merged_df,
        ['source_param_code', 'param_code', 'param_name', 'source_param_form', 'param_form', 'source_unit', 'unit'],
        value_col, 'obs_date'
    )
    agg_stats_df = get_stats_df(merged_df, ['GEMS Station Number', 'source_param_code'], value_col, 'obs_date')
    agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
        .agg(
            site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'),
            mean_ts_length_per_site=('ts_length', 'mean')
        ).reset_index()
    stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
    fname = '_'.join([ds_name, value_type, 'stats.csv'])
    stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Export processed data to CSV
meta_cols = [
    'Station Narrative', 'Parameter Description', 'Analysis Method Code', 'Method Name', 'Method Description'
]
output_codes = merged_df['param_code'].unique()
for code in output_codes:
    code_df = merged_df[merged_df['param_code'] == code]
    # Dictionary with output columns
    code_dict = {
        'obs_id': code_df['obs_id'],
        'lat_wgs84': code_df['Latitude'],
        'lon_wgs84': code_df['Longitude'],
        'obs_date': code_df['obs_date'],
        'obs_time': code_df['obs_time'],
        'obs_time_zone': np.nan,
        'site_id': code_df['GEMS Station Number'],
        'site_name': code_df['Station Identifier'],
        'site_country': code_df['Country Name'],
        'upstream_basin_area': code_df['Upstream Basin Area'],
        'upstream_basin_area_unit': np.nan,
        'drainage_region_name': code_df['Main Basin'],
        'param_code': code_df['param_code'],
        'source_param_code': code_df['source_param_code'],
        'param_name': code_df['param_name'],
        'source_param_name': code_df['source_param_name'],
        'obs_value': code_df['obs_value'],
        'source_obs_value': code_df['Value'],
        'detection_limit_flag': code_df['detection_limit_flag'],
        'param_form': code_df['param_form'],
        'source_param_form': code_df['source_param_form'],
        'unit': code_df['unit'],
        'source_unit': code_df['Unit'],
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
