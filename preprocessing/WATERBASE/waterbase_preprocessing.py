# Import the libraries
import sys
import datetime
import os
import hashlib

import pandas as pd
import numpy as np

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
ds_name = 'WATERBASE'

# Processed directory
proc_dir = sys.argv[1]

# Import the code map
cmap_file = sys.argv[2]
cmap_df = pd.read_csv(cmap_file, sep=';')
param_codes = cmap_df['source_param_code'].to_list()

# Import site data
site_file = sys.argv[3]
site_dtypes = {
    'countryCode': object,
    'monitoringSiteIdentifier': object,
    'monitoringSiteName': object,
    'waterBodyName': object,
    'confidentialityStatus': object,
    'lon': np.float64,
    'lat': np.float64
}
site_df = pd.read_csv(site_file, sep=',', usecols=site_dtypes.keys(), dtype=site_dtypes)
site_df = strip_whitespace(site_df)
site_df = replace_chars(site_df)
site_df.drop_duplicates(inplace=True)
site_df.reset_index(drop=True, inplace=True)

# Get site file information and append to list
info_dicts = []
info_dicts.append(get_file_info(site_file, len(site_df), 'Sampling location data'))

# Get missing values and append to list
mv_dfs = []
mv_dfs.append(get_missing_values(site_df, site_file))

# Drop sites not available for publication
site_df.drop(site_df['confidentialityStatus'] == 'N', inplace=True, errors='ignore')

# Drop sites with missing or implausible location information
site_df.drop(site_df[(site_df['monitoringSiteIdentifier'].isnull())].index, inplace=True, errors='ignore')
site_df.drop(
    site_df[(site_df['lat'].isnull()) & (site_df['lon'].isnull())].index, inplace=True,
    errors='ignore'
)
site_df.drop(
    site_df[(site_df['lat'] < -90) & (site_df['lat'] > 90)].index, inplace=True, errors='ignore'
)
site_df.drop(
    site_df[(site_df['lon'] < -180) & (site_df['lon'] > 180)].index, inplace=True,
    errors='ignore'
)

# Get duplicate sites and export to CSV
dup_sites = site_df[site_df.duplicated(['monitoringSiteIdentifier'])]['monitoringSiteIdentifier'].to_list()
dup_df = site_df.loc[site_df['monitoringSiteIdentifier'].isin(dup_sites)].sort_values('monitoringSiteIdentifier')
dup_df.to_csv(os.path.join(proc_dir, 'meta', ds_name + '_dup_sites.csv'), sep=';', index=False, encoding='utf-8')

# Keep first instance of duplicate site ID
site_df.drop_duplicates(subset='monitoringSiteIdentifier', keep='first', inplace=True)
site_df.reset_index(drop=True, inplace=True)

# Import parameter metadata
param_dtypes = {
  'Label': object,
  'Notation': object
}
param_file = sys.argv[4]
param_df = pd.read_csv(param_file, sep=',', usecols=param_dtypes.keys(), dtype=param_dtypes, quotechar='"')
param_df = strip_whitespace(param_df)
param_df = replace_chars(param_df)
param_df.drop_duplicates(inplace=True)
param_df.reset_index(drop=True, inplace=True)
info_dicts.append(get_file_info(param_file, len(param_df), 'Water chemistry observations'))
mv_dfs.append(get_missing_values(param_df, param_file))

# Import observation data
obs_file = sys.argv[5]
obs_dtypes = {
    'monitoringSiteIdentifier': object,
    'parameterWaterBodyCategory': object,
    'observedPropertyDeterminandCode': object,
    'observedPropertyDeterminandLabel': object,
    'procedureAnalysedMatrix': object,
    'resultUom': object,
    'phenomenonTimeSamplingDate': object,
    'resultObservedValue': np.float64,
    'resultQualityObservedValueBelowLOQ': object,
    'resultObservationStatus': object,
    'Remarks': object,
    'metadata_observationStatus': object
}
obs_reader = pd.read_csv(obs_file, sep=',', usecols=obs_dtypes.keys(), dtype=obs_dtypes, chunksize=100000)

# Process observation data in chunks
obs_row_count = 0
obs_chunks = []
for obs_chunk in obs_reader:
    obs_row_count += len(obs_chunk)
    obs_chunk = strip_whitespace(obs_chunk)
    obs_chunk = replace_chars(obs_chunk)
    obs_chunk.drop_duplicates(inplace=True)
    obs_chunk.reset_index(drop=True, inplace=True)
    obs_chunk['resultQualityObservedValueBelowLOQ'] = pd.to_numeric(obs_chunk['resultQualityObservedValueBelowLOQ'], errors='coerce')
    # Keep only river sites
    obs_chunk.drop(obs_chunk[~(obs_chunk['parameterWaterBodyCategory'] == 'RW')].index, inplace=True, errors='ignore')
    # Keep only necessary parameters
    obs_chunk.drop(
        obs_chunk[~obs_chunk['observedPropertyDeterminandCode'].isin(param_codes)].index, inplace=True,
        errors='ignore'
    )
    # Drop missing or negative values
    obs_chunk.drop(
        obs_chunk[(obs_chunk['resultObservedValue'].isnull()) | (obs_chunk['resultObservedValue'] <= 0)].index,
        inplace=True, errors='ignore'
    )
    # Keep only values that are confirmed as correct and from a reliable source
    obs_chunk.drop(
        obs_chunk[
            ~(
                (obs_chunk['resultObservationStatus'].isna()) | 
                (obs_chunk['resultObservationStatus'] == 'A')
            )
        ].index,
        inplace=True,
        errors='ignore'
    )
    obs_chunk.drop(obs_chunk[obs_chunk['metadata_observationStatus'] != 'A'].index, inplace=True, errors='ignore')
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
obs_df['obs_date'] = pd.to_datetime(obs_df['phenomenonTimeSamplingDate'], format='%Y%m%d').dt.strftime('%Y-%m-%d')
obs_df['obs_time'] = '00:00:00'

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

# Flag values that are marked as below detection limit in source data
obs_df.loc[obs_df['resultQualityObservedValueBelowLOQ'] == 1, 'detection_limit_flag'] = '<'

# Merge the DFs
merged_df = site_df\
    .merge(obs_df, how='left', on='monitoringSiteIdentifier')\
    .merge(
        cmap_df, how='left', left_on=['observedPropertyDeterminandCode', 'resultUom'],
        right_on=['source_param_code', 'source_unit']
    )
merged_df.drop_duplicates(inplace=True)
merged_df.reset_index(drop=True, inplace=True)
merged_df.drop(merged_df[(merged_df['param_code'].isnull())].index, inplace=True, errors='ignore')
merged_df.drop(merged_df[(merged_df['obs_date'].isnull())].index, inplace=True, errors='ignore')

# Convert observation values
merged_df['obs_value'] = merged_df['resultObservedValue'] * merged_df['conversion_constant']

# Add filtration column
merged_df.loc[merged_df['procedureAnalysedMatrix'] == 'W', 'filtration'] = 'unfiltered'
merged_df.loc[merged_df['procedureAnalysedMatrix'] == 'W-DIS', 'filtration'] = 'filtered'

# Get statistics about raw and processed observation values and export to CSV
value_dict = {'raw': 'resultObservedValue', 'processed': 'obs_value'}
for value_type, value_col in value_dict.items():
    stats_df = get_stats_df(
        merged_df,
        ['source_param_code', 'param_code', 'param_name', 'source_param_form', 'param_form', 'source_unit', 'unit'],
        value_col, 'obs_date'
    )
    agg_stats_df = get_stats_df(merged_df, ['monitoringSiteIdentifier', 'source_param_code'], value_col, 'obs_date')
    agg_stats_df = agg_stats_df.groupby(['source_param_code'])\
        .agg(
            site_count=('count', 'count'), mean_obs_count_per_site=('count', 'mean'),
            mean_ts_length_per_site=('ts_length', 'mean')
        ).reset_index()
    stats_df = stats_df.merge(agg_stats_df, on='source_param_code')
    fname = '_'.join([ds_name, value_type, 'stats.csv'])
    stats_df.to_csv(os.path.join(proc_dir, 'meta', fname), sep=';', index=False, encoding='utf-8')

# Export processed data to CSV
meta_cols = ['procedureAnalysedMatrix', 'Remarks']
output_codes = merged_df['param_code'].unique()
for code in output_codes:
    code_df = merged_df[merged_df['param_code'] == code]
    # Dictionary with output columns
    code_dict = {
        'obs_id': code_df['obs_id'],
        'lat_wgs84': code_df['lat'],
        'lon_wgs84': code_df['lon'],
        'obs_date': code_df['obs_date'],
        'obs_time': code_df['obs_time'],
        'obs_time_zone': np.nan,
        'site_id': code_df['monitoringSiteIdentifier'],
        'site_name': code_df['monitoringSiteName'],
        'site_country': code_df['countryCode'],
        'upstream_basin_area': np.nan,
        'upstream_basin_area_unit': np.nan,
        'drainage_region_name': np.nan,
        'param_code': code_df['param_code'],
        'source_param_code': code_df['source_param_code'],
        'param_name': code_df['param_name'],
        'source_param_name': code_df['source_param_name'],
        'obs_value': code_df['obs_value'],
        'source_obs_value': code_df['resultObservedValue'],
        'detection_limit_flag': code_df['detection_limit_flag'],
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
        code_dict[col_name] = code_df[col]
    output_df = pd.DataFrame(code_dict)
    output_df.to_csv(os.path.join(proc_dir, code + '_' + ds_name + '.csv'), sep=';', index=False, encoding='utf-8')
